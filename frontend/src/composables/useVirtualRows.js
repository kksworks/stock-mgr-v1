import { computed, ref } from 'vue'

export function useVirtualRows(itemsRef, options = {}) {
  const rowHeight = options.rowHeight ?? 52
  const containerHeight = options.containerHeight ?? 480
  const overscan = options.overscan ?? 8
  const threshold = options.threshold ?? 80

  const scrollTop = ref(0)

  const isVirtualEnabled = computed(() => (itemsRef.value?.length || 0) >= threshold)
  const totalRows = computed(() => itemsRef.value?.length || 0)
  const viewportCount = computed(() => Math.max(1, Math.ceil(containerHeight / rowHeight)))

  const startIndex = computed(() => {
    if (!isVirtualEnabled.value) return 0
    const raw = Math.floor(scrollTop.value / rowHeight) - overscan
    return Math.max(0, raw)
  })

  const endIndex = computed(() => {
    if (!isVirtualEnabled.value) return totalRows.value
    return Math.min(totalRows.value, startIndex.value + viewportCount.value + overscan * 2)
  })

  const visibleItems = computed(() => {
    if (!isVirtualEnabled.value) return itemsRef.value || []
    return (itemsRef.value || []).slice(startIndex.value, endIndex.value)
  })

  const topSpacerHeight = computed(() => (isVirtualEnabled.value ? startIndex.value * rowHeight : 0))
  const bottomSpacerHeight = computed(() => {
    if (!isVirtualEnabled.value) return 0
    const hiddenBottomRows = Math.max(0, totalRows.value - endIndex.value)
    return hiddenBottomRows * rowHeight
  })

  function onVirtualScroll(event) {
    scrollTop.value = event?.target?.scrollTop || 0
  }

  function getRealIndex(visibleIndex) {
    return startIndex.value + visibleIndex
  }

  return {
    rowHeight,
    containerHeight,
    isVirtualEnabled,
    visibleItems,
    topSpacerHeight,
    bottomSpacerHeight,
    onVirtualScroll,
    getRealIndex,
  }
}
