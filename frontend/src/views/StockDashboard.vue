<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="d-flex align-items-center gap-2">
        <MaterialIcon name="show_chart" size="1.75rem" />
        전체 티커 정보
      </h1>
      <div class="d-flex gap-2">
        <button 
          v-if="isAdmin" 
          type="button" 
          class="btn btn-outline-dark d-inline-flex align-items-center gap-1" 
          @click="showAssetClassesModal = true"
        >
          <MaterialIcon name="category" size="1.125rem" />
          자산분류 설정
        </button>
        <button 
          v-if="isAdmin" 
          type="button" 
          class="btn btn-primary d-inline-flex align-items-center gap-1" 
          :disabled="crawling" 
          @click="doCrawl"
        >
          <MaterialIcon name="sync" size="1.125rem" />
          {{ crawling ? '크롤링 중...' : '전체 티커 동기화' }}
        </button>
      </div>
    </div>

    <!-- 검색 바 -->
    <div class="card mb-4">
      <div class="card-body">
        <form class="row g-3" @submit.prevent="search">
          <div class="col-md-10">
            <div class="input-group">
              <span class="input-group-text"><MaterialIcon name="search" size="1.125rem" /></span>
              <input 
                v-model="searchQuery" 
                type="text" 
                class="form-control" 
                placeholder="티커 번호 또는 종목명으로 검색..."
                @input="onSearchInput"
              >
            </div>
          </div>
          <div class="col-md-2">
            <button type="submit" class="btn btn-secondary w-100">검색</button>
          </div>
        </form>
      </div>
    </div>

    <PageLoadingPlaceholder v-if="loading && tickers.length === 0" variant="table" :rows="10" />

    <div v-else class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <span>주식 데이터 {{ searchQuery ? `(검색 결과: ${tickers.length}개)` : '(상위 100개)' }}</span>
        <span v-if="loading" class="spinner-border spinner-border-sm text-primary" role="status"></span>
      </div>
      <div class="card-body p-0">
        <div
          class="table-responsive"
          :class="{ 'virtual-scroll-table': isVirtualEnabled }"
          :style="isVirtualEnabled ? { maxHeight: `${containerHeight}px`, overflowY: 'auto' } : {}"
          @scroll="onVirtualScroll"
        >
          <table class="table table-hover mb-0">
            <thead class="table-light">
              <tr>
                 <th>Ticker</th>
                <th>종목명</th>
                <th>자산분류</th>
                <th>현재가</th>
                <th>시가총액</th>
                <th>거래량</th>
                <th v-if="isAdmin" class="text-end">관리</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="isVirtualEnabled && topSpacerHeight > 0" aria-hidden="true">
                <td :colspan="isAdmin ? 7 : 6" :style="{ height: `${topSpacerHeight}px`, padding: 0, border: 0 }"></td>
              </tr>
              <tr
                v-for="(stock, idx) in visibleTickers"
                :key="`${stock.ticker}-${isVirtualEnabled ? getRealIndex(idx) : idx}`"
                :style="isVirtualEnabled ? { height: `${rowHeight}px` } : {}"
              >
                <td><span class="badge bg-secondary font-monospace">{{ stock.ticker }}</span></td>
                <td>{{ stock.name }}</td>
                <td>
                  <span v-if="stock.asset_class" class="badge bg-primary-soft text-primary border border-primary-soft small">
                    {{ stock.asset_class }}
                  </span>
                  <span v-else class="text-muted small italic">-</span>
                </td>
                <td>{{ formatPrice(stock.current_price) }}</td>
                <td>{{ formatCap(stock.market_cap) }}</td>
                <td>{{ formatNumber(stock.volume) }}</td>
                <td v-if="isAdmin" class="text-end">
                  <button class="btn btn-sm btn-outline-primary" @click="editTicker(stock)">
                    <MaterialIcon name="edit" size="1rem" />
                  </button>
                </td>
              </tr>
              <tr v-if="isVirtualEnabled && bottomSpacerHeight > 0" aria-hidden="true">
                <td :colspan="isAdmin ? 7 : 6" :style="{ height: `${bottomSpacerHeight}px`, padding: 0, border: 0 }"></td>
              </tr>
              <tr v-if="!loading && tickers.length === 0">
                <td :colspan="isAdmin ? 7 : 6" class="text-center py-4 text-muted">데이터가 없습니다.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Edit Ticker Modal -->
    <div v-if="showEditModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
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
            <div v-if="editingTicker" class="row g-4">
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
                  <div class="form-text small">설정 > 포트폴리오 전략 관리에서 등록된 항목이 표시됩니다.</div>
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
                  <p class="small text-muted mb-3">티커에 사용자 정의 필드를 추가하거나 수정할 수 있습니다.</p>
                  <form @submit.prevent="saveField">
                    <div class="row g-2 mb-2">
                      <div class="col-5">
                        <input v-model="newField.name" type="text" class="form-control form-control-sm" placeholder="필드명 (예: note)">
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

    <!-- Asset Classes Management Modal -->
    <div v-if="showAssetClassesModal" class="modal fade show d-block" tabindex="-1" style="background: rgba(0,0,0,0.5)">
      <div class="modal-dialog">
        <div class="modal-content border-0 shadow-lg">
          <div class="modal-header bg-dark text-white">
            <h5 class="modal-title d-flex align-items-center gap-2">
              <MaterialIcon name="category" />
              전역 자산분류 설정
            </h5>
            <button type="button" class="btn-close btn-close-white" @click="showAssetClassesModal = false"></button>
          </div>
          <div class="modal-body p-4">
            <p class="text-muted small mb-4">티커별로 지정할 수 있는 공통 자산분류(예: 국내주식, 미국주식, 채권, 원자재 등)를 관리합니다.</p>
            
            <div class="d-flex flex-wrap gap-2 mb-4">
              <div v-for="(cls, idx) in assetClasses" :key="idx" class="badge bg-primary-soft text-primary border border-primary-soft p-2 d-flex align-items-center gap-2">
                <span class="fw-bold">{{ cls }}</span>
                <MaterialIcon name="cancel" size="1rem" class="cursor-pointer opacity-75 hover-opacity-100" @click="removeAssetClass(idx)" />
              </div>
              <div v-if="!assetClasses.length" class="text-muted small italic py-2">등록된 분류가 없습니다.</div>
            </div>

            <div class="mb-3">
              <label class="form-label small fw-bold text-muted">새 분류 추가</label>
              <div class="input-group input-group-sm">
                <input 
                  v-model="newAssetClass" 
                  type="text" 
                  class="form-control" 
                  placeholder="예: 국내주식"
                  @keypress.enter="addAssetClass"
                >
                <button class="btn btn-dark" type="button" @click="addAssetClass">추가</button>
              </div>
            </div>
          </div>
          <div class="modal-footer bg-light">
            <button type="button" class="btn btn-secondary btn-sm px-3" @click="showAssetClassesModal = false">닫기</button>
            <button type="button" class="btn btn-primary btn-sm px-4 fw-bold" :disabled="savingAssetClasses" @click="saveAssetClasses">
              <span v-if="savingAssetClasses" class="spinner-border spinner-border-sm me-1"></span>
              설정 저장
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { stockApi, portfolioApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { useVirtualRows } from '../composables/useVirtualRows'
import { getVirtualScrollOptions } from '../config/virtualScroll'
import { formatKstDateTime } from '../utils/dateTime'

const emit = defineEmits(['flash'])

const tickers = ref([])
const loading = ref(true)
const crawling = ref(false)
const searchQuery = ref('')
const assetClasses = ref([])
const isAdmin = computed(() => authStore.isAdmin)

const showEditModal = ref(false)
const showAssetClassesModal = ref(false)
const newAssetClass = ref('')
const savingAssetClasses = ref(false)
const editingTicker = ref(null)
const newField = reactive({ name: '', value: '' })

let searchTimeout = null
let tickerAbortController = null
let lastTickerRequestId = 0

const {
  rowHeight,
  containerHeight,
  isVirtualEnabled,
  visibleItems: visibleTickers,
  topSpacerHeight,
  bottomSpacerHeight,
  onVirtualScroll,
  getRealIndex,
} = useVirtualRows(tickers, getVirtualScrollOptions('stock', {
  rowHeight: 52,
  containerHeight: 560,
  threshold: 120,
}))

async function loadTickers() {
  if (tickerAbortController) {
    tickerAbortController.abort()
  }
  tickerAbortController = new AbortController()
  const requestId = ++lastTickerRequestId
  loading.value = true
  try {
    const p1 = stockApi.getTickers(searchQuery.value, { signal: tickerAbortController.signal })
    const p2 = portfolioApi.getAssetClasses()
    const [resT, resA] = await Promise.all([p1, p2])
    
    if (requestId !== lastTickerRequestId) return
    tickers.value = resT.data
    assetClasses.value = resA.data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    if (requestId !== lastTickerRequestId) return
    emit('flash', getApiErrorMessage(e, '데이터를 불러오는 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    if (requestId !== lastTickerRequestId) return
    loading.value = false
  }
}

function onSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadTickers()
  }, 300)
}

