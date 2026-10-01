<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="d-flex align-items-center gap-2">
        <MaterialIcon name="pie_chart" size="1.75rem" />
        포트폴리오 전략 관리
      </h1>
    </div>
    <div v-if="!authStore.isAuthenticated" class="alert alert-info mb-3 d-flex align-items-start gap-2">
      <MaterialIcon name="info" size="1.25rem" class="flex-shrink-0 mt-1" />
      <span>로그인을 하시면 자신만의 포트폴리오 전략을 등록하고 관리할 수 있습니다.</span>
    </div>
    <PageLoadingPlaceholder v-if="loading && portfolios.length === 0" variant="cards" :rows="4" />

    <div v-else class="row">
      <div v-if="authStore.isAuthenticated" class="col-md-6">
        <div class="action-panel">
          <h4>포트폴리오 생성 / 수정</h4>
          <form @submit.prevent="save">
            <div class="mb-3">
              <label class="form-label">포트폴리오명</label>
              <input v-model="form.name" type="text" class="form-control" placeholder="예: 배당 성장 전략" required>
            </div>
            <div class="mb-3">
              <label class="form-label">설명</label>
              <textarea v-model="form.description" class="form-control" rows="2" placeholder="전략에 대한 설명을 입력하세요."></textarea>
            </div>
            <div v-if="authStore.isAdmin" class="mb-3 d-flex align-items-center gap-3">
              <div class="form-check form-switch mb-0">
                <input v-model="form.is_public" class="form-check-input" type="checkbox" id="isPublicSwitch">
                <label class="form-check-label fw-bold" for="isPublicSwitch">전체 공개</label>
              </div>
              <div v-if="form.is_public" class="d-flex align-items-center gap-2">
                <label class="form-label mb-0 small fw-bold text-muted">권한 레벨:</label>
                <select v-model.number="form.level" class="form-select form-select-sm" style="width: 80px;">
                  <option v-for="n in 5" :key="n" :value="n">LV.{{ n }}</option>
                </select>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">구성 종목</label>
              <div class="input-group mb-2">
                <input v-model="tickerQuery" type="text" class="form-control" placeholder="종목명 또는 티커 검색" @keypress.enter.prevent="searchTicker">
                <button class="btn btn-outline-secondary" type="button" @click="searchTicker">검색</button>
              </div>
              <div v-if="searchResults.length" class="list-group mb-3" style="max-height: 200px; overflow-y: auto;">
                <button
                  v-for="item in searchResults"
                  :key="item.ticker"
                  type="button"
                  class="list-group-item list-group-item-action"
                  @click="addItem(item)"
                >
                  {{ item.name }} ({{ item.ticker }})
                </button>
              </div>
              <table class="table table-sm table-bordered">
                <thead>
                  <tr>
                    <th>종목명 (티커)</th>
                    <th style="width: 100px;">비율(%)</th>
                    <th style="width: 50px;">삭제</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in form.items" :key="item.ticker">
                    <td>{{ item.name }} <small class="text-muted">({{ item.ticker }})</small></td>
                    <td>
                      <input v-model.number="item.ratio" type="number" step="0.01" class="form-control form-control-sm" placeholder="%" required>
                    </td>
                    <td>
                      <button type="button" class="btn btn-sm btn-danger" @click="form.items.splice(idx, 1)">X</button>
                    </td>
                  </tr>
                </tbody>
              </table>
              <p class="mb-2 small" :class="isRatioSumValid ? 'text-success' : 'text-danger'">
                비율 합계: <strong>{{ ratioSumDisplay }}%</strong>
                <span v-if="!isRatioSumValid && form.items.length > 0"> — 합계 100% (소수 둘째 자리 기준)가 되어야 저장됩니다.</span>
              </p>
            </div>
            <div class="d-grid gap-2">
              <button type="submit" class="btn btn-primary" :disabled="!isRatioSumValid">저장</button>
              <button type="button" class="btn btn-secondary" @click="resetForm">초기화</button>
            </div>
          </form>
        </div>
      </div>
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">저장된 포트폴리오</div>
          <div class="card-body">
            <div class="list-group list-group-flush">
              <div v-for="pf in portfolios" :key="pf.id" class="list-group-item px-0">
                <div class="d-flex w-100 justify-content-between align-items-center mb-2">
                  <div class="d-flex align-items-center gap-2">
                    <h5 class="mb-0">{{ pf.name }}</h5>
                    <span v-if="pf.is_public" class="badge bg-primary-soft text-primary border border-primary-soft small d-flex align-items-center gap-1">
                      공용
                      <span class="opacity-75" style="font-size: 0.7rem; font-weight: 800;">LV.{{ pf.level || 1 }}</span>
                    </span>
                    <span v-else class="badge bg-light text-muted border small">나의</span>
                  </div>
                  <div v-if="pf.user_id === authStore.user?.id || authStore.isAdmin">
                    <button type="button" class="btn btn-sm btn-outline-primary me-1" @click="loadPortfolio(pf)">수정</button>
                    <button type="button" class="btn btn-sm btn-outline-danger" @click="deletePf(pf)">삭제</button>
                  </div>
                </div>
                <p v-if="pf.description" class="mb-2 text-muted small text-truncate-2">{{ pf.description }}</p>
                <div class="d-flex justify-content-between align-items-center">
                  <router-link :to="`/portfolios/${pf.id}`" class="btn btn-sm btn-link p-0 text-decoration-none d-flex align-items-center gap-1">
                    <MaterialIcon name="visibility" size="1.1rem" />
                    상세 보기
                  </router-link>
                  <p v-if="!pf.items || pf.items.length === 0" class="mb-0 text-muted small italic">구성 종목 없음</p>
                  <p v-else class="mb-0 text-muted small">종목 수: {{ pf.items.length }}개</p>
                </div>
              </div>
              <div v-if="!loading && portfolios.length === 0" class="list-group-item text-center p-4">저장된 포트폴리오가 없습니다.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { portfolioApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  DoughnutController,
} from 'chart.js'

