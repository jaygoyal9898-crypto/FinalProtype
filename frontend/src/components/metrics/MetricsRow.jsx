import { Activity, Car, Gauge, Timer } from 'lucide-react'
import MetricCard from './MetricCard'

export default function MetricsRow({
  total = 0,
  density = 0,
  congestion = 'UNKNOWN',
  flow = 0,
}) {
  const congestionValue =
    congestion === 'LOW'
      ? 'LOW'
      : congestion === 'MEDIUM'
        ? 'MEDIUM'
        : congestion === 'HIGH'
          ? 'HIGH'
          : congestion === 'CRITICAL'
            ? 'CRITICAL'
            : '—'

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">

      {/* TOTAL VEHICLES */}

      <MetricCard
        label="Vehicles detected"
        value={Number(total).toLocaleString('en-IN')}
        suffix="vehicles"
        icon={Car}
      />

      {/* DENSITY */}

      <MetricCard
        label="Traffic density"
        value={Number(density).toFixed(2)}
        suffix="density"
        icon={Gauge}
        tone="amber"
      />

      {/* CONGESTION */}

      <MetricCard
        label="Congestion"
        value={congestionValue}
        suffix="current"
        icon={Activity}
        tone="rose"
      />

      {/* FLOW */}

      <MetricCard
        label="Traffic flow"
        value={Math.round(Number(flow)).toLocaleString('en-IN')}
        suffix="vehicles/hour"
        icon={Timer}
      />

    </div>
  )
}