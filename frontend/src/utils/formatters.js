export const compactNumber = (value) => new Intl.NumberFormat('en-IN', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
export const timeAgo = (minutes) => minutes === 0 ? 'Just now' : `${minutes} min ago`
export const levelLabel = (level) => ({ critical: 'Critical', high: 'High', medium: 'Moderate', low: 'Clear' }[level] || level)
