<template>
  <div>
    <div class="d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center gap-2 mb-4">
      <h1 class="mb-0 d-flex align-items-center gap-2">
        <MaterialIcon name="history" size="1.75rem" />
        자산 추이 상세 내역
      </h1>
      <div v-if="account" class="text-muted small">
        <span class="fw-bold text-dark">{{ account.account_name }}</span> ({{ account.account_number }})
      </div>
    </div>

    <!-- Filter Card -->
    <div class="card shadow-sm border-0 mb-4">
      <div class="card-body p-3">
        <div class="d-flex flex-column flex-md-row gap-3 align-items-md-center">
          <div class="btn-group btn-group-sm w-100-mobile">
            <button v-for="p in periods" :key="p.val" @click="setPeriod(p.val)" type="button" 
              :class="['btn flex-grow-1', periodPreset === p.val ? 'btn-primary' : 'btn-outline-secondary']">
              {{ p.label }}
            </button>
          </div>
          <div class="d-flex align-items-center gap-1 gap-sm-2 ms-md-auto w-100-mobile flex-nowrap">
            <input type="date" v-model="startDate" @change="periodPreset = 0" class="form-control form-control-sm flex-grow-1 shadow-none border-light-subtle" style="min-width: 0;">
            <span class="text-muted small flex-shrink-0">~</span>
            <input type="date" v-model="endDate" @change="periodPreset = 0" class="form-control form-control-sm flex-grow-1 shadow-none border-light-subtle" style="min-width: 0;">
            <button @click="loadHistory" type="button" class="btn btn-sm btn-primary px-2 px-sm-3 fw-bold d-flex align-items-center gap-1 shadow-sm flex-shrink-0 text-nowrap" :disabled="loading">
              <MaterialIcon v-if="!loading" name="search" size="1.05rem" />
              <span v-else class="spinner-border spinner-border-sm" role="status" aria-hidden="true" style="width: 0.8rem; height: 0.8rem;"></span>
              <span>조회</span>
            </button>
          </div>
          <div class="d-flex align-items-center gap-2 border-start ps-md-3">
             <div class="form-check form-switch mb-0">
                <input class="form-check-input" type="checkbox" id="rebalancedOnlySwitch" v-model="rebalancedOnly" @change="loadHistory">
                <label class="form-check-label small fw-bold text-nowrap" for="rebalancedOnlySwitch">리밸런싱만 보기</label>
             </div>
          </div>
        </div>
      </div>
    </div>

    <!-- History Table (Desktop) -->
    <div class="d-none d-lg-block card shadow-sm border-0 mb-4">
      <div class="card-body p-0">
        <div class="table-responsive">
          <table class="table table-hover align-middle mb-0">
            <thead class="table-light">
              <tr>
                <th style="width: 50px;"></th>
                <th>날짜</th>
                <th class="text-end">총 자산</th>
                <th class="text-end">전일대비</th>
                <th class="text-end text-muted small">원금</th>
                <th class="text-end">평가손익</th>
                <th class="text-center">수익률</th>
                <th style="width: 100px;"></th>
              </tr>
            </thead>
            <tbody>
              <template v-for="(h, idx) in visibleHistory" :key="h.date">
                <tr :class="{'expanded-row': expandedRows.includes(h.date)}" @click="toggleRow(h.date)" style="cursor: pointer;">
                  <td class="text-center">
                    <MaterialIcon :name="expandedRows.includes(h.date) ? 'expand_more' : 'chevron_right'" size="1.2rem" class="text-muted" />
                  </td>
                  <td class="fw-bold">
                    <div class="d-flex align-items-center gap-2">
                       {{ h.date }}
                      <span v-if="h.is_rebalanced" class="badge bg-info bg-opacity-10 text-info border border-info border-opacity-25 rounded-pill px-2 py-1" style="font-size: 0.65rem;">
                        리밸런싱
                      </span>
                    </div>
                  </td>
                  <td class="text-end fw-bold text-success">₩{{ Math.round(h.total_asset_value).toLocaleString() }}</td>
                  <td
                    class="text-end fw-semibold small"
                    :class="prevDayClass(h.prev_day_asset_change)"
                  >
                    {{ formatPrevDayChange(h.prev_day_asset_change) }}
                    <div v-if="h.prev_day_return_vs_principal_pct != null" class="small fw-normal text-muted">
                      ({{ formatPrevDayPct(h.prev_day_return_vs_principal_pct) }})
                    </div>
                  </td>
                  <td class="text-end text-muted small">₩{{ Math.round(h.principal).toLocaleString() }}</td>
                  <td class="text-end fw-bold" :class="h.investment_return > 0 ? 'text-danger' : h.investment_return < 0 ? 'text-primary' : ''">
                    {{ h.investment_return > 0 ? '+' : '' }}₩{{ Math.round(h.investment_return).toLocaleString() }}
                  </td>
                  <td class="text-center fw-bold" :class="h.return_rate > 0 ? 'text-danger' : h.return_rate < 0 ? 'text-primary' : ''">
                    {{ h.return_rate > 0 ? '+' : '' }}{{ h.return_rate.toFixed(2) }}%
                  </td>
                  <td class="text-center">
                    <div class="d-flex flex-column align-items-center gap-1 py-1">
                      <button type="button" class="btn btn-sm btn-link text-decoration-none p-0" @click.stop="toggleRow(h.date)">
                        {{ expandedRows.includes(h.date) ? '닫기' : '상세 내역' }}
                      </button>
                    </div>
                  </td>
                </tr>
                <!-- Expanded Drill-down Content (Desktop Table Version) -->
                <tr v-if="expandedRows.includes(h.date)">
                  <td colspan="8" class="p-0 bg-light border-start border-4 border-primary">
                    <div class="p-3">
                      <h6 class="fw-bold mb-3 d-flex align-items-center gap-2">
                        <MaterialIcon name="inventory_2" size="1rem" />
                        {{ h.date }} 보유 종목 상세
                      </h6>
                      <div v-if="h.holdings && h.holdings.length > 0" class="table-responsive rounded border bg-white">
                        <table class="table table-sm table-borderless align-middle mb-0">
                          <thead class="table-light small text-muted text-center border-bottom">
                            <tr>
                              <th class="text-start ps-3">종목명 (티커)</th>
                              <th>보유 수량</th>
                              <th>종가(기준가)</th>
                              <th class="text-end">평가금액</th>
                              <th class="text-end">당시 비중</th>
                              <th class="text-end">목표 비중</th>
                              <th class="text-end pe-3">차이</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="item in h.holdings" :key="item.ticker" class="border-bottom-subtle">
                              <td class="ps-3">
                                <span class="fw-bold">{{ item.name }}</span>
                                <small class="text-muted ms-1">({{ item.ticker }})</small>
                              </td>
                              <td class="text-center">{{ Number(item.quantity).toLocaleString() }}</td>
                              <td class="text-center text-muted">₩{{ Number(item.price).toLocaleString() }}</td>
                              <td class="text-end fw-bold text-dark">₩{{ Math.round(item.value).toLocaleString() }}</td>
                              <td class="text-end text-muted">{{ ((item.current_ratio || (item.value / h.total_asset_value)) * 100).toFixed(1) }}%</td>
                              <td class="text-end text-muted">{{ ((item.target_ratio || 0) * 100).toFixed(1) }}%</td>
                              <td class="text-end pe-3 fw-bold" :class="(item.current_ratio - item.target_ratio) > 0.0001 ? 'text-danger' : (item.current_ratio - item.target_ratio) < -0.0001 ? 'text-primary' : 'text-muted'">
                                {{ (item.current_ratio - item.target_ratio) > 0.0001 ? '+' : '' }}{{ ((item.current_ratio - item.target_ratio) * 100).toFixed(1) }}pp
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                      <div v-else class="text-muted small italic p-2 text-center border rounded bg-white">
                        기록된 보유 종목 정보가 없습니다.
                      </div>
                      <div class="mt-3 d-flex flex-wrap gap-2 align-items-center">
                        <button
                          type="button"
                          class="btn btn-sm btn-outline-secondary d-inline-flex align-items-center gap-1"
                          @click.stop="openRawJson(h.date)"
                        >
                          <MaterialIcon name="code" size="0.95rem" />
                          해당 일자 전체 필드 (JSON)
                        </button>
                      </div>
                    </div>
                  </td>
                </tr>
              </template>
            </tbody>
          </table>
          <div v-if="!loading && history.length === 0" class="text-center py-5 text-muted">
            <MaterialIcon name="search_off" size="2.5rem" class="mb-2 d-block mx-auto opacity-25" />
            해당 기간의 자산 추이 데이터가 없습니다.
          </div>
        </div>

        <!-- Load More Button (Desktop) -->
        <div v-if="history.length > visibleHistory.length" class="p-3 border-top text-center bg-light-subtle">
           <button type="button" class="btn btn-outline-primary btn-sm px-4 fw-bold shadow-sm" @click="currentPage++">
             <div class="d-flex align-items-center gap-2">
               <MaterialIcon name="expand_more" size="1.25rem" />
               내역 더 보기 ({{ visibleHistory.length }} / {{ history.length }})
             </div>
           </button>
        </div>
      </div>
    </div>

    <!-- History List (Mobile) -->
    <div class="d-lg-none d-flex flex-column gap-3 mb-4">
      <div v-for="h in visibleHistory" :key="h.date" class="card shadow-sm border-0 overflow-hidden" :class="{'border-start border-4 border-primary': expandedRows.includes(h.date)}">
        <div class="card-body p-3" @click="toggleRow(h.date)" style="cursor: pointer;">
          <div class="d-flex justify-content-between align-items-start mb-2">
            <div>
              <div class="d-flex align-items-center gap-2 mb-1">
                <div class="fw-bold h5 mb-0">{{ h.date }}</div>
                <span v-if="h.is_rebalanced" class="badge bg-info bg-opacity-10 text-info border border-info border-opacity-25 rounded-pill px-2 py-1" style="font-size: 0.6rem;">
                  리밸런싱
                </span>
              </div>
              <div class="text-muted small">수익률: 
                <span class="fw-bold" :class="h.return_rate > 0 ? 'text-danger' : h.return_rate < 0 ? 'text-primary' : ''">
                  {{ h.return_rate > 0 ? '+' : '' }}{{ h.return_rate.toFixed(2) }}%
                </span>
              </div>
            </div>
            <div class="text-end">
              <div class="fw-bold text-success h5 mb-0">₩{{ Math.round(h.total_asset_value).toLocaleString() }}</div>
              <div class="small fw-semibold" :class="prevDayClass(h.prev_day_asset_change)">
                전일대비 {{ formatPrevDayChange(h.prev_day_asset_change) }}
              </div>
              <div class="text-muted small" :class="h.investment_return > 0 ? 'text-danger' : h.investment_return < 0 ? 'text-primary' : ''">
                {{ h.investment_return > 0 ? '+' : '' }}₩{{ Math.round(h.investment_return).toLocaleString() }}
              </div>
            </div>
          </div>
          <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top">
            <span class="text-muted small">원금: ₩{{ Math.round(h.principal).toLocaleString() }}</span>
            <div class="d-flex flex-column align-items-end gap-1">
              <button type="button" class="btn btn-sm btn-outline-secondary py-1" @click.stop="toggleRow(h.date)">
                {{ expandedRows.includes(h.date) ? '닫기' : '상세 내역' }}
                <MaterialIcon :name="expandedRows.includes(h.date) ? 'expand_more' : 'chevron_right'" size="1rem" align="middle" />
              </button>
            </div>
          </div>
        </div>
        <!-- Expanded Content (Mobile List Version) -->
        <div v-if="expandedRows.includes(h.date)" class="bg-light border-top p-3">
          <h6 class="fw-bold mb-3 small d-flex align-items-center gap-2">
            <MaterialIcon name="inventory_2" size="0.9rem" />
            보유 종목 상세
          </h6>
          <div v-if="h.holdings && h.holdings.length > 0" class="d-flex flex-column gap-2">
            <div v-for="item in h.holdings" :key="item.ticker" class="bg-white p-2 rounded border-subtle shadow-xs">
              <div class="d-flex justify-content-between align-items-start">
                <div>
                  <div class="fw-bold small">{{ item.name }}</div>
                  <div class="text-muted tiny">{{ item.ticker }} · {{ Number(item.quantity).toLocaleString() }}주</div>
                </div>
                <div class="text-end">
                  <div class="fw-bold small">₩{{ Math.round(item.value).toLocaleString() }}</div>
                  <div class="tiny" :class="(item.current_ratio - item.target_ratio) > 0.0001 ? 'text-danger' : (item.current_ratio - item.target_ratio) < -0.0001 ? 'text-primary' : 'text-muted'">
                    {{ ((item.current_ratio || 0) * 100).toFixed(1) }}% 
                    <span class="text-muted">(계획 {{ ((item.target_ratio || 0) * 100).toFixed(1) }}%)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="text-muted small italic text-center">기록이 없습니다.</div>
          <div class="mt-3">
            <button type="button" class="btn btn-sm btn-outline-secondary w-100 d-inline-flex align-items-center justify-content-center gap-1" @click.stop="openRawJson(h.date)">
              <MaterialIcon name="code" size="0.9rem" />
              해당 일자 Raw JSON
            </button>
          </div>
        </div>
      </div>
      <div v-if="!loading && history.length === 0" class="text-center py-5 text-muted bg-white rounded shadow-sm">
        <MaterialIcon name="search_off" size="2.5rem" class="mb-2 d-block mx-auto opacity-25" />
        데이터가 없습니다.
      </div>

      <!-- Load More Button (Mobile) -->
      <div v-if="history.length > visibleHistory.length" class="mt-2">
         <button type="button" class="btn btn-outline-primary w-100 fw-bold shadow-sm d-flex align-items-center justify-content-center gap-2" @click="currentPage++">
             <MaterialIcon name="expand_more" size="1.25rem" />
             내역 더 보기 ({{ visibleHistory.length }} / {{ history.length }})
         </button>
      </div>
    </div>

    <!-- Loading Overlay -->
    <PageLoadingPlaceholder v-if="loading && history.length === 0" variant="table" :rows="10" />

    <!-- Raw JSON modal -->
    <Teleport to="body">
      <div
        v-if="rawModal.open"
        class="raw-json-modal-backdrop"
        role="dialog"
        aria-modal="true"
        :aria-label="`Raw JSON ${rawModal.date}`"
        @click.self="closeRawJson"
      >
        <div class="raw-json-modal-dialog card shadow-lg border-0">
          <div class="card-header d-flex align-items-center justify-content-between py-3">
            <h5 class="mb-0 d-flex align-items-center gap-2 small fw-bold">
              <MaterialIcon name="code" size="1.25rem" class="text-primary" />
              balance_history · {{ rawModal.date }}
            </h5>
            <button type="button" class="btn-close" aria-label="닫기" @click="closeRawJson"></button>
          </div>
          <div class="card-body pt-0">
            <p class="text-muted x-small mb-2">MongoDB에 저장된 해당 일자 문서(동일 날짜가 여러 건이면 <code>documents</code> 배열로 반환됩니다).</p>
            <div v-if="rawModal.loading" class="text-center py-5 text-muted">불러오는 중…</div>
            <div v-else-if="rawModal.error" class="alert alert-danger small mb-0">{{ rawModal.error }}</div>
            <template v-else>
              <div class="d-flex flex-wrap gap-2 mb-2">
                <button type="button" class="btn btn-sm btn-primary" @click="copyRawJson">클립보드에 복사</button>
              </div>
              <pre class="raw-json-pre mb-0">{{ rawModal.text }}</pre>
            </template>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { accountApi, getApiErrorMessage } from '../api'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import MaterialIcon from '../components/MaterialIcon.vue'

