/**
 * 강제 갱신 POST 후 백그라운드 재계산이 끝날 때까지 주기적으로 GET을 반복합니다.
 */

export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

/**
 * @param {object} opts
 * @param {() => Promise<void>} opts.loadOverview - overview 다시 불러오기
 * @param {() => boolean} opts.isStale - true면 아직 갱신 대기 중
 * @param {number} [opts.maxAttempts=24]
 * @param {number} [opts.intervalMs=2000]
 * @returns {Promise<boolean>} 새 데이터 반영 여부(타임아웃 시 false)
 */
export async function pollUntilBalanceOverviewFresh({
  loadOverview,
  isStale,
  maxAttempts = 24,
  intervalMs = 2000,
}) {
  for (let i = 0; i < maxAttempts; i++) {
    await sleep(intervalMs)
    await loadOverview()
    if (!isStale()) return true
  }
  return false
}

/**
 * @param {object} opts
 * @param {() => Promise<void>} opts.load
 * @param {() => boolean} opts.isStale
 */
export async function pollUntilBalanceDetailFresh({
  load,
  isStale,
  maxAttempts = 24,
  intervalMs = 2000,
}) {
  for (let i = 0; i < maxAttempts; i++) {
    await sleep(intervalMs)
    await load()
    if (!isStale()) return true
  }
  return false
}
