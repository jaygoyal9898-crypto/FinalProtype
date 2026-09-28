import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  BarChart3,
  Car,
  Gauge,
  RefreshCw,
  Timer,
  TrendingUp,
} from "lucide-react";

import { apiFetch } from "../api/client";

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
}) {
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

        <div className="rounded-xl bg-slate-50 p-2.5 text-slate-600">
          <Icon size={18} />
        </div>

      </div>
    </div>
  );
}

function CongestionBadge({ value }) {
  if (!value) {
    return <span className="text-slate-400">—</span>;
  }

  const level = String(value).toUpperCase();

  let classes = "bg-slate-100 text-slate-600";

  if (level === "LOW") {
    classes = "bg-emerald-50 text-emerald-600";
  }

  if (level === "MEDIUM") {
    classes = "bg-amber-50 text-amber-600";
  }

  if (level === "HIGH") {
    classes = "bg-rose-50 text-rose-600";
  }

  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-bold ${classes}`}
    >
      {level}
    </span>
  );
}

export default function Analytics() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadAnalytics = useCallback(async () => {
    try {
      setError("");

      const result = await apiFetch(
        "/current-analysis"
      );

      setAnalysis(result);
    } catch (err) {
      console.error(err);

      setError(
        err?.message ||
          "Could not load analytics."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadAnalytics();

    const timer = setInterval(
      loadAnalytics,
      5000
    );

    return () => clearInterval(timer);
  }, [loadAnalytics]);

  const vehicleCounts =
    analysis?.vehicle_counts || {};

  const vehicleRows = useMemo(() => {
    return Object.entries(vehicleCounts)
      .sort(
        (a, b) =>
          Number(b[1]) - Number(a[1])
      );
  }, [vehicleCounts]);

  const totalVehicles =
    analysis?.total_vehicles ?? 0;

  const density =
    analysis?.average_density ??
    analysis?.density ??
    0;

  const flow =
    analysis?.flow_vph ?? 0;

  const duration =
    analysis?.duration_s ?? 0;

  const frames =
    analysis?.frames ??
    analysis?.total_frames ??
    0;

  const fps =
    analysis?.fps ?? 0;

  const completed =
    analysis?.status === "completed" ||
    analysis?.completed === true;

  return (
    <main className="mx-auto max-w-[1600px] space-y-6 px-6 py-7 lg:px-10">

      {/* ================================================= */}
      {/* HEADER */}
      {/* ================================================= */}

      <section className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

        <div>
          <p className="text-xs font-semibold text-slate-400">
            Insights / Analytics
          </p>

          <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-950">
            Network analytics
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Historical results and vehicle composition from your traffic analysis.
          </p>
        </div>

        <button
          onClick={loadAnalytics}
          disabled={loading}
          className="inline-flex w-fit items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-bold text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
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

      </section>

      {/* ================================================= */}
      {/* ERROR */}
      {/* ================================================= */}

      {error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* ================================================= */}
      {/* OVERVIEW METRICS */}
      {/* ================================================= */}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

        <MetricCard
          label="Vehicles detected"
          value={formatNumber(
            totalVehicles
          )}
          suffix="vehicles"
          icon={Car}
        />

        <MetricCard
          label="Traffic density"
          value={formatNumber(
            density,
            2
          )}
          suffix="index"
          icon={Activity}
        />

        <MetricCard
          label="Traffic flow"
          value={formatNumber(flow)}
          suffix="vehicles / hour"
          icon={TrendingUp}
        />

        <MetricCard
          label="Average speed"
          value="—"
          suffix="not available"
          icon={Gauge}
        />

      </section>

      {/* ================================================= */}
      {/* ANALYSIS SUMMARY */}
      {/* ================================================= */}

      <section className="grid gap-6 lg:grid-cols-2">

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

          <div className="flex items-center justify-between">

            <div>
              <h2 className="text-base font-black text-slate-950">
                Analysis summary
              </h2>

              <p className="mt-1 text-xs text-slate-400">
                Results from the latest completed traffic run.
              </p>
            </div>

            <BarChart3
              size={20}
              className="text-slate-300"
            />

          </div>

          <div className="mt-5 space-y-4">

            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <span className="text-sm text-slate-500">
                Analysis status
              </span>

              <span
                className={
                  completed
                    ? "font-bold text-emerald-600"
                    : "font-bold text-amber-600"
                }
              >
                {String(
                  analysis?.status ||
                    "UNKNOWN"
                ).toUpperCase()}
              </span>
            </div>

            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <span className="text-sm text-slate-500">
                Congestion
              </span>

              <CongestionBadge
                value={
                  analysis?.congestion
                }
              />
            </div>

            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <span className="text-sm text-slate-500">
                Video duration
              </span>

              <strong className="text-sm text-slate-900">
                {formatNumber(
                  duration,
                  2
                )}{" "}
                sec
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

            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-500">
                Processing FPS
              </span>

              <strong className="text-sm text-slate-900">
                {formatNumber(fps, 2)}
              </strong>
            </div>

          </div>

        </div>

        {/* FLOW */}

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

          <h2 className="text-base font-black text-slate-950">
            Traffic flow
          </h2>

          <p className="mt-1 text-xs text-slate-400">
            Estimated vehicle flow from the completed analysis.
          </p>

          <div className="mt-8">

            <div className="flex items-end gap-3">

              <span className="text-5xl font-black tracking-tight text-slate-950">
                {formatNumber(flow)}
              </span>

              <span className="pb-2 text-sm font-semibold text-slate-400">
                vehicles/hour
              </span>

            </div>

            <div className="mt-6 rounded-xl bg-slate-50 p-4">

              <div className="flex items-center gap-3">

                <div className="rounded-lg bg-teal-50 p-2 text-teal-600">
                  <TrendingUp size={18} />
                </div>

                <div>
                  <p className="text-xs font-semibold text-slate-400">
                    Analysis flow
                  </p>

                  <p className="text-sm font-bold text-slate-800">
                    Based on detected vehicle movement
                  </p>
                </div>

              </div>

            </div>

          </div>

        </div>

      </section>

      {/* ================================================= */}
      {/* VEHICLE MIX */}
      {/* ================================================= */}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

        <div className="flex items-center justify-between">

          <div>
            <h2 className="text-base font-black text-slate-950">
              Fleet composition
            </h2>

            <p className="mt-1 text-xs text-slate-400">
              Vehicle classes detected by the trained YOLO model.
            </p>
          </div>

          <Car
            size={20}
            className="text-slate-300"
          />

        </div>

        {vehicleRows.length > 0 ? (
          <div className="mt-6 overflow-x-auto">

            <table className="w-full min-w-[600px] text-left">

              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wider text-slate-400">

                  <th className="px-4 py-3 font-bold">
                    Vehicle type
                  </th>

                  <th className="px-4 py-3 text-right font-bold">
                    Count
                  </th>

                  <th className="px-4 py-3 text-right font-bold">
                    Share
                  </th>

                  <th className="px-4 py-3 font-bold">
                    Distribution
                  </th>

                </tr>
              </thead>

              <tbody>

                {vehicleRows.map(
                  ([name, count]) => {

                    const percentage =
                      totalVehicles > 0
                        ? (Number(count) /
                            totalVehicles) *
                          100
                        : 0;

                    return (
                      <tr
                        key={name}
                        className="border-b border-slate-100 last:border-0"
                      >

                        <td className="px-4 py-4 text-sm font-bold text-slate-800">
                          {name}
                        </td>

                        <td className="px-4 py-4 text-right text-sm font-black text-slate-950">
                          {formatNumber(
                            count
                          )}
                        </td>

                        <td className="px-4 py-4 text-right text-sm font-semibold text-slate-500">
                          {formatNumber(
                            percentage,
                            1
                          )}
                          %
                        </td>

                        <td className="px-4 py-4">

                          <div className="flex items-center gap-3">

                            <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100">

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

                          </div>

                        </td>

                      </tr>
                    );
                  }
                )}

              </tbody>

            </table>

          </div>
        ) : (
          <div className="mt-6 rounded-xl bg-slate-50 p-10 text-center text-sm text-slate-400">
            No vehicle classification data is available yet.
          </div>
        )}

      </section>

      {/* ================================================= */}
      {/* DETAILED STATISTICS */}
      {/* ================================================= */}

      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600">
              <Timer size={18} />
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-400">
                Duration
              </p>

              <p className="mt-1 text-lg font-black text-slate-950">
                {formatNumber(
                  duration,
                  2
                )} s
              </p>
            </div>

          </div>

        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-teal-50 p-2.5 text-teal-600">
              <Activity size={18} />
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-400">
                Density
              </p>

              <p className="mt-1 text-lg font-black text-slate-950">
                {formatNumber(
                  density,
                  2
                )}
              </p>
            </div>

          </div>

        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-amber-50 p-2.5 text-amber-600">
              <Gauge size={18} />
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-400">
                Flow
              </p>

              <p className="mt-1 text-lg font-black text-slate-950">
                {formatNumber(flow)}
              </p>
            </div>

          </div>

        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

          <div className="flex items-center gap-3">

            <div className="rounded-xl bg-rose-50 p-2.5 text-rose-600">
              <Car size={18} />
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-400">
                Vehicles
              </p>

              <p className="mt-1 text-lg font-black text-slate-950">
                {formatNumber(
                  totalVehicles
                )}
              </p>
            </div>

          </div>

        </div>

      </section>

      {/* ================================================= */}
      {/* ANALYSIS ID */}
      {/* ================================================= */}

      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">

        <div className="flex flex-col gap-2 text-xs sm:flex-row sm:items-center sm:justify-between">

          <span className="font-semibold text-slate-400">
            Current analysis
          </span>

          <span className="font-mono text-slate-600">
            {analysis?.analysis_id || "—"}
          </span>

        </div>

      </section>

    </main>
  );
}