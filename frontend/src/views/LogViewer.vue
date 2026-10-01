<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="d-flex align-items-center gap-2">
        <MaterialIcon name="description" size="1.75rem" />
        시스템 로그 (최근 100건)
      </h1>
      <button type="button" class="btn btn-danger d-inline-flex align-items-center gap-1" @click="clearLogs">
        <MaterialIcon name="delete_sweep" size="1.125rem" />
        로그 초기화
      </button>
    </div>
    <PageLoadingPlaceholder v-if="loading && logs.length === 0" variant="table" :rows="8" />

    <div v-else class="card">
      <div class="card-body p-0">
        <div
          class="table-responsive"
          :style="isVirtualEnabled ? { maxHeight: `${containerHeight}px`, overflowY: 'auto' } : {}"
          @scroll="onVirtualScroll"
        >
          <table class="table table-striped table-hover mb-0">
            <thead class="table-light">
              <tr>
                <th style="width: 200px;">시간</th>
                <th style="width: 100px;">레벨</th>
                <th>메시지</th>
                <th style="width: 150px;">모듈</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isVirtualEnabled && topSpacerHeight > 0" aria-hidden="true">
                <td colspan="4" :style="{ height: `${topSpacerHeight}px`, padding: 0, border: 0 }"></td>
              </tr>
              <tr
                v-for="(log, idx) in visibleLogs"
                :key="`${log.id}-${isVirtualEnabled ? getRealIndex(idx) : idx}`"
                :style="isVirtualEnabled ? { height: `${rowHeight}px` } : {}"
              >
                <td>{{ formatTime(log.timestamp) }}</td>
                <td>
                  <span v-if="log.level === 'INFO'" class="badge bg-info text-dark">INFO</span>
                  <span v-else-if="log.level === 'WARNING'" class="badge bg-warning text-dark">WARN</span>
                  <span v-else-if="log.level === 'ERROR'" class="badge bg-danger">ERROR</span>
                  <span v-else class="badge bg-secondary">{{ log.level }}</span>
                </td>
                <td>{{ log.message }}</td>
                <td class="text-muted small">{{ log.module }}:{{ log.lineno }}</td>
              </tr>
              <tr v-if="isVirtualEnabled && bottomSpacerHeight > 0" aria-hidden="true">
                <td colspan="4" :style="{ height: `${bottomSpacerHeight}px`, padding: 0, border: 0 }"></td>
              </tr>
              <tr v-if="!loading && logs.length === 0">
                <td colspan="4" class="text-center py-3">기록된 로그가 없습니다.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { systemApi, getApiErrorMessage } from '../api'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { useVirtualRows } from '../composables/useVirtualRows'
import { getVirtualScrollOptions } from '../config/virtualScroll'
import { formatKstDateTime } from '../utils/dateTime'

const emit = defineEmits(['flash'])
const logs = ref([])
const loading = ref(true)
let logsAbortController = null
let logsReqId = 0
const {
  rowHeight,
  containerHeight,
  isVirtualEnabled,
  visibleItems: visibleLogs,
  topSpacerHeight,
  bottomSpacerHeight,
  onVirtualScroll,
  getRealIndex,
} = useVirtualRows(logs, getVirtualScrollOptions('logs', {
  rowHeight: 50,
  containerHeight: 520,
  threshold: 80,
}))

function formatTime(ts) {
  if (!ts) return ''
  return formatKstDateTime(ts)
}

async function load() {
  if (logsAbortController) {
    logsAbortController.abort()
  }
  logsAbortController = new AbortController()
  const reqId = ++logsReqId
  const { data } = await systemApi.getLogs({ signal: logsAbortController.signal })
  if (reqId !== logsReqId) return
  logs.value = data
}

onMounted(async () => {
  try {
    await load()
  } catch (e) {
    if (e?.code !== 'ERR_CANCELED') {
      emit('flash', getApiErrorMessage(e, '로그를 불러오지 못했습니다.'), 'alert-danger')
    }
  } finally {
    loading.value = false
  }
})

async function clearLogs() {
  if (!confirm('모든 로그를 삭제하시겠습니까?')) return
  try {
    await systemApi.clearLogs()
    emit('flash', '시스템 로그가 초기화되었습니다.', 'alert-success')
    await load()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '삭제 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

onBeforeUnmount(() => {
  logsAbortController?.abort()
})
</script>