function search() {
  loadTickers()
}

async function doCrawl() {
  if (!confirm('전체 티커 동기화를 시작하시겠습니까? (수분 소요될 수 있음)')) return
  crawling.value = true
  try {
    const { data } = await stockApi.crawl()
    emit('flash', data.message, 'alert-success')
    loadTickers()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '크롤링 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    crawling.value = false
  }
}

function addAssetClass() {
  const val = newAssetClass.value.trim()
  if (!val) return
  if (assetClasses.value.includes(val)) {
    emit('flash', '이미 존재하는 분류입니다.', 'alert-warning')
    return
  }
  assetClasses.value.push(val)
  newAssetClass.value = ''
}

function removeAssetClass(idx) {
  assetClasses.value.splice(idx, 1)
}

async function saveAssetClasses() {
  savingAssetClasses.value = true
  try {
    await portfolioApi.updateAssetClasses(assetClasses.value)
    emit('flash', '자산 분류 설정이 저장되었습니다.', 'alert-success')
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '자산 분류 저장 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    savingAssetClasses.value = false
  }
}

async function editTicker(stock) {
  try {
    const { data } = await stockApi.getTickerDetail(stock.ticker)
    editingTicker.value = data
    showEditModal.value = true
    newField.name = ''
    newField.value = ''
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '상세 정보를 가져오지 못했습니다.'), 'alert-danger')
  }
}

