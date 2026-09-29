import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  Car,
  Clock3,
  Gauge,
  Map,
  RefreshCw,
  RotateCcw,
  Timer,
  Video,
} from "lucide-react";

import { apiFetch, API_BASE_URL } from "../api/client";
import { getCurrentAnalysis } from "../api/traffic";

function makeUrl(path) {
  if (!path) return "";

  if (
    path.startsWith("http://") ||
    path.startsWith("https://")
  ) {
    return path;
  }

  return `${API_BASE_URL}${path.startsWith("/") ? "" : "/"}${path}`;
}

function formatNumber(value, digits = 0) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  if (Number.isNaN(number)) {
    return "—";
  }

  return number.toLocaleString("en-IN", {
    maximumFractionDigits: digits,
  });
}

function MetricCard({
  label,
  value,
  suffix,
  icon: Icon,
  tone = "slate",
}) {
  const tones = {
    slate: "bg-slate-50 text-slate-700",
    teal: "bg-teal-50 text-teal-600",
    amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600",
    blue: "bg-blue-50 text-blue-600",
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-400">
            {label}
          </p>

          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-950">
              {value}
            </span>

            {suffix && (
              <span className="text-xs font-semibold text-slate-400">
                {suffix}
              </span>
            )}
          </div>
        </div>

        <div
          className={`rounded-xl p-2.5 ${
            tones[tone] || tones.slate
          }`}
        >
          <Icon size={18} />
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ status }) {
  const completed = status === "completed";
  const processing =
    status === "processing" ||
    status === "queued";

  if (completed) {
    return (
      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-600">
        COMPLETED
      </span>
    );
  }

  if (processing) {
    return (
      <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-600">
        PROCESSING
      </span>
    );
  }

  return (
    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-500">
      {String(status || "UNKNOWN").toUpperCase()}
    </span>
  );
}