const route = useRoute()
const accountId = route.params.accountId

const account = ref(null)
const history = ref([])
const loading = ref(true)
const expandedRows = ref([])
const currentPage = ref(1)
const itemsPerPage = 50

const visibleHistory = computed(() => {
  return history.value.slice(0, currentPage.value * itemsPerPage)
})

const rawModal = ref({
  open: false,
  date: '',
  text: '',
  loading: false,
  error: '',
})

const startDate = ref('')
const endDate = ref('')
const periodPreset = ref(3) // 기본 3개월
const rebalancedOnly = ref(false)

const periods = [
  { label: '1개월', val: 1 },
  { label: '3개월', val: 3 },
  { label: '6개월', val: 6 },
  { label: '1년', val: 12 },
  { label: '전체', val: 0 },
]

onMounted(async () => {
  if (route.query.rebalanced_only === 'true') {
    rebalancedOnly.value = true
    periodPreset.value = 0 // "전체" 또는 기본 기간 대신 쿼리 무력화
  }
  setPeriod(rebalancedOnly.value ? 0 : 3)
  await fetchAccountInfo()
  await loadHistory()
})

function formatPrevDayChange(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return '—'
  const n = Math.round(Number(v))
  return `${n > 0 ? '+' : ''}₩${n.toLocaleString()}`
}

