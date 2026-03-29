<template>
  <PageLoadingPlaceholder v-if="loading" variant="cards" :rows="4" />
  <div v-else-if="error" class="alert alert-danger">
    {{ error }}
    <div class="mt-3">
      <router-link to="/portfolios" class="btn btn-outline-danger btn-sm">목록으로 돌아가기</router-link>
    </div>
  </div>
  <div v-else>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="d-flex align-items-center gap-2 mb-0">
        <MaterialIcon name="pie_chart" size="2rem" />
        {{ portfolio.name }}
        <span v-if="portfolio.is_public" class="badge bg-primary-soft text-primary border border-primary-soft ms-2 fs-6">공용</span>
        <span v-else class="badge bg-light text-muted border ms-2 fs-6">나의</span>
      </h1>
      <router-link to="/portfolios" class="btn btn-outline-secondary">
        <MaterialIcon name="arrow_back" size="1.2rem" />
        목록으로
      </router-link>
    </div>

    <div class="row g-4">
      <div class="col-lg-8">
        <div class="card mb-4 shadow-sm border-0">
          <div class="card-body">
            <h5 class="card-title fw-bold mb-3 d-flex align-items-center gap-2">
              <MaterialIcon name="description" size="1.25rem" class="text-primary" />
              전략 설명
            </h5>
            <p v-if="portfolio.description" class="card-text text-secondary" style="white-space: pre-wrap;">
              {{ portfolio.description }}
            </p>
            <p v-else class="text-muted italic mb-0">설명이 없습니다.</p>
          </div>
        </div>

        <div class="card shadow-sm border-0">
          <div class="card-header border-bottom-0 pt-4 px-4 bg-transparent">
            <h5 class="card-title fw-bold mb-0 d-flex align-items-center gap-2">
              <MaterialIcon name="list" size="1.25rem" class="text-primary" />
              구성 종목 및 비율
            </h5>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover align-middle mb-0">
                <thead>
                  <tr>
                    <th class="ps-4">종목명</th>
                    <th>티커</th>
                    <th>자산분류</th>
                    <th class="text-end" :class="authStore.isAdmin ? 'pe-2' : 'pe-4'">비율 (%)</th>
                    <th v-if="authStore.isAdmin" class="text-end pe-4">관리</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in portfolio.items" :key="item.ticker">
                    <td class="ps-4 fw-bold">
                      <a 
                        :href="`https://finance.naver.com/item/main.naver?code=${item.ticker}`" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        class="text-primary text-decoration-none d-inline-flex align-items-center gap-1 stock-link"
                      >
                        {{ item.name }}
                        <MaterialIcon name="open_in_new" size="1rem" class="link-icon" />
                      </a>
                    </td>
                    <td><code>{{ item.ticker }}</code></td>
                    <td>
                      <span v-if="item.asset_class" class="badge bg-primary-soft text-primary border border-primary-soft small">
                        {{ item.asset_class }}
                      </span>
                      <span v-else class="text-muted small italic">-</span>
                    </td>
                    <td class="text-end" :class="authStore.isAdmin ? 'pe-2' : 'pe-4'">
                      <div class="d-inline-block px-3 py-1 rounded-pill portfolio-badge fw-bold">
                        {{ item.ratio }}%
                      </div>
                    </td>
                    <td v-if="authStore.isAdmin" class="text-end pe-4">
                      <button class="btn btn-sm btn-outline-primary" @click="editTicker(item)">
                        <MaterialIcon name="edit" size="1rem" />
                      </button>
                    </td>
                  </tr>
                </tbody>
                <tfoot class="fw-bold" style="background-color: var(--ui-surface-soft);">
                  <tr>
                    <td :colspan="authStore.isAdmin ? 4 : 3" class="ps-4">합계</td>
                    <td class="text-end pe-4">100.00%</td>
                    <td v-if="authStore.isAdmin"></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-4">
        <div class="card shadow-sm border-0 sticky-top" style="top: 2rem; z-index: 10;">
          <div class="card-body text-center p-4">
            <h5 class="card-title fw-bold mb-4">자산분류별 비중</h5>
            <div class="chart-container" style="position: relative; min-height: 400px;">
              <Doughnut :data="chartData" :options="chartOptions" :plugins="[ChartDataLabels, centerTextPlugin]" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Ticker Modal (Admin) -->
    <div v-if="showEditModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5); z-index: 1060;">
      <div class="modal-dialog modal-lg">
        <div class="modal-content border-0 shadow-lg">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title d-flex align-items-center gap-2">
              <MaterialIcon name="edit" />
              티커 상세 정보 및 수정
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="closeModal"></button>
          </div>
          <div class="modal-body p-4">
            <div v-if="editingTicker" class="row g-4 text-start">
              <div class="col-md-6">
                <h6 class="text-muted mb-3">기본 정보</h6>
                <div class="mb-3">
                  <label class="form-label text-muted small uppercase fw-bold">Ticker</label>
                  <input :value="editingTicker.ticker" type="text" class="form-control" disabled>
                </div>
                <div class="mb-3">
                  <label class="form-label text-muted small uppercase fw-bold">종목명</label>
                  <input v-model="editingTicker.name" type="text" class="form-control mb-1">
                  <button type="button" class="btn btn-sm btn-outline-primary w-100 mt-1" @click="saveFieldName">종목명 저장</button>
                </div>
                <div class="mb-3">
                  <label class="form-label text-muted small uppercase fw-bold">자산 분류</label>
                  <select v-model="editingTicker.asset_class" class="form-select shadow-none" @change="saveAssetClass">
                    <option :value="undefined">소속 없음</option>
                    <option v-for="cls in assetClasses" :key="cls" :value="cls">{{ cls }}</option>
                  </select>
                </div>
                <div class="mb-3">
                  <label class="form-label text-muted small uppercase fw-bold">마지막 업데이트</label>
                  <div class="form-control-plaintext">{{ formatDate(editingTicker.last_updated) }}</div>
                </div>
              </div>
              <div class="col-md-6 border-start">
                <h6 class="text-muted d-flex align-items-center justify-content-between mb-3">
                  커스텀 필드 추가
                  <MaterialIcon name="add_circle" class="text-success cursor-pointer" @click="addEmptyField" />
                </h6>
                <div class="mb-3">
                  <form @submit.prevent="saveField">
                    <div class="row g-2 mb-2">
                      <div class="col-5">
                        <input v-model="newField.name" type="text" class="form-control form-control-sm" placeholder="필드명">
                      </div>
                      <div class="col-5">
                        <input v-model="newField.value" type="text" class="form-control form-control-sm" placeholder="값">
                      </div>
                      <div class="col-2">
                        <button type="submit" class="btn btn-sm btn-success w-100" :disabled="!newField.name">저장</button>
                      </div>
                    </div>
                  </form>
                </div>
                <div class="mt-4">
                  <h6 class="text-muted small uppercase fw-bold mb-2">현재 데이터 (Raw)</h6>
                  <pre class="bg-light p-2 rounded small overflow-auto" style="max-height: 200px">{{ editingTicker }}</pre>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer bg-light">
            <button type="button" class="btn btn-secondary px-4" @click="closeModal">닫기</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { portfolioApi, stockApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { formatKstDateTime } from '../utils/dateTime'
import { Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  DoughnutController,
} from 'chart.js'
import ChartDataLabels from 'chartjs-plugin-datalabels'

ChartJS.register(ArcElement, Tooltip, Legend, DoughnutController)

const route = useRoute()
const portfolio = ref(null)
const loading = ref(true)
const error = ref('')
const emit = defineEmits(['flash'])

const assetClasses = ref([])
const showEditModal = ref(false)
const editingTicker = ref(null)
const newField = reactive({ name: '', value: '' })

let portfolioAbortController = null
let portfolioReqId = 0

const CHART_COLORS = [
  '#6366f1', '#8b5cf6', '#06b6d4', '#10b981',
  '#f59e0b', '#ec4899', '#3b82f6', '#14b8a6',
  '#a855f7', '#64748b',
]

// Custom plugin to draw text in the center
const centerTextPlugin = {
  id: 'centerText',
  beforeDraw(chart) {
    if (!chart.chartArea) return
    const { ctx, chartArea: { width, height, top } } = chart
    ctx.save()
    const centerX = width / 2
    const centerY = top + (height / 2)
    
    ctx.font = 'bold 12px "JetBrains Mono", "IBM Plex Mono", monospace'
    ctx.fillStyle = '#8b9bb4'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('ASSET MIX', centerX, centerY)
    ctx.restore()
  }
}

const chartData = computed(() => {
  if (!portfolio.value || !portfolio.value.items) return null
  const items = portfolio.value.items
  
  const groups = {}
  items.forEach(i => {
    const key = i.asset_class || '미분류'
    groups[key] = (groups[key] || 0) + (Number(i.ratio) || 0)
  })
  
  const sortedLabels = Object.keys(groups).sort((a, b) => groups[b] - groups[a])
  
  return {
    labels: sortedLabels, // Just labels, percentage will be handled by datalabels plugin
    datasets: [{
      data: sortedLabels.map(label => groups[label]),
      backgroundColor: sortedLabels.map((_, idx) => CHART_COLORS[idx % CHART_COLORS.length]),
      borderWidth: 2,
      borderColor: 'white'
    }]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 20,
        boxWidth: 10,
        usePointStyle: true,
        font: { size: 10 },
        color: '#8b9bb4'
      }
    },
    datalabels: {
      color: '#ffffff',
      anchor: 'center',
      align: 'center',
      font: { 
        weight: '700', 
        size: 11,
        family: 'Inter, sans-serif'
      },
      formatter: (value, ctx) => {
        if (value < 4) return null // 조금 더 낮은 문턱값으로 더 많이 표시
        const label = ctx.chart.data.labels[ctx.dataIndex]
        return `${label}\n${value.toFixed(1)}%`
      },
      textAlign: 'center',
      textStrokeColor: 'rgba(0,0,0,0.7)', // 그림자보다 가독성이 좋은 테두리 적용
      textStrokeWidth: 2,
    },
    tooltip: {
      callbacks: {
        label: (ctx) => `${ctx.label}: ${ctx.parsed}%`
      }
    }
  },
  cutout: '65%', // Thinner doughnut to make room for center text
}

