import { reactive } from 'vue'

export const networkState = reactive({
  activeRequests: 0,
  slowRequests: 0,
  lastErrorMessage: '',
  lastErrorAt: 0,
})

export function beginNetworkRequest() {
  networkState.activeRequests += 1
}

export function markSlowNetworkRequest() {
  networkState.slowRequests += 1
}

export function endNetworkRequest({ wasSlow = false } = {}) {
  networkState.activeRequests = Math.max(0, networkState.activeRequests - 1)
  if (wasSlow) {
    networkState.slowRequests = Math.max(0, networkState.slowRequests - 1)
  }
}

export function notifyNetworkError(message) {
  networkState.lastErrorMessage = message || '네트워크 오류가 발생했습니다.'
  networkState.lastErrorAt = Date.now()
}
