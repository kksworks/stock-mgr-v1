/**
 * balance_history.prev_day_asset_change + 원금대비 % 표시용
 */

export function formatPrevDayMoney(change) {
  if (change == null || Number.isNaN(Number(change))) return '—'
  const n = Math.round(Number(change))
  const sign = n > 0 ? '+' : ''
  return `${sign}₩${n.toLocaleString()}`
}

export function formatPrevDayPercent(pct) {
  if (pct == null || Number.isNaN(Number(pct))) return ''
  const n = Number(pct)
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toFixed(2)}%`
}

/** 상승/하락 색 (전역 .text-stock-up / .text-stock-down) */
export function prevDayChangeClass(change) {
  if (change == null || Number.isNaN(Number(change))) return 'text-muted'
  const n = Number(change)
  if (n > 0) return 'text-stock-up'
  if (n < 0) return 'text-stock-down'
  return 'text-muted'
}
