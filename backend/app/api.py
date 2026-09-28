import json
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .config import DEMO_VIDEO, HISTORY_DIR, MODEL_PATH
from .db import Analysis, SessionLocal, init_db
from .pipeline import process_video
from .recommend import recommendations


app = FastAPI(
    title="AI Traffic Decision Support API",
    version="4.0",
)

# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# DIRECTORIES
# ---------------------------------------------------------

HISTORY_DIR.mkdir(parents=True, exist_ok=True)

app.mount(
    "/files",
    StaticFiles(directory=str(HISTORY_DIR)),
    name="files",
)


# ---------------------------------------------------------
# JOB CONTROL
# ---------------------------------------------------------

JOB_LOCK = threading.Lock()


# ---------------------------------------------------------
# STARTUP
# ---------------------------------------------------------

@app.on_event("startup")
def startup():
    init_db()


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def _read_json(path: Path, default=None):
    if default is None:
        default = {}

    try:
        if path.exists():
            return json.loads(
                path.read_text(encoding="utf-8")
            )
    except Exception:
        pass

    return default


def _relative_file_url(analysis_id: str, filename: str):
    """
    Convert a generated file into a frontend-accessible URL.

    Example:
    /files/analysis_xxx/traffic_browser.mp4
    """

    path = HISTORY_DIR / analysis_id / filename

    if path.exists() and path.is_file() and path.stat().st_size > 0:
        return f"/files/{analysis_id}/{filename}"

    return None


def _urls(analysis_id: str):
    """
    Find generated frontend files.
    """

    directory = HISTORY_DIR / analysis_id

    video = _relative_file_url(
        analysis_id,
        "traffic_browser.mp4",
    )

    heatmap = _relative_file_url(
        analysis_id,
        "heatmap.png",
    )

    return video, heatmap


def analysis_dict(a):
    """
    Convert SQLite Analysis object into the JSON
    consumed by the frontend.
    """

    if not a:
        return None

    analysis_id = a.id
    directory = HISTORY_DIR / analysis_id

    # ---------------------------------------------
    # Database values
    # ---------------------------------------------

    result = {
        "analysis_id": analysis_id,
        "video_name": a.video_name,

        "status": a.status,

        "frames": a.frames or 0,
        "duration_s": a.duration_s or 0,

        "total_vehicles": a.total_vehicles or 0,

        "density": a.density or 0,
        "average_density": a.density or 0,

        "congestion": a.congestion or "UNKNOWN",

        "flow_vph": a.flow_vph or 0,

        "annotated_video": None,
        "browser_video": None,
        "video_url": None,
        "heatmap": None,

        "error": a.error,

        "created_at": (
            a.created_at.isoformat()
            if a.created_at
            else None
        ),
    }

    # ---------------------------------------------
    # Summary JSON
    # ---------------------------------------------

    summary = _read_json(
        directory / "summary.json",
        {},
    )

    if isinstance(summary, dict):
        for key, value in summary.items():

            if key not in {
                "annotated_video",
                "browser_video",
                "video_url",
                "heatmap",
            }:
                result[key] = value

    # ---------------------------------------------
    # Live state
    # ---------------------------------------------

    state = _read_json(
        directory / "live_state.json",
        {},
    )

    if isinstance(state, dict):
        result.update(state)

    # ---------------------------------------------
    # Always preserve database identity
    # ---------------------------------------------

    result["analysis_id"] = analysis_id
    result["video_name"] = a.video_name

    # ---------------------------------------------
    # Status
    # ---------------------------------------------

    if a.status in {"failed", "completed"}:
        result["status"] = a.status
    elif state.get("status"):
        result["status"] = state["status"]
    else:
        result["status"] = a.status

    # ---------------------------------------------
    # Convert Windows filesystem paths into URLs
    # ---------------------------------------------

    video, heatmap = _urls(analysis_id)

    result["annotated_video"] = video
    result["browser_video"] = video
    result["video_url"] = video
    result["heatmap"] = heatmap

    result["final_video_available"] = video is not None

    result["processing"] = result["status"] == "processing"
    result["completed"] = result["status"] == "completed"

    return result


# ---------------------------------------------------------
# CREATE ANALYSIS
# ---------------------------------------------------------

def _new_analysis(video_name):

    return Analysis(
        id="analysis_" + uuid.uuid4().hex[:12],
        video_name=video_name,
        status="queued",
    )


# ---------------------------------------------------------
# RUN ANALYSIS
# ---------------------------------------------------------

