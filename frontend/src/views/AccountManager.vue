<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h1 class="d-flex align-items-center gap-2 mb-0">
        <MaterialIcon name="account_balance" size="1.75rem" />
        계좌 관리
      </h1>
      <button class="btn btn-primary d-flex align-items-center gap-1" @click="openAddModal">
        <MaterialIcon name="add" size="1.2rem" />
        계좌 추가
      </button>
    </div>

    <div v-if="authStore.isAdmin" class="alert alert-secondary mb-3 small">
      <strong>관리자:</strong> 기본적으로 본인 소유 계좌만 표시됩니다. 멤버 관리에서 특정 사용자의 계좌 관리로 이동할 수 있습니다.
    </div>

    <PageLoadingPlaceholder v-if="loading && accounts.length === 0" variant="table" :rows="8" />
    <div v-else class="row g-4">
      <!-- 나의 계좌 그룹 -->
      <div v-if="myAccounts.length > 0" class="col-12">
        <div class="px-2 py-1 small fw-bold text-muted d-flex align-items-center gap-1 mb-2 opacity-75 text-uppercase letter-spacing-1">
          <MaterialIcon name="person" size="1.1rem" class="text-primary" />
          나의 계좌 ({{ myAccounts.length }})
        </div>
        <div class="card shadow-sm border-0">
          <!-- 데스크탑 테이블 -->
          <div class="d-none d-md-block table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th class="ps-4 py-3 text-muted x-small text-uppercase">계좌명</th>
                  <th class="py-3 text-muted x-small text-uppercase">계좌번호</th>
                  <th class="py-3 text-muted x-small text-uppercase">표시 소유자</th>
                  <th v-if="authStore.isAdmin" class="py-3 text-muted x-small text-uppercase">계정(소유)</th>
                  <th class="py-3 text-muted x-small text-uppercase">구분</th>
                  <th class="py-3 text-muted x-small text-uppercase">태그</th>
                  <th class="text-end pe-4 py-3 text-muted x-small text-uppercase">상세</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="acc in myAccounts" :key="`d-${acc.id}`">
                  <td class="ps-4">
                    <div class="fw-bold text-dark">{{ acc.account_name }}</div>
                    <div v-if="acc.description" class="text-muted small">{{ acc.description }}</div>
                  </td>
                  <td><span class="badge bg-light text-secondary border fw-normal">{{ acc.account_number }}</span></td>
                  <td><span class="text-muted">{{ acc.owner }}</span></td>
                  <td v-if="authStore.isAdmin">
                    <span class="small text-muted">{{ acc.owner_username || '—' }}</span>
                  </td>
                  <td>
                    <span v-if="acc.is_public" class="badge bg-warning-subtle text-warning border border-warning me-1 fw-normal">공개</span>
                    <span class="badge bg-light text-secondary border fw-normal">내 계좌</span>
                  </td>
                  <td>
                    <span
                      v-for="tag in (acc.tags || [])"
                      :key="`${acc.id}-${tag}`"
                      class="badge rounded-pill text-bg-light border me-1"
                    >{{ tag }}</span>
                    <span v-if="!(acc.tags || []).length" class="text-muted small">미분류</span>
                  </td>
                  <td class="text-end pe-4">
                    <router-link :to="`/accounts/${acc.id}`" class="btn btn-sm btn-outline-primary d-inline-flex gap-1 align-items-center">
                      <MaterialIcon name="arrow_forward" size="0.9rem" />
                      상세
                    </router-link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 모바일 카드 목록 -->
          <div class="d-md-none">
            <div v-for="acc in myAccounts" :key="`m-${acc.id}`" class="list-group-item px-4 py-3 border-bottom border-light-subtle">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                  <div class="fw-bold text-dark fs-6">{{ acc.account_name }}</div>
                  <div class="small text-muted mt-1 d-flex gap-2">
                    <span class="badge bg-light text-secondary border fw-normal">{{ acc.account_number }}</span>
                    <span>{{ acc.owner }}</span>
                  </div>
                  <div class="small mt-2">
                    <span
                      v-for="tag in (acc.tags || [])"
                      :key="`m-tag-${acc.id}-${tag}`"
                      class="badge rounded-pill text-bg-light border me-1"
                    >{{ tag }}</span>
                    <span v-if="!(acc.tags || []).length" class="text-muted">미분류</span>
                  </div>
                </div>
                <div class="d-flex flex-column align-items-end gap-1">
                  <span v-if="acc.is_public" class="badge bg-warning-subtle text-warning border border-warning fw-normal">공개</span>
                  <span class="badge bg-light text-secondary border fw-normal">내 계좌</span>
                </div>
              </div>
              <div class="mt-2">
                <router-link :to="`/accounts/${acc.id}`" class="btn btn-sm btn-outline-primary w-100 d-inline-flex justify-content-center gap-1">
                  <MaterialIcon name="arrow_forward" size="0.9rem" />
                  상세 보기
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 공유받은 계좌 그룹 -->
      <div v-if="sharedAccounts.length > 0" class="col-12 mt-4">
        <div class="px-2 py-1 small fw-bold text-muted d-flex align-items-center gap-1 mb-2 opacity-75 text-uppercase letter-spacing-1">
          <MaterialIcon name="group" size="1.1rem" class="text-info" />
          공유받은 계좌 ({{ sharedAccounts.length }})
        </div>
        <div class="card shadow-sm border-0 border-info border-start border-4">
          <!-- 데스크탑 테이블 -->
          <div class="d-none d-md-block table-responsive">
            <table class="table table-hover align-middle mb-0">
              <thead class="table-light">
                <tr>
                  <th class="ps-4 py-3 text-muted x-small text-uppercase">계좌명</th>
                  <th class="py-3 text-muted x-small text-uppercase">계좌번호</th>
                  <th class="py-3 text-muted x-small text-uppercase">표시 소유자</th>
                  <th v-if="authStore.isAdmin" class="py-3 text-muted x-small text-uppercase">계정(소유)</th>
                  <th class="py-3 text-muted x-small text-uppercase">구분</th>
                  <th class="text-end pe-4 py-3 text-muted x-small text-uppercase">상세</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="acc in sharedAccounts" :key="`d-${acc.id}`">
                  <td class="ps-4">
                    <div class="fw-bold text-dark d-flex align-items-center gap-2">
                      {{ acc.account_name }}
                      <span class="badge bg-info-subtle text-info border border-info fw-normal" style="font-size: 0.65rem;">공유</span>
                    </div>
                    <div v-if="acc.description" class="text-muted small">{{ acc.description }}</div>
                  </td>
                  <td><span class="badge bg-light text-secondary border fw-normal">{{ acc.account_number }}</span></td>
                  <td><span class="text-muted">{{ acc.owner }}</span></td>
                  <td v-if="authStore.isAdmin">
                    <span class="small text-muted">{{ acc.owner_username || '—' }}</span>
                  </td>
                  <td>
                    <span v-if="acc.is_public" class="badge bg-warning-subtle text-warning border border-warning me-1 fw-normal">공개</span>
                  </td>
                  <td class="text-end pe-4">
                    <router-link :to="`/accounts/${acc.id}`" class="btn btn-sm btn-outline-primary d-inline-flex gap-1 align-items-center">
                      <MaterialIcon name="arrow_forward" size="0.9rem" />
                      상세
                    </router-link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 모바일 카드 목록 -->
          <div class="d-md-none">
            <div v-for="acc in sharedAccounts" :key="`m-${acc.id}`" class="list-group-item px-4 py-3 border-bottom border-light-subtle">
              <div class="d-flex justify-content-between align-items-start mb-2">
                <div>
                  <div class="fw-bold text-dark fs-6 d-flex align-items-center gap-1">
                    {{ acc.account_name }}
                    <span class="badge bg-info-subtle text-info border border-info fw-normal" style="font-size: 0.65rem;">공유</span>
                  </div>
                  <div class="small text-muted mt-1 d-flex gap-2">
                    <span class="badge bg-light text-secondary border fw-normal">{{ acc.account_number }}</span>
                    <span>{{ acc.owner }}</span>
                  </div>
                </div>
                <div class="d-flex flex-column align-items-end gap-1">
                  <span v-if="acc.is_public" class="badge bg-warning-subtle text-warning border border-warning fw-normal">공개</span>
                </div>
              </div>
              <div class="mt-2">
                <router-link :to="`/accounts/${acc.id}`" class="btn btn-sm btn-outline-primary w-100 d-inline-flex justify-content-center gap-1">
                  <MaterialIcon name="arrow_forward" size="0.9rem" />
                  상세 보기
                </router-link>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!loading && myAccounts.length === 0" class="col-12 text-center text-muted py-5 small border rounded-4 bg-light">
        등록된 계좌가 없습니다.
      </div>
    </div>
  </div>

  <!-- 계좌 추가 모달 -->
  <div class="modal fade" id="addAccountModal" tabindex="-1" aria-hidden="true" ref="addModalRef">
    <div class="modal-dialog">
      <div class="modal-content shadow-lg border-0 rounded-4">
        <div class="modal-header border-0 pb-2 pt-4 px-4">
          <h6 class="modal-title fw-bold mb-0">계좌 추가</h6>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form @submit.prevent="save">
          <div class="modal-body px-4 pb-2 pt-3">
            <template v-if="authStore.isAdmin">
              <div class="mb-3">
                <label class="form-label text-muted small mb-1">소유자 계정</label>
                <select v-model="form.ownerUserId" class="form-select shadow-none" required>
                  <option v-for="u in allUsers" :key="u.id" :value="u.id">{{ u.username }}</option>
                </select>
              </div>
              <div class="mb-3">
                <label class="form-label text-muted small d-block mb-1">함께 볼 수 있는 사용자 (공유)</label>
                <div class="border rounded p-2 bg-light" style="max-height: 120px; overflow-y: auto;">
                  <div v-for="u in shareCandidates" :key="u.id" class="form-check">
                    <input :id="'add-share-' + u.id" v-model="form.sharedUserIds" class="form-check-input" type="checkbox" :value="u.id">
                    <label class="form-check-label small" :for="'add-share-' + u.id">{{ u.username }}</label>
                  </div>
                  <p v-if="shareCandidates.length === 0" class="text-muted small mb-0">다른 사용자가 없습니다.</p>
                </div>
              </div>
              <div class="mb-3 form-check">
                <input id="add-is-public" v-model="form.is_public" class="form-check-input" type="checkbox">
                <label class="form-check-label small" for="add-is-public">Public Export (비로그인 포함 전체 조회 허용)</label>
              </div>
            </template>
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">계좌명</label>
              <input v-model="form.account_name" type="text" class="form-control shadow-none" placeholder="예: 주식 위탁 계좌" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">계좌번호</label>
              <input v-model="form.account_number" type="text" class="form-control shadow-none" placeholder="예: 123-45-67890" required>
            </div>
            <div class="mb-3">
              <label class="form-label text-muted small mb-1">표시 소유자명</label>
              <input v-model="form.owner" type="text" class="form-control shadow-none" placeholder="예: 홍길동" required>
            </div>
            <div class="mb-0">
              <label class="form-label text-muted small mb-1">설명</label>
              <textarea v-model="form.description" class="form-control shadow-none" rows="2" placeholder="계좌에 대한 추가 정보를 입력하세요."></textarea>
            </div>
            <div class="mt-3">
              <label class="form-label text-muted small mb-1">분류 태그</label>
              <input
                v-model="form.tagsInput"
                type="text"
                class="form-control shadow-none"
                placeholder="예: 장기, ISA, 연금 (쉼표로 구분)"
              >
              <div class="small text-muted mt-1">쉼표(,)로 여러 태그를 입력하세요.</div>
            </div>
          </div>
          <div class="modal-footer border-0 px-4 pb-4 pt-3 d-flex gap-2">
            <button type="button" class="btn btn-outline-secondary flex-grow-1" data-bs-dismiss="modal">취소</button>
            <button type="submit" class="btn btn-primary flex-grow-1 fw-semibold" :disabled="saving">
              {{ saving ? '저장 중...' : '추가' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { Modal } from 'bootstrap'
import { accountApi, authApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'

const emit = defineEmits(['flash'])
const route = useRoute()
const accounts = ref([])
const allUsers = ref([])
const loading = ref(true)
const saving = ref(false)
const addModalRef = ref(null)
let addBootstrapModal = null
let loadAccountsAbortController = null
let loadUsersAbortController = null

const form = reactive({
  id: null,
  account_name: '',
  account_number: '',
  owner: '',
  description: '',
  ownerUserId: '',
  sharedUserIds: [],
  is_public: false,
  tagsInput: '',
})

const shareCandidates = computed(() => {
  const oid = form.ownerUserId
  return allUsers.value.filter((u) => u.id !== oid)
})

const targetOwnerUserId = computed(() => String(route.query.ownerUserId || authStore.user?.id || ''))

function isSharedForMe(acc) {
  const me = authStore.user?.id
  if (!me || !acc.user_id) return false
  return acc.user_id !== me && (acc.shared_user_ids || []).includes(me)
}

const myAccounts = computed(() => {
  return accounts.value.filter(acc => String(acc.user_id) === targetOwnerUserId.value)
})
const sharedAccounts = computed(() => [])


function openAddModal() {
  form.id = null
  form.account_name = ''
  form.account_number = ''
  form.owner = ''
  form.description = ''
  form.ownerUserId = authStore.user?.id || ''
  form.sharedUserIds = []
  form.is_public = false
  form.tagsInput = ''
  if (!addBootstrapModal && addModalRef.value) {
    addBootstrapModal = new Modal(addModalRef.value)
  }
  addBootstrapModal?.show()
}

async function load() {
  if (loadAccountsAbortController) loadAccountsAbortController.abort()
  loadAccountsAbortController = new AbortController()
  const { data } = await accountApi.getAccounts({ signal: loadAccountsAbortController.signal })
  accounts.value = data
}

async function loadUsers() {
  if (!authStore.isAdmin) return
  if (loadUsersAbortController) loadUsersAbortController.abort()
  loadUsersAbortController = new AbortController()
  try {
    const { data } = await authApi.getUsers({ signal: loadUsersAbortController.signal })
    allUsers.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    emit('flash', getApiErrorMessage(e, '사용자 목록을 불러오지 못했습니다.'), 'alert-danger')
  }
}

async function save() {
  saving.value = true
  try {
    const payload = {
      id: form.id,
      account_name: form.account_name,
      account_number: form.account_number,
      owner: form.owner,
      description: form.description,
      tags: form.tagsInput.split(',').map(v => v.trim()).filter(Boolean),
    }
    if (authStore.isAdmin) {
      payload.user_id = form.ownerUserId
      payload.shared_user_ids = [...form.sharedUserIds]
      payload.is_public = Boolean(form.is_public)
    }
    await accountApi.updateAccount(payload)
    emit('flash', '계좌가 추가되었습니다.', 'alert-success')
    addBootstrapModal?.hide()
    await load()
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '저장 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    saving.value = false
  }
}

onMounted(async () => {
  try {
    await loadUsers()
    if (authStore.isAdmin && authStore.user?.id) {
      form.ownerUserId = authStore.user.id
    }
    await load()
  } finally {
    loading.value = false
  }
  if (addModalRef.value) {
    addBootstrapModal = new Modal(addModalRef.value)
  }
})

onBeforeUnmount(() => {
  loadAccountsAbortController?.abort()
  loadUsersAbortController?.abort()
  addBootstrapModal?.dispose()
})
</script>

<style scoped>
.hover-primary:hover {
  color: var(--ui-primary) !important;
}
</style>
