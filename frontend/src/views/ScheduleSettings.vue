<template>
  <div>
    <div class="d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center gap-2 mb-4">
      <h1 class="mb-0 d-flex align-items-center gap-2">
        <MaterialIcon name="schedule" size="1.75rem" />
        크롤링 스케줄
      </h1>
    </div>
    <p class="text-muted mb-4">
      자동 크롤링 스케줄을 관리합니다. 관리자만 설정할 수 있습니다.
    </p>

    <PageLoadingPlaceholder v-if="initializing" variant="cards" :rows="4" />

    <template v-else>
    <!-- 계좌 현황 자동 갱신 (Cron) -->
    <div class="card mb-4 shadow-sm">
      <div class="card-header border-bottom-0 bg-transparent py-3">
        <h5 class="card-title mb-0 d-flex align-items-center gap-2">
          <MaterialIcon name="account_balance_wallet" color="var(--text-primary)" />
          계좌 현황 자동 갱신 (전체 계좌)
        </h5>
      </div>
      <div class="card-body">
        <div v-if="loadError" class="alert alert-danger">{{ loadError }}</div>
        <template v-else>
          <p class="small text-muted mb-4">
            정기적으로 모든 계좌의 현재가를 크롤링하여 balance_history(스냅샷)를 생성합니다.
          </p>
          <div class="mb-4">
            <div class="form-check form-switch">
              <input
                id="schedule-enabled"
                v-model="form.enabled"
                type="checkbox"
                class="form-check-input"
              >
              <label class="form-check-label fw-bold" for="schedule-enabled">스케줄 활성화</label>
            </div>
          </div>

          <div class="mb-4 p-3 bg-light rounded-3">
            <label class="form-label small fw-bold text-uppercase tracking-wider">실행 주기 설정 (Cron)</label>
            <div class="d-flex flex-wrap gap-2 align-items-center mb-2">
              <select v-model="preset" class="form-select" style="width: auto;">
                <option value="custom">사용자 지정 (cron)</option>
                <option value="0 9 * * *">매일 09:00</option>
                <option value="0 15 * * *">매일 15:00</option>
                <option value="0 9,15 * * 1-5">평일 09:00, 15:00</option>
                <option value="0 */2 * * *">2시간마다</option>
              </select>
              <input
                v-if="preset === 'custom'"
                v-model="form.cron"
                type="text"
                class="form-control"
                placeholder="0 9,15 * * 1-5"
                style="max-width: 200px;"
              >
            </div>
            <div class="text-muted smallest">분 시 일 월 요일 (예: 0 9,15 * * 1-5 = 평일 09:00·15:00)</div>
          </div>

          <div class="row g-3 mb-4">
            <div class="col-12 col-md-6">
              <div class="card border bg-transparent h-100">
                <div class="card-body p-2 d-flex align-items-center gap-3">
                  <MaterialIcon name="history" size="1.5rem" color="#6c757d" />
                  <div>
                    <div class="text-muted smallest">마지막 실행</div>
                    <div class="fw-bold small">{{ lastRunLabel }}</div>
                  </div>
                </div>
              </div>
            </div>
            <div class="col-12 col-md-6">
              <div class="card border bg-transparent h-100">
                <div class="card-body p-2 d-flex align-items-center gap-3">
                  <MaterialIcon name="update" size="1.5rem" color="#6c757d" />
                  <div>
                    <div class="text-muted smallest">다음 실행 예정</div>
                    <div class="fw-bold small">{{ nextRunLabel }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="d-flex gap-2">
            <button
              type="button"
              class="btn btn-primary px-4"
              :disabled="saving"
              @click="saveSchedule"
            >
              <MaterialIcon v-if="saving" name="sync" class="spin" />
              {{ saving ? '저장 중...' : '설정 저장' }}
            </button>
            <button
              type="button"
              class="btn btn-outline-secondary"
              :disabled="refreshing"
              @click="runNow"
            >
              <MaterialIcon v-if="refreshing" name="sync" class="spin" />
              {{ refreshing ? '실행 중...' : '지금 한 번 실행' }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <!-- 현재가 갱신 정책 (자동 stale / 강제 버튼 쿨다운) -->
    <div class="card mb-4 shadow-sm border-0 border-top border-4 border-secondary">
      <div class="card-header border-bottom-0 bg-transparent py-3">
        <h5 class="card-title mb-0 d-flex align-items-center gap-2">
          <MaterialIcon name="speed" color="var(--text-secondary)" />
          현재가 갱신 정책
        </h5>
      </div>
      <div class="card-body">
        <p class="small text-muted mb-4">
          자동 갱신은 DB 현재가가 아래 분 수보다 오래되었을 때만 크롤합니다. 「현재가 갱신」 버튼은 최소 간격(초)을 지켜야 다시 실행됩니다.
        </p>
        <div v-if="priceLoadError" class="alert alert-warning small">{{ priceLoadError }}</div>
        <div class="row g-3 mb-4">
          <div class="col-12 col-md-6">
            <label class="form-label small fw-bold">자동 크롤 기준 (분)</label>
            <input
              v-model.number="priceForm.refresh_threshold_minutes"
              type="number"
              class="form-control"
              min="1"
              max="1440"
              style="max-width: 140px;"
            >
            <div class="text-muted smallest mt-1">이 시간보다 오래된 현재가만 외부에서 다시 가져옵니다.</div>
          </div>
          <div class="col-12 col-md-6">
            <label class="form-label small fw-bold">강제 갱신 버튼 쿨다운 (초)</label>
            <input
              v-model.number="priceForm.force_refresh_cooldown_sec"
              type="number"
              class="form-control"
              min="5"
              max="86400"
              style="max-width: 140px;"
            >
            <div class="text-muted smallest mt-1">같은 계좌에 대해 버튼으로 전량 재크롤할 수 있는 최소 간격입니다.</div>
          </div>
        </div>
        <button
          type="button"
          class="btn btn-secondary px-4"
          :disabled="savingPrice"
          @click="savePriceSettings"
        >
          <MaterialIcon v-if="savingPrice" name="sync" class="spin" />
          {{ savingPrice ? '저장 중...' : '정책 저장' }}
        </button>
      </div>
    </div>

    <!-- 포트폴리오 티커 가격 갱신 (Interval) -->
    <div class="card mb-4 shadow-sm border-0 border-top border-4 border-info">
      <div class="card-header border-bottom-0 bg-transparent py-3">
        <h5 class="card-title mb-0 d-flex align-items-center gap-2">
          <MaterialIcon name="trending_up" color="var(--info)" />
          포트폴리오 티커 가격 자동 갱신
        </h5>
      </div>
      <div class="card-body">
        <p class="small text-muted mb-4">
          전체 포트폴리오에 등록된 종목들의 현재가를 주기적으로 갱신합니다. (실시간 리밸런싱 지표 유지용)
        </p>
        <div class="mb-4">
          <div class="form-check form-switch">
            <input
              id="portfolio-enabled"
              v-model="portfolioForm.enabled"
              type="checkbox"
              class="form-check-input"
            >
            <label class="form-check-label fw-bold" for="portfolio-enabled">스케줄 활성화</label>
          </div>
        </div>

        <div class="mb-4 p-3 bg-light rounded-3">
          <label class="form-label small fw-bold text-uppercase tracking-wider">실행 주기 설정 (분 단위)</label>
          <div class="d-flex align-items-center gap-2">
            <input
              v-model.number="portfolioForm.interval"
              type="number"
              class="form-control"
              style="max-width: 120px;"
              min="1"
            >
            <span class="fw-bold text-muted">분 마다 실행</span>
          </div>
          <div class="text-muted smallest mt-1">너무 짧은 주기는 서버 부하와 도메인 차단을 유발할 수 있습니다. (추천: 10~30분)</div>
        </div>

        <div class="row g-3 mb-4">
          <div class="col-12 col-md-6">
            <div class="card border bg-transparent h-100">
              <div class="card-body p-2 d-flex align-items-center gap-3">
                <MaterialIcon name="history" size="1.5rem" color="#6c757d" />
                <div>
                  <div class="text-muted smallest">마지막 실행</div>
                  <div class="fw-bold small">{{ portfolioLastRunLabel }}</div>
                </div>
              </div>
            </div>
          </div>
          <div class="col-12 col-md-6">
            <div class="card border bg-transparent h-100">
              <div class="card-body p-2 d-flex align-items-center gap-3">
                <MaterialIcon name="update" size="1.5rem" color="#6c757d" />
                <div>
                  <div class="text-muted smallest">다음 실행 예정</div>
                  <div class="fw-bold small">{{ portfolioNextRunLabel }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="d-flex gap-2">
          <button
            type="button"
            class="btn btn-info text-white px-4"
            :disabled="savingPortfolio"
            @click="savePortfolioSchedule"
          >
            <MaterialIcon v-if="savingPortfolio" name="sync" class="spin" />
            {{ savingPortfolio ? '저장 중...' : '설정 저장' }}
          </button>
          <button
            type="button"
            class="btn btn-outline-secondary"
            :disabled="refreshingPortfolio"
            @click="runPortfolioNow"
          >
            <MaterialIcon v-if="refreshingPortfolio" name="sync" class="spin" />
            {{ refreshingPortfolio ? '실행 중...' : '지금 한 번 실행' }}
          </button>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { scheduleApi, getApiErrorMessage } from '../api'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { formatKstDateTime } from '../utils/dateTime'

const emit = defineEmits(['flash'])

// --- Account Balance Refresh (Cron) ---
const form = ref({ enabled: false, cron: '0 9,15 * * 1-5' })
const preset = ref('0 9,15 * * 1-5')
const lastRun = ref(null)
const nextRun = ref(null)
const saving = ref(false)
const refreshing = ref(false)

const lastRunLabel = computed(() => formatDt(lastRun.value))
const nextRunLabel = computed(() => {
  if (!nextRun.value) return form.value.enabled ? '스케줄 적용 후 표시' : '-'
  return formatDt(nextRun.value)
})

// --- Portfolio Ticker Refresh (Interval) ---
const portfolioForm = ref({ enabled: true, interval: 10 })
const portfolioLastRun = ref(null)
const portfolioNextRun = ref(null)
const savingPortfolio = ref(false)
const refreshingPortfolio = ref(false)
let scheduleAbortController = null
let scheduleReqId = 0

const portfolioLastRunLabel = computed(() => formatDt(portfolioLastRun.value))
const portfolioNextRunLabel = computed(() => {
  if (!portfolioNextRun.value) return portfolioForm.value.enabled ? '스케줄 적용 후 표시' : '-'
  return formatDt(portfolioNextRun.value)
})

const loadError = ref('')
const initializing = ref(true)

const priceForm = ref({ refresh_threshold_minutes: 10, force_refresh_cooldown_sec: 60 })
const savingPrice = ref(false)
const priceLoadError = ref('')

function formatDt(val) {
  if (!val) return '-'
  return formatKstDateTime(val, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

async function load() {
  if (scheduleAbortController) {
    scheduleAbortController.abort()
  }
  scheduleAbortController = new AbortController()
  const reqId = ++scheduleReqId
  loadError.value = ''
  try {
    // 1. Account Schedule Load
    const { data: bData } = await scheduleApi.getSchedule({ signal: scheduleAbortController.signal })
    if (reqId !== scheduleReqId) return
    form.value = { enabled: bData.enabled, cron: bData.cron || '0 9,15 * * 1-5' }
    lastRun.value = bData.last_run ?? null
    nextRun.value = bData.next_run ?? null
    preset.value = ['0 9 * * *', '0 15 * * *', '0 9,15 * * 1-5', '0 */2 * * *'].includes(form.value.cron)
      ? form.value.cron
      : 'custom'

    // 2. Portfolio Schedule Load
    const { data: pData } = await scheduleApi.getPortfolioSchedule({ signal: scheduleAbortController.signal })
    if (reqId !== scheduleReqId) return
    portfolioForm.value = { enabled: pData.enabled, interval: pData.interval || 10 }
    portfolioLastRun.value = pData.last_run ?? null
    portfolioNextRun.value = pData.next_run ?? null

    priceLoadError.value = ''
    try {
      const { data: priceData } = await scheduleApi.getPriceSettings({ signal: scheduleAbortController.signal })
      if (reqId !== scheduleReqId) return
      priceForm.value = {
        refresh_threshold_minutes: priceData.refresh_threshold_minutes ?? 10,
        force_refresh_cooldown_sec: priceData.force_refresh_cooldown_sec ?? 60,
      }
    } catch (pe) {
      if (pe?.code === 'ERR_CANCELED') return
      priceLoadError.value = getApiErrorMessage(pe, '현재가 정책을 불러오지 못했습니다.')
    }
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    loadError.value = getApiErrorMessage(e, '설정을 불러오지 못했습니다.')
  } finally {
    if (reqId === scheduleReqId) {
      initializing.value = false
    }
  }
}

async function saveSchedule() {
  saving.value = true
  try {
    const cron = preset.value === 'custom' ? form.value.cron : preset.value
    const { data } = await scheduleApi.updateSchedule({ enabled: form.value.enabled, cron })
    nextRun.value = data.next_run ?? null
    emit('flash', data.message || '저장되었습니다.', 'alert-success')
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '저장에 실패했습니다.'), 'alert-danger')
  } finally {
    saving.value = false
  }
}

async function savePortfolioSchedule() {
  savingPortfolio.value = true
  try {
    const { data } = await scheduleApi.updatePortfolioSchedule(portfolioForm.value)
    portfolioNextRun.value = data.next_run ?? null
    emit('flash', data.message || '포트폴리오 스케줄이 저장되었습니다.', 'alert-success')
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '저장에 실패했습니다.'), 'alert-danger')
  } finally {
    savingPortfolio.value = false
  }
}

async function runNow() {
  refreshing.value = true
  try {
    const { data } = await scheduleApi.runRefreshNow()
    emit('flash', `완료: ${data.count}개 계좌 갱신됨.`, 'alert-success')
    await load()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '실행 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    refreshing.value = false
  }
}

async function savePriceSettings() {
  savingPrice.value = true
  try {
    const { data } = await scheduleApi.updatePriceSettings({
      refresh_threshold_minutes: priceForm.value.refresh_threshold_minutes,
      force_refresh_cooldown_sec: priceForm.value.force_refresh_cooldown_sec,
    })
    emit('flash', data.message || '저장되었습니다.', 'alert-success')
    priceLoadError.value = ''
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '저장에 실패했습니다.'), 'alert-danger')
  } finally {
    savingPrice.value = false
  }
}

async function runPortfolioNow() {
  refreshingPortfolio.value = true
  try {
    const { data } = await scheduleApi.runPortfolioRefreshNow()
    emit('flash', `완료: ${data.count}개 종목 가격 갱신됨.`, 'alert-success')
    await load()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '실행 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    refreshingPortfolio.value = false
  }
}

onMounted(load)

onBeforeUnmount(() => {
  scheduleAbortController?.abort()
})
</script>

<style scoped>
.smallest {
  font-size: 0.7rem;
}
.tracking-wider {
  letter-spacing: 0.05em;
}
.spin {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
