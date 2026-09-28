import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

const colors = [
  '#0f766e',
  '#f59e0b',
  '#ef4444',
  '#3b82f6',
  '#8b5cf6',
  '#14b8a6',
  '#f97316',
  '#6366f1',
  '#64748b',
  '#ec4899',
  '#84cc16',
  '#06b6d4',
  '#a855f7',
  '#78716c',
]

export default function VehicleMixChart({ vehicleCounts = {} }) {
  const data = Object.entries(vehicleCounts)
    .filter(([, value]) => Number(value) > 0)
    .map(([name, value], index) => ({
      name,
      value: Number(value),
      color: colors[index % colors.length],
    }))

  const total = data.reduce(
    (sum, item) => sum + item.value,
    0
  )

  if (!data.length) {
    return (
      <div className="flex h-44 items-center justify-center text-xs text-slate-400">
        No vehicle data available yet.
      </div>
    )
  }

  return (
    <div className="flex items-center gap-4">

      {/* PIE CHART */}

      <div className="h-44 w-1/2">

        <ResponsiveContainer width="100%" height="100%">

          <PieChart>

            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={48}
              outerRadius={68}
              paddingAngle={3}
            >

              {data.map((vehicle) => (
                <Cell
                  key={vehicle.name}
                  fill={vehicle.color}
                />
              ))}

            </Pie>

            <Tooltip
              formatter={(value, name) => [
                `${value} vehicles`,
                name,
              ]}
            />

          </PieChart>

        </ResponsiveContainer>

      </div>

      {/* LEGEND */}

      <div className="max-h-44 flex-1 space-y-2 overflow-y-auto">

        {data.map((vehicle) => {

          const percentage =
            total > 0
              ? ((vehicle.value / total) * 100).toFixed(1)
              : '0.0'

          return (
            <div
              key={vehicle.name}
              className="flex items-center gap-2 text-xs"
            >

              <span
                className="h-2 w-2 shrink-0 rounded-full"
                style={{
                  backgroundColor: vehicle.color,
                }}
              />

              <span className="truncate text-slate-500">
                {vehicle.name}
              </span>

              <b className="ml-auto whitespace-nowrap text-slate-800">
                {vehicle.value}
              </b>

              <span className="w-12 text-right text-[10px] text-slate-400">
                {percentage}%
              </span>

            </div>
          )
        })}

      </div>

    </div>
  )
}