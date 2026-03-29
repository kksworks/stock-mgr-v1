const KST_TIME_ZONE = 'Asia/Seoul'

function toDate(value) {
  if (!value) return null
  const date = value instanceof Date ? value : new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

export function formatKstDateTime(value, options = {}) {
  const date = toDate(value)
  if (!date) return value || ''
  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: KST_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    ...options,
  }).format(date)
}

export function toKstDateInput(value) {
  const date = toDate(value)
  if (!date) return ''
  return new Intl.DateTimeFormat('sv-SE', {
    timeZone: KST_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(date)
}

export function getKstTodayDateInput() {
  return toKstDateInput(new Date())
}
