import csv
import json
import shutil
import subprocess
import time
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2

from .analytics import (
    build_summary,
    congestion_level,
    density,
    is_vehicle,
    make_heatmap,
    stopped_ratio,
    zone,
)
from .config import HISTORY_DIR, MODEL_PATH
from .detection import extract_detections, load_model, track_frame


# ============================================================
# SAFE JSON
# ============================================================

def _write_json(path: Path, data):
    """
    Windows-safe JSON writer.

    We deliberately do NOT use:
        temporary_file.replace(target)

    because Windows was producing WinError 5 in the previous
    implementation.
    """

    path.parent.mkdir(parents=True, exist_ok=True)

    payload = json.dumps(
        data,
        indent=2,
        default=str,
    )

    for attempt in range(3):
        try:
            path.write_text(
                payload,
                encoding="utf-8",
            )
            return
        except PermissionError:
            if attempt == 2:
                print(
                    f"[WARNING] Could not update {path.name}; "
                    "continuing video processing."
                )
                return

            time.sleep(0.10)


# ============================================================
# FFMPEG
# ============================================================

def _ffmpeg_path():
    return shutil.which("ffmpeg")


def make_browser_video(
    input_video: str,
    output_video: str,
) -> str:

    ffmpeg = _ffmpeg_path()

    if not ffmpeg:
        raise RuntimeError(
            "FFmpeg is required. "
            "Install FFmpeg and add ffmpeg.exe to PATH."
        )

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(input_video),

        "-c:v",
        "libx264",

        "-preset",
        "veryfast",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-an",

        "-movflags",
        "+faststart",

        str(output_video),
    ]

    print("[FFMPEG] Creating browser video...")

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "FFmpeg conversion failed:\n"
            + result.stderr[-5000:]
        )

    output_path = Path(output_video)

    if not output_path.exists():
        raise RuntimeError(
            "FFmpeg finished but browser video was not created."
        )

    if output_path.stat().st_size == 0:
        raise RuntimeError(
            "Browser video was created but is empty."
        )

    print(
        f"[FFMPEG] Browser video ready: {output_path}"
    )

    return str(output_path)


# ============================================================
# LIVE STATE
# ============================================================

def _update_live_state(
    state_file,
    analysis_id,
    status,
    frame_no,
    total_frames,
    fps,
    current_vehicles,
    unique_vehicles,
    tracked_now,
    current_density,
    congestion,
    flow_vph,
    vehicle_counts,
):

    _write_json(
        state_file,
        {
            "analysis_id": analysis_id,
            "status": status,

            "frame": frame_no,
            "total_frames": total_frames,

            "fps": fps,
            "duration_s": (
                frame_no / fps
                if fps
                else 0
            ),

            "current_vehicles": current_vehicles,
            "unique_vehicles": unique_vehicles,
            "tracked_now": tracked_now,

            "density": current_density,
            "average_density": current_density,

            "congestion": congestion,
            "flow_vph": flow_vph,

            "vehicle_counts": vehicle_counts,

            "processing": status == "processing",
            "completed": status == "completed",
        },
    )


# ============================================================
# MAIN VIDEO PROCESSOR
# ============================================================