onMounted(async () => {
  const id = route.params.portfolioId
  portfolioAbortController = new AbortController()
  const reqId = ++portfolioReqId
  try {
    const p1 = portfolioApi.getPortfolio(id, { signal: portfolioAbortController.signal })
    const p2 = authStore.isAdmin ? portfolioApi.getAssetClasses() : Promise.resolve({ data: [] })
    
    const [resP, resA] = await Promise.all([p1, p2])
    
    if (reqId !== portfolioReqId) return
    portfolio.value = resP.data
    assetClasses.value = resA.data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    if (reqId !== portfolioReqId) return
    error.value = getApiErrorMessage(e, '포트폴리오 정보를 불러오지 못했습니다.')
  } finally {
    if (reqId !== portfolioReqId) return
    loading.value = false
  }
})

async function editTicker(item) {
  try {
    const { data } = await stockApi.getTickerDetail(item.ticker)
    editingTicker.value = data
    showEditModal.value = true
    newField.name = ''
    newField.value = ''
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '상세 정보를 가져오지 못했습니다.'), 'alert-danger')
  }
}

async function saveField() {
  if (!newField.name) return
  try {
    const { data } = await stockApi.addField(editingTicker.value.ticker, newField.name, newField.value)
    emit('flash', data.message, 'alert-success')
    const res = await stockApi.getTickerDetail(editingTicker.value.ticker)
    editingTicker.value = res.data
    newField.name = ''
    newField.value = ''
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '필드 저장 중 오류 발생'), 'alert-danger')
  }
}