ChartJS.register(ArcElement, Tooltip, Legend, DoughnutController)

const CHART_COLORS = [
  'rgb(220, 53, 69)', 'rgb(13, 110, 253)', 'rgb(25, 135, 84)', 'rgb(255, 193, 7)',
  'rgb(13, 202, 240)', 'rgb(111, 66, 193)', 'rgb(253, 126, 20)', 'rgb(214, 51, 132)',
]

function getChartData(pf) {
  const items = (pf.items || []).filter((i) => i.ratio != null && i.ratio !== '')
  if (items.length === 0) {
    return { labels: ['없음'], datasets: [{ data: [100], backgroundColor: ['#dee2e6'] }] }
  }
  return {
    labels: items.map((i) => `${i.name} (${Number(i.ratio)}%)`),
    datasets: [{
      data: items.map((i) => Number(i.ratio)),
      backgroundColor: items.map((_, idx) => CHART_COLORS[idx % CHART_COLORS.length]),
      borderWidth: 0,
      borderColor: 'transparent',
    }],
  }
}

const chartOptions = {
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 2,
  plugins: {
    legend: {
      position: 'right',
      labels: { boxWidth: 12, font: { size: 11 }, color: '#8b9bb4' },
    },
    tooltip: {
      callbacks: {
        label: (ctx) => `${ctx.label}: ${ctx.parsed}%`,
      },
    },
  },
}

const emit = defineEmits(['flash'])
const portfolios = ref([])
const loading = ref(true)
const tickerQuery = ref('')
const searchResults = ref([])
const form = reactive({ id: null, name: '', description: '', items: [], is_public: false, level: 1 })
let portfoliosAbortController = null
let portfoliosReqId = 0
let tickerSearchAbortController = null
let tickerSearchReqId = 0

/** 비율 입력값 파싱 (빈칸·문자 → 0) */
function parseRatio(val) {
  const n = Number(val)
  return Number.isFinite(n) ? n : 0
}