def process_video(
    video_path,
    analysis_id=None,
    model_path=None,
    conf=0.30,
):

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(
            f"Video not found: {video_path}"
        )

    analysis_id = analysis_id or (
        "analysis_"
        + uuid.uuid4().hex[:12]
    )

    out_dir = HISTORY_DIR / analysis_id

    out_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print("=" * 60)
    print("[TRAFFIC AI] Starting analysis")
    print("=" * 60)
    print(f"[VIDEO] {video_path}")
    print(f"[ANALYSIS] {analysis_id}")

    # ========================================================
    # MODEL
    # ========================================================

    print("[YOLO] Loading trained model...")

    model = load_model(
        model_path or MODEL_PATH
    )

    print("[YOLO] Model loaded.")

    # ========================================================
    # INPUT VIDEO
    # ========================================================

    print("[VIDEO] Opening video...")

    cap = cv2.VideoCapture(
        str(video_path)
    )

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open video: {video_path}"
        )

    width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    ) or 1280

    height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    ) or 720

    fps = (
        cap.get(
            cv2.CAP_PROP_FPS
        )
        or 25.0
    )

    if fps <= 0:
        fps = 25.0

    total_frames = int(
        cap.get(
            cv2.CAP_PROP_FRAME_COUNT
        )
    )

    print(
        f"[VIDEO] Resolution: "
        f"{width}x{height}"
    )

    print(
        f"[VIDEO] FPS: {fps:.2f}"
    )

    print(
        f"[VIDEO] Frames: {total_frames}"
    )

    # ========================================================
    # OUTPUT FILES
    # ========================================================

    intermediate = (
        out_dir /
        "traffic_annotated.mp4"
    )

    browser_video = (
        out_dir /
        "traffic_browser.mp4"
    )

    state_file = (
        out_dir /
        "live_state.json"
    )

    frame_stats_file = (
        out_dir /
        "frame_stats.json"
    )

    # ========================================================
    # VIDEO WRITER
    # ========================================================

    writer = cv2.VideoWriter(
        str(intermediate),
        cv2.VideoWriter_fourcc(
            *"mp4v"
        ),
        fps,
        (
            width,
            height,
        ),
    )

    if not writer.isOpened():

        cap.release()

        raise RuntimeError(
            "Could not create annotated video writer."
        )

    # ========================================================
    # ANALYTICS
    # ========================================================

    events = []

    congestion_rows = []

    frame_stats = []

    heatmap_points = []

    previous_positions = {}

    unique_ids = set()

    class_ids = {}

    frame_no = 0

    current_vehicle_counts = {}

    last_density = 0.0

    last_congestion = "UNKNOWN"

    last_flow = 0.0

    last_tracked = 0

    # ========================================================
    # INITIAL STATE
    # ========================================================

    _update_live_state(
        state_file,
        analysis_id,
        "processing",
        0,
        total_frames,
        fps,
        0,
        0,
        0,
        0,
        "UNKNOWN",
        0,
        {},
    )

    # ========================================================
    # FRAME LOOP
    # ========================================================

    while True:

        ok, frame = cap.read()

        if not ok:
            break

        frame_no += 1

        # ----------------------------------------------------
        # YOLO + TRACKING
        # ----------------------------------------------------

        results = track_frame(
            model,
            frame,
            conf=conf,
        )

        result = (
            results[0]
            if results
            else None
        )

        # ----------------------------------------------------
        # DETECTIONS
        # ----------------------------------------------------

        all_detections = (
            extract_detections(
                result
            )
            if result is not None
            else []
        )

        detections = [
            d
            for d in all_detections
            if is_vehicle(
                d["vehicle_class"]
            )
        ]

        timestamp_s = (
            frame_no / fps
        )

        timestamp = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        # ----------------------------------------------------
        # VEHICLE COUNTS
        # ----------------------------------------------------

        current_vehicle_counts = dict(
            Counter(
                d["vehicle_class"]
                for d in detections
            )
        )

        # ----------------------------------------------------
        # TRACKING
        # ----------------------------------------------------

        tracked_ids = set()

        for detection in detections:

            d = dict(detection)

            d["frame"] = frame_no

            d["timestamp_s"] = timestamp_s

            d["timestamp"] = timestamp

            d["zone"] = zone(
                d["center_x"],
                d["center_y"],
                width,
                height,
            )

            events.append(d)

            heatmap_points.append(
                (
                    d["center_x"],
                    d["center_y"],
                )
            )

            track_id = d.get(
                "track_id"
            )

            if track_id is not None:

                track_id = str(
                    track_id
                )

                tracked_ids.add(
                    track_id
                )

                unique_ids.add(
                    track_id
                )

                class_ids.setdefault(
                    d["vehicle_class"],
                    set(),
                ).add(
                    track_id
                )

        tracked_now = len(
            tracked_ids
        )

        last_tracked = tracked_now

        # ----------------------------------------------------
        # DENSITY
        # ----------------------------------------------------

        current_density = density(
            len(detections),
            width,
            height,
        )

        last_density = (
            current_density
        )

        # ----------------------------------------------------
        # STOPPED VEHICLES
        # ----------------------------------------------------

        stop_ratio = stopped_ratio(
            detections,
            previous_positions,
        )

        # ----------------------------------------------------
        # CONGESTION
        # ----------------------------------------------------

        current_congestion = (
            congestion_level(
                current_density,
                stop_ratio,
            )
        )

        last_congestion = (
            current_congestion
        )

        # ----------------------------------------------------
        # POSITIONS
        # ----------------------------------------------------

        previous_positions = {
            d["track_id"]:
            (
                d["center_x"],
                d["center_y"],
            )
            for d in detections
            if d.get("track_id") is not None
        }

        # ----------------------------------------------------
        # FLOW
        # ----------------------------------------------------

        elapsed = (
            frame_no / fps
            if fps
            else 0
        )

        if elapsed >= 5:

            flow_vph = (
                len(unique_ids)
                / elapsed
                * 3600
            )

        else:

            # Do not display misleading huge
            # values during the first seconds.

            flow_vph = 0

        last_flow = flow_vph

        # ====================================================
        # ANNOTATED FRAME
        # ====================================================

        if result is not None:

            annotated = result.plot()

        else:

            annotated = frame.copy()

        # ====================================================
        # INFORMATION PANEL
        # ====================================================

        cv2.rectangle(
            annotated,
            (8, 8),
            (720, 188),
            (15, 23, 42),
            -1,
        )

        lines = [
            f"VEHICLES: {len(detections)}",

            (
                f"TRACKED: {tracked_now}   "
                f"UNIQUE: {len(unique_ids)}"
            ),

            (
                f"DENSITY: "
                f"{current_density:.2f}"
            ),

            (
                f"CONGESTION: "
                f"{current_congestion}"
            ),

            (
                f"FLOW: "
                f"{flow_vph:.0f} VPH"
            ),

            (
                f"FRAME: "
                f"{frame_no}/"
                f"{total_frames or '?'}"
            ),
        ]

        for index, text in enumerate(
            lines
        ):

            cv2.putText(
                annotated,
                text,
                (
                    18,
                    35 + index * 27,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        # ====================================================
        # VEHICLE TYPE COUNTS
        # ====================================================

        type_text = " | ".join(
            f"{key}: {value}"
            for key, value
            in current_vehicle_counts.items()
        )

        if type_text:

            cv2.putText(
                annotated,
                type_text,
                (
                    18,
                    178,
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.50,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        # ====================================================
        # WRITE ANNOTATED FRAME
        # ====================================================

        writer.write(
            annotated
        )

        # ====================================================
        # FRAME STAT
        # ====================================================

        stat = {
            "frame": frame_no,
            "fps": fps,
            "timestamp_s": timestamp_s,

            "current_vehicles":
                len(detections),

            "tracked_now":
                tracked_now,

            "cumulative_vehicles":
                len(unique_ids),

            "density":
                current_density,

            "stopped_ratio":
                stop_ratio,

            "congestion":
                current_congestion,

            "flow_vph":
                flow_vph,

            "vehicle_counts":
                current_vehicle_counts,
        }

        frame_stats.append(
            stat
        )

        congestion_rows.append(
            {
                "frame":
                    frame_no,

                "density":
                    current_density,

                "stopped_ratio":
                    stop_ratio,

                "congestion":
                    current_congestion,
            }
        )

        # ====================================================
        # LIVE STATE
        # ====================================================
        #
        # IMPORTANT:
        #
        # Only live_state.json is updated.
        #
        # frame_stats.json is NOT rewritten here.
        #
        # This prevents the previous frame-15 slowdown.
        # ====================================================

        if (
            frame_no == 1
            or frame_no % 30 == 0
        ):

            _update_live_state(
                state_file,
                analysis_id,
                "processing",
                frame_no,
                total_frames,
                fps,
                len(detections),
                len(unique_ids),
                tracked_now,
                current_density,
                current_congestion,
                flow_vph,
                current_vehicle_counts,
            )

        # ====================================================
        # TERMINAL PROGRESS
        # ====================================================

        if (
            frame_no == 1
            or frame_no % 100 == 0
        ):

            percent = (
                (
                    frame_no
                    / total_frames
                )
                * 100
                if total_frames
                else 0
            )

            print(
                f"[YOLO] "
                f"{frame_no}/"
                f"{total_frames} "
                f"({percent:.1f}%) | "
                f"vehicles={len(detections)} | "
                f"unique={len(unique_ids)}"
            )

    # ========================================================
    # CLOSE VIDEO
    # ========================================================

    cap.release()

    writer.release()

    # ========================================================
    # FINAL FRAME STATS
    # ========================================================

    _write_json(
        frame_stats_file,
        frame_stats,
    )

    # ========================================================
    # CHECK ANNOTATED VIDEO
    # ========================================================

    if not intermediate.exists():

        raise RuntimeError(
            "Annotated video was not created."
        )

    if intermediate.stat().st_size <= 0:

        raise RuntimeError(
            "Annotated video is empty."
        )

    print(
        "[VIDEO] Annotated video created."
    )

    # ========================================================
    # BROWSER VIDEO
    # ========================================================

    final_video = Path(
        make_browser_video(
            str(intermediate),
            str(browser_video),
        )
    )

    # ========================================================
    # REMOVE INTERMEDIATE
    # ========================================================

    try:

        intermediate.unlink()

    except OSError:

        pass

    # ========================================================
    # EVENTS CSV
    # ========================================================

    events_csv = (
        out_dir /
        "events.csv"
    )

    fields = []

    for event in events:

        for key in event:

            if key not in fields:

                fields.append(key)

    with events_csv.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        if fields:

            csv_writer = csv.DictWriter(
                file,
                fieldnames=fields,
                extrasaction="ignore",
            )

            csv_writer.writeheader()

            csv_writer.writerows(
                events
            )

    # ========================================================
    # CONGESTION CSV
    # ========================================================

    congestion_csv = (
        out_dir /
        "congestion.csv"
    )

    with congestion_csv.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        csv_writer = csv.DictWriter(
            file,
            fieldnames=[
                "frame",
                "density",
                "stopped_ratio",
                "congestion",
            ],
        )

        csv_writer.writeheader()

        csv_writer.writerows(
            congestion_rows
        )

    # ========================================================
    # HEATMAP
    # ========================================================

    heatmap = make_heatmap(
        heatmap_points,
        width,
        height,
        out_dir /
        "heatmap.png",
    )

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    summary = build_summary(
        events,
        congestion_rows,
        fps,
        width,
        height,
        out_dir,
        video_path.name,
        str(final_video),
        heatmap,
    )

    summary.update(
        {
            "analysis_id":
                analysis_id,

            "browser_video":
                f"/files/{analysis_id}/traffic_browser.mp4",

            "annotated_video":
                f"/files/{analysis_id}/traffic_browser.mp4",

            "video_url":
                f"/files/{analysis_id}/traffic_browser.mp4",

            "fps":
                fps,

            "total_frames":
                total_frames,

            "vehicle_counts":
                {
                    key: len(value)
                    for key, value
                    in class_ids.items()
                },
        }
    )

    _write_json(
        out_dir /
        "summary.json",
        summary,
    )

    # ========================================================
    # COMPLETED LIVE STATE
    # ========================================================

    final_vehicle_counts = {
        key: len(value)
        for key, value
        in class_ids.items()
    }

    _update_live_state(
        state_file,
        analysis_id,
        "completed",
        frame_no,
        total_frames,
        fps,
        (
            len(detections)
            if "detections" in locals()
            else 0
        ),
        len(unique_ids),
        last_tracked,
        summary.get(
            "average_density",
            last_density,
        ),
        summary.get(
            "congestion",
            last_congestion,
        ),
        summary.get(
            "flow_vph",
            last_flow,
        ),
        final_vehicle_counts,
    )

    print()
    print("=" * 60)
    print("[TRAFFIC AI] ANALYSIS COMPLETED")
    print("=" * 60)
    print(
        f"[VIDEO] {browser_video}"
    )
    print(
        f"[HEATMAP] {heatmap}"
    )
    print(
        f"[UNIQUE VEHICLES] "
        f"{len(unique_ids)}"
    )
    print("=" * 60)

    return analysis_id, summary