async function saveFieldName() {
  try {
    await stockApi.addField(editingTicker.value.ticker, 'name', editingTicker.value.name)
    emit('flash', '종목명이 저장되었습니다.', 'alert-success')
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '종목명 저장 실패'), 'alert-danger')
  }
}

async function saveAssetClass() {
  try {
    await stockApi.updateAssetClass(editingTicker.value.ticker, editingTicker.value.asset_class)
    emit('flash', '자산 분류가 저장되었습니다.', 'alert-success')
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '자산 분류 저장 실패'), 'alert-danger')
  }
}

function addEmptyField() {
  newField.name = ''
  newField.value = ''
}

function closeModal() {
  showEditModal.value = false
  editingTicker.value = null
  // Refresh detail page to reflect changes
  const id = route.params.portfolioId
  portfolioApi.getPortfolio(id).then(res => {
    portfolio.value = res.data
  })
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return formatKstDateTime(dateStr)
}

onBeforeUnmount(() => {
  portfolioAbortController?.abort()
})
</script>

<style scoped>
.chart-container {
  max-width: 100%;
}
.stock-link {
  transition: all 0.2s ease;
}
.stock-link:hover {
  text-decoration: underline !important;
  opacity: 0.8;
}
.link-icon {
  opacity: 0;
  transition: opacity 0.2s ease;
}
.stock-link:hover .link-icon {
  opacity: 1;
}
</style>
