function toPositiveInt(value, fallback) {
  const n = Number(value)
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : fallback
}

function envInt(key, fallback) {
  return toPositiveInt(import.meta.env[key], fallback)
}

function pagePrefix(pageKey) {
  return String(pageKey || '')
    .trim()
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .toUpperCase()
}

export function getVirtualScrollOptions(pageKey, defaults = {}) {
  const prefix = pagePrefix(pageKey)

  const globalThreshold = envInt('VITE_VIRTUAL_THRESHOLD', 80)
  const globalRowHeight = envInt('VITE_VIRTUAL_ROW_HEIGHT', 52)
  const globalContainerHeight = envInt('VITE_VIRTUAL_CONTAINER_HEIGHT', 520)
  const globalOverscan = envInt('VITE_VIRTUAL_OVERSCAN', 8)

  const threshold = envInt(
    `VITE_VIRTUAL_${prefix}_THRESHOLD`,
    defaults.threshold ?? globalThreshold
  )
  const rowHeight = envInt(
    `VITE_VIRTUAL_${prefix}_ROW_HEIGHT`,
    defaults.rowHeight ?? globalRowHeight
  )
  const containerHeight = envInt(
    `VITE_VIRTUAL_${prefix}_CONTAINER_HEIGHT`,
    defaults.containerHeight ?? globalContainerHeight
  )
  const overscan = envInt(
    `VITE_VIRTUAL_${prefix}_OVERSCAN`,
    defaults.overscan ?? globalOverscan
  )

  return {
    threshold,
    rowHeight,
    containerHeight,
    overscan,
  }
}