const ratioSum = computed(() =>
  form.items.reduce((acc, i) => acc + parseRatio(i.ratio), 0)
)

/** 표시·검증 모두 소수 둘째 자리로 반올림해 부동소수점 오차 방지 */
const ratioSumRounded = computed(() => Math.round(ratioSum.value * 100) / 100)
const ratioSumDisplay = computed(() => ratioSumRounded.value.toFixed(2))

const isRatioSumValid = computed(() => {
  if (form.items.length === 0) return false
  return Math.abs(ratioSumRounded.value - 100) < 0.005
})

onMounted(async () => {
  portfoliosAbortController = new AbortController()
  const reqId = ++portfoliosReqId
  try {
    const { data } = await portfolioApi.getPortfolios({ signal: portfoliosAbortController.signal })
    if (reqId !== portfoliosReqId) return
    portfolios.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    emit('flash', getApiErrorMessage(e, '포트폴리오 목록을 불러오지 못했습니다.'), 'alert-danger')
  } finally {
    if (reqId !== portfoliosReqId) return
    loading.value = false
  }
})

async function searchTicker() {
  const q = tickerQuery.value.trim()
  if (!q) return
  if (tickerSearchAbortController) {
    tickerSearchAbortController.abort()
  }
  tickerSearchAbortController = new AbortController()
  const reqId = ++tickerSearchReqId
  try {
    const { data } = await portfolioApi.searchTicker(q, { signal: tickerSearchAbortController.signal })
    if (reqId !== tickerSearchReqId) return
    searchResults.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    emit('flash', getApiErrorMessage(e, '티커 검색 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

function addItem(item) {
  if (form.items.some((i) => i.ticker === item.ticker)) {
    emit('flash', '이미 추가된 종목입니다.', 'alert-warning')
    return
  }
  form.items.push({ ticker: item.ticker, name: item.name, ratio: '' })
  searchResults.value = []
  tickerQuery.value = ''
}

function loadPortfolio(pf) {
  form.id = pf.id
  form.name = pf.name
  form.description = pf.description || ''
  form.items = (pf.items || []).map((i) => ({ ...i }))
  form.is_public = !!pf.is_public
  form.level = pf.level || 1
}

function resetForm() {
  form.id = null
  form.name = ''
  form.description = ''
  form.items = []
  form.is_public = false
  form.level = 1
  searchResults.value = []
}

async function save() {
  if (!form.name.trim()) {
    emit('flash', '포트폴리오명은 필수입니다.', 'alert-warning')
    return
  }
  if (!isRatioSumValid.value) {
    emit('flash', '비율의 합이 100%가 되어야 저장할 수 있습니다.', 'alert-warning')
    return
  }
  const items = form.items.filter((i) => i.ticker && i.ratio !== '' && i.ratio != null).map((i) => ({ ticker: i.ticker, name: i.name || i.ticker, ratio: Number(i.ratio) }))
  try {
    await portfolioApi.savePortfolio({ 
      id: form.id, 
      name: form.name, 
      description: form.description, 
      items,
      is_public: form.is_public,
      level: form.level
    })
    emit('flash', `포트폴리오 "${form.name}"가 저장되었습니다.`, 'alert-success')
    const { data } = await portfolioApi.getPortfolios()
    portfolios.value = data
    resetForm()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '저장 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

async function deletePf(pf) {
  if (!confirm(`정말 "${pf.name}" 포트폴리오를 삭제하시겠습니까?`)) return
  try {
    await portfolioApi.deletePortfolio(pf.id)
    emit('flash', `포트폴리오 "${pf.name}"가 삭제되었습니다.`, 'alert-success')
    const { data } = await portfolioApi.getPortfolios()
    portfolios.value = data
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '삭제 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

onBeforeUnmount(() => {
  portfoliosAbortController?.abort()
  tickerSearchAbortController?.abort()
})
</script>

<style scoped>
.text-truncate-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