def _run(analysis_id, video_path):

    db = None

    try:

        print("\n" + "=" * 60)
        print("[API] Starting background analysis")
        print("[API] Analysis:", analysis_id)
        print("[API] Video:", video_path)
        print("=" * 60)

        # ---------------------------------------------
        # Mark processing
        # ---------------------------------------------

        db = SessionLocal()

        analysis = db.get(
            Analysis,
            analysis_id,
        )

        if not analysis:
            print("[API] Analysis not found")
            return

        analysis.status = "processing"
        analysis.error = None

        db.commit()
        db.close()
        db = None

        # ---------------------------------------------
        # RUN THE WORKING PIPELINE
        # ---------------------------------------------

        print("[API] Calling process_video()...")

        aid, summary = process_video(
            video_path,
            analysis_id=analysis_id,
            model_path=MODEL_PATH,
        )

        print("[API] process_video() completed")
        print("[API] Result:", summary)

        # ---------------------------------------------
        # Update database
        # ---------------------------------------------

        db = SessionLocal()

        analysis = db.get(
            Analysis,
            aid,
        )

        if not analysis:
            raise RuntimeError(
                f"Analysis {aid} disappeared from database"
            )

        analysis.status = "completed"

        analysis.frames = int(
            summary.get("frames", 0)
        )

        analysis.duration_s = float(
            summary.get("duration_s", 0)
        )

        analysis.total_vehicles = int(
            summary.get("total_vehicles", 0)
        )

        analysis.density = float(
            summary.get(
                "average_density",
                summary.get("density", 0),
            )
        )

        analysis.congestion = str(
            summary.get(
                "congestion",
                "UNKNOWN",
            )
        )

        analysis.flow_vph = float(
            summary.get("flow_vph", 0)
        )

        # ---------------------------------------------
        # VIDEO URL
        # ---------------------------------------------

        video_path = HISTORY_DIR / aid / "traffic_browser.mp4"

        if (
            video_path.exists()
            and video_path.stat().st_size > 0
        ):
            analysis.annotated_video = (
                f"/files/{aid}/traffic_browser.mp4"
            )
        else:
            analysis.annotated_video = None

        # ---------------------------------------------
        # HEATMAP URL
        # ---------------------------------------------

        heatmap_path = HISTORY_DIR / aid / "heatmap.png"

        if (
            heatmap_path.exists()
            and heatmap_path.stat().st_size > 0
        ):
            analysis.heatmap = (
                f"/files/{aid}/heatmap.png"
            )
        else:
            analysis.heatmap = None

        analysis.error = None

        db.commit()

        print("\n" + "=" * 60)
        print("[API] ANALYSIS COMPLETED")
        print("[API] ID:", aid)
        print("[API] Frames:", analysis.frames)
        print("[API] Vehicles:", analysis.total_vehicles)
        print("[API] Density:", analysis.density)
        print("[API] Congestion:", analysis.congestion)
        print("[API] Flow:", analysis.flow_vph)
        print("[API] Video:", analysis.annotated_video)
        print("[API] Heatmap:", analysis.heatmap)
        print("=" * 60)

    except Exception as exc:

        import traceback

        traceback.print_exc()

        try:

            if db is not None:
                db.rollback()
                db.close()

            db = SessionLocal()

            analysis = db.get(
                Analysis,
                analysis_id,
            )

            if analysis:

                analysis.status = "failed"
                analysis.error = str(exc)

                db.commit()

        except Exception:

            traceback.print_exc()

        finally:

            if db is not None:
                db.close()

    finally:

        if db is not None:
            db.close()


# ---------------------------------------------------------
# START ANALYSIS
# ---------------------------------------------------------

def _start(video_path):

    video_path = Path(video_path)

    # ---------------------------------------------
    # Check existing running job
    # ---------------------------------------------

    db = SessionLocal()

    try:

        running = (
            db.query(Analysis)
            .filter(
                Analysis.status.in_(
                    ["queued", "processing"]
                )
            )
            .order_by(
                Analysis.created_at.desc()
            )
            .first()
        )

        if running:

            print(
                "[API] Existing analysis:",
                running.id,
            )

            return analysis_dict(running)

        # -----------------------------------------
        # Create new analysis
        # -----------------------------------------

        analysis = _new_analysis(
            video_path.name
        )

        db.add(analysis)
        db.commit()

        analysis_id = analysis.id

    finally:

        db.close()

    # ---------------------------------------------
    # Start worker
    # ---------------------------------------------

    worker = threading.Thread(
        target=_run,
        args=(
            analysis_id,
            video_path,
        ),
        daemon=True,
    )

    worker.start()

    print(
        "[API] Worker started:",
        analysis_id,
    )

    return {
        "analysis_id": analysis_id,
        "video_name": video_path.name,
        "status": "queued",
    }


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():

    return {
        "name": "AI Traffic Decision Support API",
        "status": "running",
        "version": "4.0",
        "docs": "/docs",
    }


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "ok",

        "model_exists": MODEL_PATH.exists(),
        "video_exists": DEMO_VIDEO.exists(),

        "model": str(MODEL_PATH),
        "video": str(DEMO_VIDEO),
    }


