<template>
  <PageLoadingPlaceholder v-if="loading" variant="cards" :rows="4" />
  <div v-else-if="error" class="alert alert-danger m-4">
    <MaterialIcon name="error" size="1.5rem" class="me-2" />
    {{ error }}
    <div class="mt-3">
      <router-link to="/accounts" class="btn btn-outline-danger btn-sm">목록으로 돌아가기</router-link>
    </div>
  </div>
  <div v-else-if="account" class="container-fluid py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="d-flex align-items-center gap-2 mb-0">
        <MaterialIcon name="account_balance" size="2rem" class="text-primary" />
        계좌 상세 정보
      </h1>
      <div class="d-flex align-items-center gap-2">
        <template v-if="account.user_id === authStore.user?.id || authStore.isAdmin">
          <button class="btn btn-sm btn-outline-primary" @click="openEditAccountModal">
            <MaterialIcon name="edit" size="1rem" />
            수정
          </button>
          <button class="btn btn-sm btn-outline-danger" @click="deleteAccount">
            <MaterialIcon name="delete" size="1rem" />
            삭제
          </button>
        </template>
        <router-link to="/accounts" class="btn btn-sm btn-outline-secondary">
          <MaterialIcon name="arrow_back" size="1.2rem" />
          목록으로
        </router-link>
      </div>
    </div>

    <div class="row g-4">
      <div class="col-lg-7">
        <!-- 기본 정보 카드 -->
        <div class="card shadow-sm border-0 mb-4">
          <div class="card-header bg-white border-bottom-0 pt-4 px-4">
            <h5 class="card-title fw-bold mb-0 d-flex align-items-center gap-2">
              <MaterialIcon name="info" size="1.25rem" class="text-primary" />
              기본 정보
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="row g-3">
              <div class="col-sm-6">
                <label class="text-muted small d-block">계좌명</label>
                <div class="fw-bold fs-5">{{ account.account_name }}</div>
              </div>
              <div class="col-sm-6">
                <label class="text-muted small d-block">계좌번호</label>
                <div class="badge bg-light text-dark border fs-6">{{ account.account_number }}</div>
              </div>
              <div class="col-12">
                <label class="text-muted small d-block">표시 소유자</label>
                <div class="fw-bold">{{ account.owner }}</div>
              </div>
              <div class="col-12">
                <label class="text-muted small d-block">설명</label>
                <div class="text-secondary p-3 bg-light rounded" style="white-space: pre-wrap;">
                  {{ account.description || '설명이 없습니다.' }}
                </div>
              </div>
              <div class="col-12">
                <label class="text-muted small d-block mb-1">분류 태그</label>
                <div>
                  <span
                    v-for="tag in (account.tags || [])"
                    :key="`detail-tag-${tag}`"
                    class="badge rounded-pill text-bg-light border me-1"
                  >{{ tag }}</span>
                  <span v-if="!(account.tags || []).length" class="text-muted small">미분류</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 거래 내역 섹션 -->
        <div class="card shadow-sm border-0 mb-4">
          <div class="card-header bg-white border-bottom-0 pt-4 px-4 d-flex justify-content-between align-items-center">
            <h5 class="card-title fw-bold mb-0 d-flex align-items-center gap-2">
              <MaterialIcon name="history" size="1.25rem" class="text-primary" />
              최근 입출금 내역
            </h5>
            <button
              v-if="account.user_id === authStore.user?.id || authStore.isAdmin"
              class="btn btn-sm btn-primary d-flex align-items-center gap-1"
              @click="openAddModal"
            >
              <MaterialIcon name="add" size="1rem" />
              내역 추가
            </button>
          </div>
          <div class="card-body p-0">
            <!-- 데스크탑 테이블 뷰 -->
            <div class="table-responsive d-none d-md-block">
              <table class="table table-hover align-middle mb-0">
                <thead class="table-light">
                  <tr>
                    <th class="ps-4">날짜</th>
                    <th>구분</th>
                    <th class="text-end">금액</th>
                    <th>적요</th>
                    <th class="text-center pe-4">관리</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="tx in transactions" :key="tx.id">
                    <td class="ps-4">{{ tx.date }}</td>
                    <td>
                      <span :class="tx.type === 'deposit' ? 'text-primary' : 'text-danger'" class="fw-bold">
                        {{ tx.type === 'deposit' ? '입금' : '출금' }}
                      </span>
                      <small v-if="tx.type === 'withdraw'" class="text-muted ms-1">
                        ({{ tx.source === 'profit' ? '수익' : '원금' }})
                      </small>
                    </td>
                    <td class="text-end tabular-nums fw-bold">
                      <span :class="tx.type === 'deposit' ? 'text-primary' : 'text-danger'">
                        {{ tx.type === 'deposit' ? '+' : '-' }}
                      </span>
                      ₩{{ Number(tx.amount).toLocaleString() }}
                    </td>
                    <td class="text-truncate" style="max-width: 150px;">{{ tx.description || '-' }}</td>
                    <td class="text-center pe-4">
                      <div class="btn-group">
                        <button class="btn btn-sm btn-outline-secondary" @click="editTx(tx)">
                          <MaterialIcon name="edit" size="1.1rem" />
                        </button>
                        <button class="btn btn-sm btn-outline-danger" @click="delTx(tx.id)">
                          <MaterialIcon name="delete" size="1.1rem" />
                        </button>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="!txLoading && transactions.length === 0">
                    <td colspan="5" class="text-center py-5 text-muted">
                      거래 내역이 없습니다.
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 모바일 카드 뷰 -->
            <div class="d-md-none">
              <div v-if="transactions.length > 0" class="list-group list-group-flush">
                <div v-for="tx in transactions" :key="tx.id" class="list-group-item p-3">
                  <div class="d-flex justify-content-between align-items-start mb-2">
                    <div>
                      <div class="small text-muted mb-1">{{ tx.date }}</div>
                      <div class="fw-bold d-flex align-items-center gap-1">
                        <span :class="tx.type === 'deposit' ? 'text-primary' : 'text-danger'">
                          {{ tx.type === 'deposit' ? '입금' : '출금' }}
                        </span>
                        <small v-if="tx.type === 'withdraw'" class="text-muted">
                          ({{ tx.source === 'profit' ? '수익' : '원금' }})
                        </small>
                      </div>
                    </div>
                    <div class="text-end">
                      <div class="fw-bold fs-5 tabular-nums" :class="tx.type === 'deposit' ? 'text-primary' : 'text-danger'">
                        {{ tx.type === 'deposit' ? '+' : '-' }}₩{{ Number(tx.amount).toLocaleString() }}
                      </div>
                    </div>
                  </div>
                  <div class="d-flex justify-content-between align-items-center">
                    <div class="text-secondary small text-truncate pe-2">{{ tx.description || '-' }}</div>
                    <div class="btn-group">
                      <button class="btn btn-sm btn-outline-secondary py-1" @click="editTx(tx)">
                        <MaterialIcon name="edit" size="0.9rem" />
                      </button>
                      <button class="btn btn-sm btn-outline-danger py-1" @click="delTx(tx.id)">
                        <MaterialIcon name="delete" size="0.9rem" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else-if="!txLoading" class="p-5 text-center text-muted small">
                거래 내역이 없습니다.
              </div>
            </div>

            <!-- 더보기 버튼 -->
            <div v-if="hasMore" class="p-3 text-center border-top">
              <button class="btn btn-outline-primary btn-sm px-4" :disabled="txLoading" @click="loadMore">
                <span v-if="txLoading" class="spinner-border spinner-border-sm me-1"></span>
                {{ txLoading ? '불러오는 중...' : '더보기 (목록 확장)' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="col-lg-5">
        <!-- 권한 및 공유 정보 -->
        <div class="card shadow-sm border-0 mb-4">
          <div class="card-header bg-white border-bottom-0 pt-4 px-4">
            <h5 class="card-title fw-bold mb-0 d-flex align-items-center gap-2">
              <MaterialIcon name="security" size="1.25rem" class="text-primary" />
              권한 및 공유 설정
            </h5>
          </div>
          <div class="card-body px-4 pb-4">
            <div class="mb-4">
              <label class="text-muted small d-block mb-1">시스템 소유 계정</label>
              <div class="d-flex align-items-center gap-2">
                <div class="avatar-circle small">{{ (account.owner_username || 'U').charAt(0).toUpperCase() }}</div>
                <span class="fw-bold">{{ account.owner_username || '알 수 없음' }}</span>
                <span v-if="account.user_id === authStore.user?.id" class="badge bg-primary-subtle text-primary border border-primary-subtle ms-1">나 (Owner)</span>
              </div>
            </div>

            <div>
              <label class="text-muted small d-block mb-2">공유된 사용자 ({{ (account.shared_users_display || []).length }}명)</label>
              <div v-if="(account.shared_users_display || []).length" class="list-group list-group-flush border rounded overflow-hidden">
                <div v-for="u in account.shared_users_display" :key="u.id" class="list-group-item d-flex align-items-center gap-2 px-3">
                  <MaterialIcon name="person" size="1.1rem" class="text-muted" />
                  <span>{{ u.username || u.id }}</span>
                </div>
              </div>
              <p v-else class="text-muted small italic mb-0">공유 중인 사용자가 없습니다.</p>
            </div>
          </div>
        </div>

        <!-- 관련 계좌 잔고 링크 (Compact) -->
        <div class="card shadow-sm border-0 overflow-hidden">
          <div class="card-body p-4 d-flex align-items-center justify-content-between position-relative">
            <div style="z-index: 1;">
              <h6 class="fw-bold mb-1 d-flex align-items-center gap-2">
                <MaterialIcon name="account_balance_wallet" size="1.2rem" class="text-primary" />
                실시간 잔고 확인
              </h6>
              <p class="small text-muted mb-0">현재 보유 종목 및 수익률 확인</p>
            </div>
            <router-link :to="`/balances/${account.id}`" class="btn btn-primary d-flex align-items-center gap-1 shadow-sm px-3 py-2" style="z-index: 1;">
              <span class="fw-bold">이동</span>
              <MaterialIcon name="chevron_right" size="1.2rem" />
            </router-link>
            <MaterialIcon name="account_balance_wallet" size="6rem" class="position-absolute" style="right: -0.5rem; bottom: -1rem; opacity: 0.03; z-index: 0;" />
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 트랜잭션 추가/수정 모달 -->
  <div class="modal fade" id="txModal" tabindex="-1" aria-hidden="true" ref="txModalRef">
    <div class="modal-dialog">
      <div class="modal-content shadow-lg border-0 rounded-4">
        <div class="modal-header border-0 pb-2 pt-4 px-4">
          <h6 class="modal-title fw-bold text-dark mb-0">{{ editingTxId ? '내역 수정' : '입출금 내역 추가' }}</h6>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form @submit.prevent="saveTx">
          <div class="modal-body px-4 pb-2 pt-3">
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">날짜</label>
              <input v-model="txForm.date" type="date" class="form-control shadow-none" required>
            </div>
            <div class="row g-3 mb-3">
              <div class="col-6">
                <label class="form-label text-muted small mb-1">구분</label>
                <select v-model="txForm.type" class="form-select shadow-none" required @change="onTxTypeChange">
                  <option value="deposit">입금 (+)</option>
                  <option value="withdraw">출금 (-)</option>
                </select>
              </div>
              <div class="col-6">
                <label class="form-label text-muted small mb-1">금액</label>
                <div class="input-group">
                  <span class="input-group-text bg-light text-muted">₩</span>
                  <input v-model.number="txForm.amount" type="number" class="form-control shadow-none text-end" placeholder="0" required>
                </div>
              </div>
            </div>
            <div v-if="txForm.type === 'withdraw'" class="mb-3 p-3 bg-light rounded-3">
              <label class="form-label text-muted small d-block mb-2">출금 출처</label>
              <div class="d-flex gap-4">
                <div class="form-check mb-0">
                  <input v-model="txForm.source" class="form-check-input" type="radio" value="principal" id="srcPrincipal">
                  <label class="form-check-label small" for="srcPrincipal">원금</label>
                </div>
                <div class="form-check mb-0">
                  <input v-model="txForm.source" class="form-check-input" type="radio" value="profit" id="srcProfit">
                  <label class="form-check-label small" for="srcProfit">수익금</label>
                </div>
              </div>
              <p class="form-text mb-0 text-muted mt-2 pt-2 border-top" style="font-size: 0.78rem;">
                <MaterialIcon name="info" size="0.85rem" class="align-middle me-1" />
                수익금에서 출금 시 전체 투자 원금 합계가 변하지 않습니다.
              </p>
            </div>
            <div class="mb-0">
              <label class="form-label text-muted small mb-1">적요 (메모)</label>
              <input v-model="txForm.description" type="text" class="form-control shadow-none" placeholder="예: 3월 정기 납입">
            </div>
          </div>
          <div class="modal-footer border-0 px-4 pb-4 pt-3 d-flex gap-2">
            <button type="button" class="btn btn-outline-secondary flex-grow-1" data-bs-dismiss="modal">취소</button>
            <button type="submit" class="btn btn-primary flex-grow-1 fw-semibold" :disabled="savingTx">
              {{ savingTx ? '저장 중...' : '확인' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- 계좌 수정 모달 -->
  <div class="modal fade" id="editAccountModal" tabindex="-1" aria-hidden="true" ref="editAccountModalRef">
    <div class="modal-dialog">
      <div class="modal-content shadow-lg border-0 rounded-4">
        <div class="modal-header border-0 pb-2 pt-4 px-4">
          <h6 class="modal-title fw-bold mb-0">계좌 정보 수정</h6>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form @submit.prevent="saveEditAccount">
          <div class="modal-body px-4 pb-2 pt-3">
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">계좌명</label>
              <input v-model="editForm.account_name" type="text" class="form-control shadow-none" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">계좌번호</label>
              <input v-model="editForm.account_number" type="text" class="form-control shadow-none" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">표시 소유자명</label>
              <input v-model="editForm.owner" type="text" class="form-control shadow-none" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">설명</label>
              <textarea v-model="editForm.description" class="form-control shadow-none" rows="2"></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">분류 태그</label>
              <input
                v-model="editForm.tagsInput"
                type="text"
                class="form-control shadow-none"
                placeholder="예: 장기, ISA, 연금 (쉼표로 구분)"
              >
              <div class="small text-muted mt-1">쉼표(,)로 여러 태그를 입력하세요.</div>
            </div>
            <template v-if="authStore.isAdmin">
              <hr class="my-3">
              <div class="mb-3">
                <label class="form-label text-muted small mb-1">소유자 계정 변경</label>
                <select v-model="editForm.ownerUserId" class="form-select shadow-none">
                  <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.username }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label text-muted small d-block mb-1">공유 사용자</label>
                <div class="border rounded p-2 bg-light" style="max-height: 110px; overflow-y: auto;">
                  <div v-for="u in editShareCandidates" :key="u.id" class="form-check">
                    <input :id="'edit-share-' + u.id" v-model="editForm.sharedUserIds" class="form-check-input" type="checkbox" :value="u.id">
                    <label class="form-check-label small" :for="'edit-share-' + u.id">{{ u.username }}</label>
                  </div>
                  <p v-if="editShareCandidates.length === 0" class="text-muted small mb-0">다른 사용자가 없습니다.</p>
                </div>
              </div>
              <div class="form-check mb-0">
                <input id="edit-is-public" v-model="editForm.is_public" class="form-check-input" type="checkbox">
                <label class="form-check-label small" for="edit-is-public">Public Export (비로그인 포함 전체 조회 허용)</label>
              </div>
            </template>
          </div>
          <div class="modal-footer border-0 px-4 pb-4 pt-3 d-flex gap-2">
            <button type="button" class="btn btn-outline-secondary flex-grow-1" data-bs-dismiss="modal">취소</button>
            <button type="submit" class="btn btn-primary flex-grow-1 fw-semibold" :disabled="savingAccount">
              {{ savingAccount ? '저장 중...' : '저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Modal } from 'bootstrap'
import { accountApi, authApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { getKstTodayDateInput, toKstDateInput } from '../utils/dateTime'

const emit = defineEmits(['flash'])
const route = useRoute()
const router = useRouter()
const account = ref(null)
const loading = ref(true)
const error = ref('')
let accountAbortController = null
let accountReqId = 0

// -- Edit Account modal --
const editAccountModalRef = ref(null)
let editAccountBootstrapModal = null
const savingAccount = ref(false)
const allUsers = ref([])
const editForm = reactive({
  account_name: '',
  account_number: '',
  owner: '',
  description: '',
  ownerUserId: '',
  sharedUserIds: [],
  is_public: false,
  tagsInput: '',
})

const editShareCandidates = computed(() => {
  const oid = editForm.ownerUserId
  return allUsers.value.filter((u) => u.id !== oid)
})

// Transactions state
const transactions = ref([])
const txLoading = ref(false)
const txLimit = 10
const txOffset = ref(0)
const hasMore = ref(true)
const savingTx = ref(false)
const editingTxId = ref(null)
const txModalRef = ref(null)
let txBootstrapModal = null

const txForm = reactive({
  date: getKstTodayDateInput(),
  type: 'deposit',
  amount: 0,
  description: '',
  source: 'principal',
})

async function loadAccount() {
  const id = route.params.accountId
  accountAbortController = new AbortController()
  const reqId = ++accountReqId
  try {
    const { data } = await accountApi.getAccount(id, { signal: accountAbortController.signal })
    if (reqId !== accountReqId) return
    account.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    if (reqId !== accountReqId) return
    if (e.response?.status === 403) {
      error.value = '이 계좌의 상세 정보는 소유자 또는 관리자만 볼 수 있습니다.'
    } else {
      error.value = getApiErrorMessage(e, '계좌 정보를 불러오지 못했습니다.')
    }
  } finally {
    if (reqId === accountReqId) loading.value = false
  }
}

async function loadTransactions(isMore = false) {
  if (!isMore) {
    txOffset.value = 0
    transactions.value = []
    hasMore.value = true
  }
  
  txLoading.value = true
  try {
    const { data } = await accountApi.getTransactions(route.params.accountId, {
      limit: txLimit,
      offset: txOffset.value
    })
    
    if (data.length < txLimit) {
      hasMore.value = false
    }
    
    if (isMore) {
      transactions.value = [...transactions.value, ...data]
    } else {
      transactions.value = data
    }
    
    txOffset.value += data.length
  } catch (e) {
    console.error('Failed to load transactions:', e)
  } finally {
    txLoading.value = false
  }
}

function loadMore() {
  loadTransactions(true)
}

function openAddModal() {
  editingTxId.value = null
  txForm.date = getKstTodayDateInput()
  txForm.type = 'deposit'
  txForm.amount = 0
  txForm.description = ''
  txForm.source = 'principal'
  
  if (!txBootstrapModal) {
    initTxModal()
  }
  
  if (txBootstrapModal) {
    txBootstrapModal.show()
  } else {
    alert('모달 시스템 초기화에 실패했습니다. 페이지를 새로고침 해주세요.')
  }
}

function editTx(tx) {
  editingTxId.value = tx.id
  txForm.date = toKstDateInput(tx.date) || (tx.date || '').slice(0, 10)
  txForm.type = tx.type
  txForm.amount = tx.amount
  txForm.description = tx.description || ''
  txForm.source = tx.source || 'principal'
  
  if (!txBootstrapModal) {
    initTxModal()
  }
  
  if (txBootstrapModal) {
    txBootstrapModal.show()
  } else {
    alert('모달 시스템 초기화에 실패했습니다. 페이지를 새로고침 해주세요.')
  }
}

function initTxModal() {
  if (txModalRef.value) {
    try {
      txBootstrapModal = new Modal(txModalRef.value)
      console.log('Transaction modal initialized successfully.')
    } catch (e) {
      console.error('Failed to initialize transaction modal:', e)
    }
  }
}

async function saveTx() {
  savingTx.value = true
  try {
    const payload = {
      account_id: route.params.accountId,
      date: txForm.date,
      type: txForm.type,
      amount: txForm.amount,
      description: txForm.description,
      source: txForm.source,
    }
    if (editingTxId.value) {
      payload.transaction_id = editingTxId.value
    }
    await accountApi.saveTransaction(payload)
    if (txBootstrapModal) {
      txBootstrapModal.hide()
    }
    await loadTransactions() // Refresh list
  } catch (e) {
    alert(getApiErrorMessage(e, '내역 저장 중 오류가 발생했습니다.'))
  } finally {
    savingTx.value = false
  }
}

async function delTx(id) {
  if (!confirm('거래 내역을 삭제하시겠습니까?')) return
  try {
    await accountApi.deleteTransaction(id)
    await loadTransactions()
  } catch (e) {
    alert(getApiErrorMessage(e, '삭제 중 오류가 발생했습니다.'))
  }
}

function onTxTypeChange() {
  if (txForm.type === 'deposit') {
    txForm.source = 'principal'
  }
}

function openEditAccountModal() {
  if (!account.value) return
  editForm.account_name = account.value.account_name || ''
  editForm.account_number = account.value.account_number || ''
  editForm.owner = account.value.owner || ''
  editForm.description = account.value.description || ''
  editForm.ownerUserId = account.value.user_id || ''
  editForm.sharedUserIds = [...(account.value.shared_user_ids || [])]
  editForm.is_public = Boolean(account.value.is_public)
  editForm.tagsInput = (account.value.tags || []).join(', ')
  if (!editAccountBootstrapModal && editAccountModalRef.value) {
    editAccountBootstrapModal = new Modal(editAccountModalRef.value)
  }
  editAccountBootstrapModal?.show()
}

async function saveEditAccount() {
  savingAccount.value = true
  try {
    const payload = {
      id: account.value.id,
      account_name: editForm.account_name,
      account_number: editForm.account_number,
      owner: editForm.owner,
      description: editForm.description,
      tags: editForm.tagsInput.split(',').map(v => v.trim()).filter(Boolean),
    }
    if (authStore.isAdmin) {
      payload.user_id = editForm.ownerUserId
      payload.shared_user_ids = [...editForm.sharedUserIds]
      payload.is_public = Boolean(editForm.is_public)
    }
    await accountApi.updateAccount(payload)
    editAccountBootstrapModal?.hide()
    await loadAccount()
    emit('flash', '계좌 정보가 수정되었습니다.', 'alert-success')
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '수정 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    savingAccount.value = false
  }
}

async function deleteAccount() {
  if (!confirm(`[${account.value.account_name}] 계좌를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없으며, 관련된 거래 내역도 함께 삭제됩니다.`)) return
  try {
    await accountApi.deleteAccount(account.value.id)
    emit('flash', '계좌가 삭제되었습니다.', 'alert-success')
    router.push('/accounts')
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '삭제 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

function goToAccountManagerEdit() {
  router.push({ path: '/accounts', query: { editId: account.value.id } })
}

onMounted(async () => {
  // Load user list for admin sharing UI
  if (authStore.isAdmin) {
    try {
      const { data } = await authApi.getUsers()
      allUsers.value = data
    } catch (e) {
      console.error('Failed to load users:', e)
    }
  }
  await loadAccount()
  if (account.value) {
    loadTransactions()
  }
  initTxModal()
  if (editAccountModalRef.value) {
    editAccountBootstrapModal = new Modal(editAccountModalRef.value)
  }
})

onBeforeUnmount(() => {
  accountAbortController?.abort()
  if (txBootstrapModal) {
    txBootstrapModal.dispose()
  }
  editAccountBootstrapModal?.dispose()
})
</script>

<style scoped>
.italic { font-style: italic; }
.avatar-circle {
  width: 24px;
  height: 24px;
  background-color: var(--ui-surface-soft);
  border: 1px solid var(--ui-border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.75rem;
  color: var(--ui-text-muted);
}

.x-small {
  font-size: 0.75rem;
}

.table > thead > tr > th {
  font-weight: 600;
  font-size: 0.85rem;
  color: var(--ui-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.modal-content {
  border: none;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  border-radius: 20px;
}

.modal-header .btn-close {
  background-size: 0.8rem;
}

.input-group-text {
  background-color: var(--ui-bg);
  border-right: none;
  color: var(--ui-text-muted);
}

.input-group .form-control {
  border-left: none;
}

.input-group .form-control:focus {
  border-left-color: var(--ui-primary);
}
</style>