function formatPrevDayPct(pct) {
  if (pct === null || pct === undefined || Number.isNaN(Number(pct))) return ''
  const n = Number(pct)
  return `${n > 0 ? '+' : ''}${n.toFixed(2)}%`
}

function prevDayClass(v) {
  if (v === null || v === undefined || Number.isNaN(Number(v))) return 'text-muted'
  const n = Number(v)
  if (n > 0) return 'text-danger'
  if (n < 0) return 'text-primary'
  return 'text-muted'
}

async function fetchAccountInfo() {
  try {
    const { data } = await accountApi.getAccount(accountId)
    account.value = data
    // Update document title
    document.title = `${data.account_name} - 자산 추이 상세`
  } catch (e) {
    console.error('Account info load error:', e)
  }
}

function setPeriod(months) {
  periodPreset.value = months
  const now = new Date()
  endDate.value = now.toISOString().split('T')[0]
  
  if (months === 0) {
    startDate.value = ''
  } else {
    const start = new Date()
    start.setMonth(now.getMonth() - months)
    startDate.value = start.toISOString().split('T')[0]
  }
  
  if (onMounted && !loading.value) {
    loadHistory()
  }
}

async function loadHistory() {
  loading.value = true
  currentPage.value = 1
  try {
    const { data } = await accountApi.fetchBalanceHistory(accountId, startDate.value, endDate.value, rebalancedOnly.value)
    // 최신 날짜가 위로 오도록 역순 정렬
    history.value = [...data].reverse()
  } catch (e) {
    alert(getApiErrorMessage(e, '내역을 불러오지 못했습니다.'))
  } finally {
    loading.value = false
  }
}