# ---------------------------------------------------------
# START LIVE / DEMO ANALYSIS
# ---------------------------------------------------------

@app.post("/start-live")
def start_live():

    if not MODEL_PATH.exists():

        raise HTTPException(
            status_code=503,
            detail=f"Trained model missing: {MODEL_PATH}",
        )

    if not DEMO_VIDEO.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                f"Put traffic.mp4 in "
                f"{DEMO_VIDEO.parent}"
            ),
        )

    return _start(DEMO_VIDEO)


# ---------------------------------------------------------
# RESTART
# ---------------------------------------------------------

@app.post("/restart-live")
def restart_live():

    if not MODEL_PATH.exists():

        raise HTTPException(
            status_code=503,
            detail=f"Trained model missing: {MODEL_PATH}",
        )

    if not DEMO_VIDEO.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                f"Put traffic.mp4 in "
                f"{DEMO_VIDEO.parent}"
            ),
        )

    return _start(DEMO_VIDEO)


# ---------------------------------------------------------
# CURRENT ANALYSIS
# ---------------------------------------------------------

@app.get("/current-analysis")
def current():

    db = SessionLocal()

    try:

        analysis = (
            db.query(Analysis)
            .order_by(
                Analysis.created_at.desc()
            )
            .first()
        )

        if not analysis:

            return {
                "status": "empty"
            }

        return analysis_dict(analysis)

    finally:

        db.close()


# ---------------------------------------------------------
# GET ONE ANALYSIS
# ---------------------------------------------------------

@app.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: str):

    db = SessionLocal()

    try:

        analysis = db.get(
            Analysis,
            analysis_id,
        )

        if not analysis:

            raise HTTPException(
                status_code=404,
                detail="Analysis not found",
            )

        return analysis_dict(analysis)

    finally:

        db.close()


# ---------------------------------------------------------
# FRAME STATS
# ---------------------------------------------------------

@app.get("/analysis/{analysis_id}/frame-stats")
def frame_stats(analysis_id: str):

    path = (
        HISTORY_DIR
        / analysis_id
        / "frame_stats.json"
    )

    if not path.exists():

        return []

    return _read_json(
        path,
        [],
    )


# ---------------------------------------------------------
# ANALYSIS HISTORY
# ---------------------------------------------------------

@app.get("/analysis-history")
def history(
    limit: int = Query(
        20,
        ge=1,
        le=100,
    )
):

    db = SessionLocal()

    try:

        rows = (
            db.query(Analysis)
            .order_by(
                Analysis.created_at.desc()
            )
            .limit(limit)
            .all()
        )

        return [
            analysis_dict(row)
            for row in rows
        ]

    finally:

        db.close()


# ---------------------------------------------------------
# RECOMMENDATIONS
# ---------------------------------------------------------

@app.get("/recommendations/{analysis_id}")
def get_recommendations(
    analysis_id: str,
):

    db = SessionLocal()

    try:

        analysis = db.get(
            Analysis,
            analysis_id,
        )

        if not analysis:

            raise HTTPException(
                status_code=404,
                detail="Analysis not found",
            )

        data = analysis_dict(
            analysis
        ) or {}

        return {
            "analysis_id": analysis_id,
            "recommendations": recommendations(
                data
            ),
        }

    finally:

        db.close()


# ---------------------------------------------------------
# DEMO VIDEO
# ---------------------------------------------------------

@app.get("/demo")
def demo():

    return {
        "available": DEMO_VIDEO.exists(),
        "video": "/demo-video",
        "video_name": DEMO_VIDEO.name,
    }


@app.get("/demo-video")
def demo_video():

    if not DEMO_VIDEO.exists():

        raise HTTPException(
            status_code=404,
            detail="Put traffic.mp4 in data/raw",
        )

    return FileResponse(
        DEMO_VIDEO,
        media_type="video/mp4",
        filename=DEMO_VIDEO.name,
    )