function addEmptyField() {
  newField.name = ''
  newField.value = ''
}

async function saveField() {
  if (!newField.name) return
  try {
    const { data } = await stockApi.addField(editingTicker.value.ticker, newField.name, newField.value)
    emit('flash', data.message, 'alert-success')
    // Refresh detail
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

function closeModal() {
  showEditModal.value = false
  editingTicker.value = null
  loadTickers() // Refresh list in case something changed
}

function formatPrice(val) {
  if (!val) return '-'
  return '₩' + new Intl.NumberFormat('ko-KR').format(val)
}

function formatNumber(val) {
  if (!val) return '0'
  return new Intl.NumberFormat('ko-KR').format(val)
}

function formatCap(val) {
  if (!val) return '-'
  if (val >= 1000000000000) {
    return (val / 1000000000000).toFixed(2) + '조'
  }
  if (val >= 100000000) {
    return (val / 100000000).toFixed(0) + '억'
  }
  return '₩' + formatNumber(val)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return formatKstDateTime(dateStr)
}

onMounted(() => {
  loadTickers()
})

onBeforeUnmount(() => {
  if (tickerAbortController) {
    tickerAbortController.abort()
  }
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
})
</script>

<style scoped>
.modal.fade.show {
  display: block;
}
.cursor-pointer {
  cursor: pointer;
}
.action-panel {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 1rem;
}
pre {
  font-family: inherit;
  font-size: 0.8rem;
  white-space: pre-wrap;
}
</style>