function toggleRow(date) {
  const idx = expandedRows.value.indexOf(date)
  if (idx > -1) {
    expandedRows.value.splice(idx, 1)
  } else {
    expandedRows.value.push(date)
  }
}

function closeRawJson() {
  rawModal.value = { open: false, date: '', text: '', loading: false, error: '' }
}

async function openRawJson(dateStr) {
  rawModal.value = {
    open: true,
    date: dateStr,
    text: '',
    loading: true,
    error: '',
  }
  try {
    const { data } = await accountApi.fetchBalanceHistoryRaw(accountId, dateStr)
    rawModal.value = {
      ...rawModal.value,
      loading: false,
      text: JSON.stringify(data, null, 2),
      error: '',
    }
  } catch (e) {
    rawModal.value = {
      ...rawModal.value,
      loading: false,
      text: '',
      error: getApiErrorMessage(e, '원시 데이터를 불러오지 못했습니다.'),
    }
  }
}

async function copyRawJson() {
  const t = rawModal.value.text
  if (!t) return
  try {
    await navigator.clipboard.writeText(t)
    window.alert('JSON을 클립보드에 복사했습니다.')
  } catch {
    window.alert('복사에 실패했습니다. 브라우저 권한을 확인해 주세요.')
  }
}
</script>

<style scoped>
.expanded-row {
  background-color: var(--ui-surface-soft);
}
.border-bottom-subtle {
  border-bottom: 1px solid rgba(0,0,0,0.03);
}
[data-theme="dark"] .border-bottom-subtle {
  border-bottom: 1px solid rgba(255,255,255,0.03);
}

