<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="d-flex align-items-center gap-2">
        <MaterialIcon name="payments" size="1.75rem" />
        입출금 내역 관리
      </h1>
      <router-link class="btn btn-outline-secondary d-inline-flex align-items-center gap-1" :to="selectedAccount ? `/balances/${selectedAccount}` : '/balances'">
        <MaterialIcon name="account_balance_wallet" size="1rem" />
        {{ selectedAccount ? '해당 계좌 잔고로 돌아가기' : '계좌 잔고 목록으로 돌아가기' }} &raquo;
      </router-link>
    </div>
    <PageLoadingPlaceholder v-if="accountLoading" variant="lines" :rows="5" class="mb-4" />

    <div v-else class="card mb-4">
      <div class="card-body">
        <div class="row align-items-center">
          <div class="col-auto">
            <label for="accountSelect" class="col-form-label fw-bold">계좌 선택:</label>
          </div>
          <div class="col-md-6">
            <select id="accountSelect" v-model="selectedAccount" class="form-select" @change="loadTransactions">
              <option value="" disabled>계좌를 선택하세요</option>
              <option v-for="acc in filteredAccounts" :key="acc.id" :value="acc.id">
                {{ acc.account_name }} ({{ acc.account_number }}) - {{ acc.owner }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <div v-if="permissionError" class="alert alert-danger mb-4">
      <MaterialIcon name="error" size="1.25rem" class="me-2 align-middle" />
      {{ permissionError }}
    </div>

    <template v-else-if="selectedAccount">
      <div class="row">
        <div class="col-md-4">
          <div class="action-panel">
            <h4>{{ editingId ? '내역 수정' : '내역 추가' }}</h4>
            <form @submit.prevent="save">
              <input type="hidden" v-model="form.account_id">
              <div class="mb-3">
                <label class="form-label">날짜</label>
                <input v-model="form.date" type="date" class="form-control" required>
              </div>
              <div class="mb-3">
                <label class="form-label">구분</label>
                <select v-model="form.type" class="form-select" required @change="onTypeChange">
                  <option value="deposit">입금</option>
                  <option value="withdraw">출금</option>
                </select>
              </div>
              <div v-if="form.type === 'withdraw'" class="mb-3">
                <label class="form-label">출금 출처</label>
                <div class="d-flex gap-3">
                  <div class="form-check">
                    <input v-model="form.source" class="form-check-input" type="radio" name="source" id="sourcePrincipal" value="principal">
                    <label class="form-check-label" for="sourcePrincipal">원금</label>
                  </div>
                  <div class="form-check">
                    <input v-model="form.source" class="form-check-input" type="radio" name="source" id="sourceProfit" value="profit">
                    <label class="form-check-label" for="sourceProfit">수익금</label>
                  </div>
                </div>
                <div class="form-text">수익금에서 출금 시 원금 합계에 영향을 주지 않습니다.</div>
              </div>
              <div class="mb-3">
                <label class="form-label">금액</label>
                <input v-model.number="form.amount" type="number" class="form-control" placeholder="0" required>
              </div>
              <div class="mb-3">
                <label class="form-label">적요 (내용)</label>
                <input v-model="form.description" type="text" class="form-control" placeholder="내용 입력">
              </div>
              <div class="d-grid gap-2">
                <button type="submit" class="btn btn-primary">저장</button>
                <button type="button" class="btn btn-secondary" @click="resetForm">초기화</button>
              </div>
            </form>
          </div>
        </div>
        <div class="col-md-8">
          <div class="card">
            <div class="card-header">거래 히스토리</div>
            <div class="card-body">
              <table class="table table-hover">
                <thead>
                  <tr>
                    <th>날짜</th>
                    <th>구분</th>
                    <th>금액</th>
                    <th>적요</th>
                    <th>관리</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="tx in transactions" :key="tx.id">
                    <td>{{ tx.date }}</td>
                    <td>
                      <span :class="tx.type === 'deposit' ? 'text-primary fw-bold' : 'text-danger fw-bold'">
                        {{ tx.type === 'deposit' ? '입금' : '출금' }}
                      </span>
                      <small v-if="tx.type === 'withdraw'" class="text-muted ms-1">
                        ({{ tx.source === 'profit' ? '수익' : '원금' }})
                      </small>
                    </td>
                    <td class="num-cell">₩{{ Number(tx.amount).toLocaleString() }}</td>
                    <td>{{ tx.description }}</td>
                    <td>
                      <button type="button" class="btn btn-sm btn-outline-primary me-1" @click="editTx(tx)">수정</button>
                      <button type="button" class="btn btn-sm btn-outline-danger" @click="delTx(tx.id)">삭제</button>
                    </td>
                  </tr>
                  <tr v-if="!txLoading && transactions.length === 0">
                    <td colspan="5" class="text-center">거래 내역이 없습니다.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute } from 'vue-router'
import { accountApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { getKstTodayDateInput, toKstDateInput } from '../utils/dateTime'

const route = useRoute()
const emit = defineEmits(['flash'])
const accounts = ref([])
const transactions = ref([])
const selectedAccount = ref('')
const accountLoading = ref(true)
const txLoading = ref(false)
const editingId = ref(null)
const permissionError = ref('')
let accountsAbortController = null
let accountsReqId = 0
let txAbortController = null
let txReqId = 0
const form = reactive({
  account_id: '',
  transaction_id: '',
  date: getKstTodayDateInput(),
  type: 'deposit',
  amount: 0,
  description: '',
  source: 'principal',
})

watch(selectedAccount, (v) => { form.account_id = v || '' })

const filteredAccounts = computed(() => {
  if (authStore.isAdmin) return accounts.value
  const me = authStore.user?.id
  return accounts.value.filter(a => a.user_id === me)
})

onMounted(async () => {
  accountsAbortController = new AbortController()
  const reqId = ++accountsReqId
  try {
    const { data } = await accountApi.getAccounts({ signal: accountsAbortController.signal })
    if (reqId !== accountsReqId) return
    accounts.value = data
  
    if (route.query.account_id) {
      const accId = route.query.account_id
      // Check if user has permission for this specific account
      const acc = accounts.value.find(a => a.id === accId)
      if (acc) {
        const isOwner = authStore.isAdmin || acc.user_id === authStore.user?.id
        if (isOwner) {
          selectedAccount.value = accId
          loadTransactions()
        } else {
          permissionError.value = '이 계좌의 거래 내역을 볼 권한이 없습니다. 소유자만 접근 가능합니다.'
        }
      } else {
        permissionError.value = '계좌를 찾을 수 없습니다.'
      }
    }
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    emit('flash', getApiErrorMessage(e, '계좌 목록을 불러오지 못했습니다.'), 'alert-danger')
  } finally {
    if (reqId === accountsReqId) {
      accountLoading.value = false
    }
  }
})

async function loadTransactions() {
  if (!selectedAccount.value) return
  if (txAbortController) {
    txAbortController.abort()
  }
  txAbortController = new AbortController()
  const reqId = ++txReqId
  txLoading.value = true
  try {
    const { data } = await accountApi.getTransactions(selectedAccount.value, { signal: txAbortController.signal })
    if (reqId !== txReqId) return
    transactions.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    emit('flash', getApiErrorMessage(e, '거래 내역 조회 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    if (reqId !== txReqId) return
    txLoading.value = false
  }
}

function editTx(tx) {
  editingId.value = tx.id
  form.transaction_id = tx.id
  form.date = toKstDateInput(tx.date) || (tx.date || '').slice(0, 10)
  form.type = tx.type
  form.amount = tx.amount
  form.description = tx.description || ''
  form.source = tx.source || 'principal'
}

function onTypeChange() {
  if (form.type === 'deposit') {
    form.source = 'principal'
  }
}

function resetForm() {
  editingId.value = null
  form.transaction_id = ''
  form.date = getKstTodayDateInput()
  form.type = 'deposit'
  form.amount = 0
  form.description = ''
  form.source = 'principal'
}

async function save() {
  try {
    const payload = {
      account_id: form.account_id,
      date: form.date,
      type: form.type,
      amount: form.amount,
      description: form.description,
      source: form.source,
    }
    if (form.transaction_id) payload.transaction_id = form.transaction_id
    await accountApi.saveTransaction(payload)
    emit('flash', '거래 내역이 저장되었습니다.', 'alert-success')
    await loadTransactions()
    resetForm()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '저장 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

async function delTx(id) {
  if (!confirm('정말 삭제하시겠습니까?')) return
  try {
    await accountApi.deleteTransaction(id)
    emit('flash', '거래 내역이 삭제되었습니다.', 'alert-success')
    await loadTransactions()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '삭제 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

onBeforeUnmount(() => {
  accountsAbortController?.abort()
  txAbortController?.abort()
})
</script>

<style scoped>
.text-primary.fw-bold { color: blue !important; }
.text-danger.fw-bold { color: red !important; }
</style>