function CongestionBadge({ value }) {
  if (!value) {
    return (
      <span className="text-slate-400">
        —
      </span>
    );
  }

  const normalized = String(value).toUpperCase();

  let classes =
    "bg-slate-100 text-slate-600";

  if (normalized === "LOW") {
    classes =
      "bg-emerald-50 text-emerald-600";
  }

  if (normalized === "MEDIUM") {
    classes =
      "bg-amber-50 text-amber-600";
  }

  if (normalized === "HIGH") {
    classes =
      "bg-rose-50 text-rose-600";
  }

  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-bold ${classes}`}
    >
      {normalized}
    </span>
  );
}

export default function Dashboard() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [restarting, setRestarting] = useState(false);
  const [error, setError] = useState("");

  const loadAnalysis = useCallback(async () => {
    try {
      const result = await apiFetch(
        "/current-analysis"
      );

      setAnalysis(result);
      setError("");

      return result;
    } catch (err) {
      console.error(
        "Analysis request failed:",
        err
      );

      setError(
        err?.message ||
          "Could not connect to the backend."
      );

      return null;
    } finally {
      setLoading(false);
    }
  }, []);
useEffect(() => {
  let timer;

  const load = async () => {
    const result = await getCurrentAnalysis();
    setAnalysis(result);

    if (!result.processing && result.completed) {
      return;
    }

    timer = setTimeout(load, 2000);
  };

  load();

  return () => {
    if (timer) clearTimeout(timer);
  };
}, []);

  /*
   * Silently refresh the analysis.
   *
   * This is NOT displayed as YOLO progress.
   * It only allows the dashboard to receive
   * the final result when processing finishes.
   */
  useEffect(() => {
    const timer = setInterval(() => {
      loadAnalysis();
    }, 3000);

    return () => clearInterval(timer);
  }, [loadAnalysis]);

  const restartAnalysis = async () => {
    try {
      setRestarting(true);
      setError("");

      await apiFetch(
        "/restart-live",
        {
          method: "POST",
        }
      );

      await loadAnalysis();
    } catch (err) {
      console.error(err);

      setError(
        err?.message ||
          "Could not restart analysis."
      );
    } finally {
      setRestarting(false);
    }
  };

  const videoPath =
    analysis?.video_url ||
    analysis?.browser_video ||
    analysis?.annotated_video ||
    "";

  const heatmapPath =
    analysis?.heatmap || "";

  const videoUrl = makeUrl(videoPath);
  const heatmapUrl = makeUrl(heatmapPath);

  const completed =
    analysis?.completed === true ||
    analysis?.status === "completed";

  const vehicleCounts =
    analysis?.vehicle_counts || {};

  const vehicleRows = useMemo(() => {
    return Object.entries(vehicleCounts)
      .sort((a, b) => Number(b[1]) - Number(a[1]));
  }, [vehicleCounts]);

  const totalVehicles =
    analysis?.total_vehicles ?? 0;

  const frames =
    analysis?.frames ??
    analysis?.total_frames ??
    0;

  const duration =
    analysis?.duration_s ?? 0;

  const density =
    analysis?.average_density ??
    analysis?.density ??
    0;

  const flow =
    analysis?.flow_vph ?? 0;

  const fps =
    analysis?.fps ?? 0;

  return (
    <main className="mx-auto max-w-[1600px] space-y-6 px-6 py-7 lg:px-10">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <section className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

        <div>
          <p className="text-xs font-semibold text-slate-400">
            Operations / Live analysis
          </p>

          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">
            Traffic intelligence dashboard
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Real results generated by your YOLO traffic analysis.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">

          {analysis && (
            <StatusBadge
              status={analysis.status}
            />
          )}

          <button
            onClick={loadAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm transition hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw
              size={16}
              className={
                loading
                  ? "animate-spin"
                  : ""
              }
            />

            Refresh
          </button>

          <button
            onClick={restartAnalysis}
            disabled={restarting}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-slate-800 disabled:opacity-50"
          >
            <RotateCcw
              size={16}
              className={
                restarting
                  ? "animate-spin"
                  : ""
              }
            />

            Restart
          </button>

        </div>
      </section>

      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (
        <section className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
          {error}
        </section>
      )}

      {/* ================================================= */}
      {/* MAIN METRICS */}
      {/* ================================================= */}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <MetricCard
          label="Total vehicles"
          value={formatNumber(totalVehicles)}
          suffix="detected"
          icon={Car}
          tone="teal"
        />

        <MetricCard
          label="Traffic density"
          value={formatNumber(density, 2)}
          suffix="index"
          icon={Activity}
          tone="amber"
        />

        <MetricCard
          label="Traffic flow"
          value={formatNumber(flow)}
          suffix="vehicles / hour"
          icon={Gauge}
          tone="blue"
        />

        <MetricCard
          label="Video duration"
          value={formatNumber(duration, 1)}
          suffix="seconds"
          icon={Timer}
          tone="slate"
        />

      </section>

      {/* ================================================= */}
      {/* ANNOTATED VIDEO + SUMMARY */}
      {/* ================================================= */}

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,.75fr)]">

        {/* VIDEO */}

        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

          <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">

            <div>
              <h2 className="flex items-center gap-2 text-base font-black text-slate-950">
                <Video
                  size={18}
                  className="text-teal-500"
                />

                Annotated traffic video
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                YOLO detection and tracking output.
              </p>
            </div>

            {completed && (
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-[10px] font-black text-emerald-600">
                VIDEO READY
              </span>
            )}

          </div>

          <div className="bg-slate-950 p-4">

            {completed && videoUrl ? (
              <video
                key={videoUrl}
                className="mx-auto max-h-[680px] w-full rounded-xl bg-black object-contain"
                controls
                playsInline
                preload="metadata"
              >
                <source
                  src={videoUrl}
                  type="video/mp4"
                />

                Your browser does not support
                MP4 video playback.
              </video>
            ) : (
              <div className="flex min-h-[520px] items-center justify-center rounded-xl bg-black">

                <div className="text-center">

                  <Video
                    size={42}
                    className="mx-auto mb-4 text-slate-600"
                  />

                  <p className="text-sm font-bold text-white">
                    Annotated video is not ready yet
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    The dashboard will update automatically.
                  </p>

                </div>

              </div>
            )}

          </div>

        </div>

        {/* SUMMARY */}

        <div className="space-y-6">

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

            <h2 className="text-base font-black text-slate-950">
              Traffic summary
            </h2>

            <div className="mt-5 space-y-4">

              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <span className="text-sm text-slate-500">
                  Congestion
                </span>

                <CongestionBadge
                  value={analysis?.congestion}
                />
              </div>

              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <span className="text-sm text-slate-500">
                  Total vehicles
                </span>

                <strong className="text-sm text-slate-900">
                  {formatNumber(totalVehicles)}
                </strong>
              </div>

              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <span className="text-sm text-slate-500">
                  Frames processed
                </span>

                <strong className="text-sm text-slate-900">
                  {formatNumber(frames)}
                </strong>
              </div>

              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <span className="text-sm text-slate-500">
                  FPS
                </span>

                <strong className="text-sm text-slate-900">
                  {formatNumber(fps, 2)}
                </strong>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-500">
                  Flow
                </span>

                <strong className="text-sm text-slate-900">
                  {formatNumber(flow)} / hr
                </strong>
              </div>

            </div>

          </section>

          {/* ANALYSIS INFO */}

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

            <h2 className="text-base font-black text-slate-950">
              Analysis information
            </h2>

            <div className="mt-4 space-y-3 text-sm">

              <div className="flex justify-between gap-4">
                <span className="text-slate-400">
                  Video
                </span>

                <span className="truncate font-semibold text-slate-700">
                  {analysis?.video_name || "—"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-400">
                  Analysis ID
                </span>

                <span className="max-w-[180px] truncate font-mono text-xs text-slate-600">
                  {analysis?.analysis_id || "—"}
                </span>
              </div>

              <div className="flex justify-between gap-4">
                <span className="text-slate-400">
                  Duration
                </span>

                <span className="font-semibold text-slate-700">
                  {formatNumber(duration, 2)} s
                </span>
              </div>

            </div>

          </section>

        </div>

      </section>

      {/* ================================================= */}
      {/* VEHICLE MIX */}
      {/* ================================================= */}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

        <div className="flex items-center justify-between">

          <div>
            <h2 className="text-base font-black text-slate-950">
              Vehicle classification
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              Vehicles detected by your trained model.
            </p>
          </div>

          <Car
            size={20}
            className="text-slate-300"
          />

        </div>

        {vehicleRows.length > 0 ? (
          <div className="mt-5 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">

            {vehicleRows.map(
              ([name, count]) => {

                const percentage =
                  totalVehicles > 0
                    ? (Number(count) /
                        totalVehicles) *
                      100
                    : 0;

                return (
                  <div
                    key={name}
                    className="rounded-xl border border-slate-100 bg-slate-50 p-4"
                  >

                    <div className="flex items-center justify-between gap-3">

                      <span className="text-sm font-bold text-slate-700">
                        {name}
                      </span>

                      <span className="text-lg font-black text-slate-950">
                        {formatNumber(count)}
                      </span>

                    </div>

                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200">

                      <div
                        className="h-full rounded-full bg-teal-500"
                        style={{
                          width: `${Math.min(
                            percentage,
                            100
                          )}%`,
                        }}
                      />

                    </div>

                    <p className="mt-2 text-[11px] font-semibold text-slate-400">
                      {formatNumber(
                        percentage,
                        1
                      )}
                      % of detected vehicles
                    </p>

                  </div>
                );
              }
            )}

          </div>
        ) : (
          <div className="mt-5 rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-400">
            Vehicle classification will appear after analysis.
          </div>
        )}

      </section>

      {/* ================================================= */}
      {/* HEATMAP */}
      {/* ================================================= */}

      <section className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">

        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">

          <div>
            <h2 className="flex items-center gap-2 text-base font-black text-slate-950">
              <Map
                size={18}
                className="text-teal-500"
              />

              Traffic heatmap
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              Generated from the completed traffic analysis.
            </p>
          </div>

        </div>

        <div className="bg-slate-50 p-5">

          {completed && heatmapUrl ? (
            <img
              src={heatmapUrl}
              alt="Traffic heatmap"
              className="mx-auto max-h-[650px] w-full rounded-xl border border-slate-200 bg-white object-contain"
            />
          ) : (
            <div className="flex min-h-[300px] items-center justify-center rounded-xl bg-white text-sm text-slate-400">
              Heatmap will appear after analysis.
            </div>
          )}

        </div>

      </section>

      {/* ================================================= */}
      {/* FOOTER STATUS */}
      {/* ================================================= */}

      <section className="flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-4 text-xs text-slate-400 sm:flex-row sm:items-center sm:justify-between">

        <div className="flex items-center gap-2">
          <Clock3 size={14} />

          <span>
            Backend analysis:
            {" "}
            <strong className="text-slate-600">
              {analysis?.status || "loading"}
            </strong>
          </span>
        </div>

        <span>
          Source:
          {" "}
          <strong className="text-slate-600">
            YOLO analysis backend
          </strong>
        </span>

      </section>

    </main>
  );
}