.tiny {
  font-size: 0.7rem;
}
.shadow-xs {
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}
.border-subtle {
  border: 1px solid rgba(0,0,0,0.05);
}
[data-theme="dark"] .border-subtle {
  border-color: rgba(255,255,255,0.05);
}

@media (max-width: 576px) {
  .w-100-mobile {
    width: 100% !important;
  }
}

.raw-json-btn {
  font-size: 0.7rem;
}

.x-small {
  font-size: 0.78rem;
}
</style>

<style>
/* Teleport to body — 전역 */
.raw-json-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1055;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.raw-json-modal-dialog {
  width: 100%;
  max-width: min(960px, 100vw - 2rem);
  max-height: min(90vh, 900px);
  display: flex;
  flex-direction: column;
}

.raw-json-modal-dialog .card-body {
  overflow: auto;
  flex: 1;
  min-height: 0;
}

.raw-json-pre {
  font-size: 0.72rem;
  line-height: 1.45;
  padding: 0.75rem;
  border-radius: 8px;
  background: var(--ui-surface-soft, #f1f5f9);
  color: var(--ui-text, #0f172a);
  border: 1px solid var(--ui-border, #e2e8f0);
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 60vh;
  overflow: auto;
}

[data-theme='dark'] .raw-json-pre {
  background: #0f172a;
  color: #e2e8f0;
  border-color: #334155;
}
</style>
