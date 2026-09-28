export const congestionColor = (level) => ({ critical: '#f43f5e', high: '#f59e0b', medium: '#fbbf24', low: '#14b8a6' }[level] || '#cbd5e1')
export const congestionText = (level) => ({ critical: 'text-rose-500', high: 'text-amber-500', medium: 'text-yellow-600', low: 'text-teal-600' }[level] || 'text-slate-500')
export const congestionBg = (level) => ({ critical: 'bg-rose-50', high: 'bg-amber-50', medium: 'bg-yellow-50', low: 'bg-teal-50' }[level] || 'bg-slate-50')
