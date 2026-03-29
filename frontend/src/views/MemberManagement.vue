<template>
  <div class="container py-4 stock-theme">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="fw-bold text-gradient d-flex align-items-center gap-2">
        <MaterialIcon name="group" size="1.5rem" />
        멤버 관리
      </h2>
    </div>

    <PageLoadingPlaceholder v-if="loading && users.length === 0" variant="table" :rows="8" />

    <div v-else class="card border-0 shadow-sm rounded-4 overflow-hidden">
      <div
        class="table-responsive"
        :style="isVirtualEnabled ? { maxHeight: `${containerHeight}px`, overflowY: 'auto' } : {}"
        @scroll="onVirtualScroll"
      >
        <table
          class="table table-hover align-middle mb-0"
          :class="{ 'virtual-scroll-table': isVirtualEnabled }"
        >
          <thead class="bg-light">
            <tr>
              <th class="px-4 py-3 text-secondary small fw-bold text-uppercase">사용자</th>
              <th class="px-4 py-3 text-secondary small fw-bold text-uppercase">역할</th>
              <th class="px-4 py-3 text-secondary small fw-bold text-uppercase">ID</th>
              <th class="px-4 py-3 text-secondary small fw-bold text-uppercase">보유 계좌</th>
              <th class="px-4 py-3 text-secondary small fw-bold text-uppercase">관리</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="isVirtualEnabled && topSpacerHeight > 0" aria-hidden="true">
              <td colspan="5" :style="{ height: `${topSpacerHeight}px`, padding: 0, border: 0 }"></td>
            </tr>
            <tr
              v-for="(user, idx) in visibleUsers"
              :key="`${user.id}-${isVirtualEnabled ? getRealIndex(idx) : idx}`"
              :style="isVirtualEnabled ? { height: `${rowHeight}px` } : {}"
            >
              <td class="px-4 py-3">
                <div class="d-flex align-items-center">
                  <div class="avatar me-3">{{ user.username[0].toUpperCase() }}</div>
                  <span class="fw-semibold">{{ user.username }}</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <span :class="['badge rounded-pill px-3 py-2', user.role === 'admin' ? 'bg-primary-soft text-primary' : 'bg-light text-secondary']">
                  {{ user.role }}
                </span>
              </td>
              <td class="px-4 py-3 text-muted small font-monospace">
                {{ user.id }}
              </td>
              <td class="px-4 py-3">
                <router-link
                  :to="`/accounts?ownerUserId=${encodeURIComponent(user.id)}`"
                  class="btn btn-outline-secondary btn-sm d-inline-flex align-items-center gap-1"
                >
                  <MaterialIcon name="account_balance" size="1rem" />
                  계좌 보기
                </router-link>
              </td>
              <td class="px-4 py-3">
                <button
                  type="button"
                  class="btn btn-outline-primary btn-sm d-inline-flex align-items-center gap-1"
                  @click="openPasswordModal(user)"
                >
                  <MaterialIcon name="lock_reset" size="1rem" />
                  비밀번호 설정
                </button>
              </td>
            </tr>
            <tr v-if="isVirtualEnabled && bottomSpacerHeight > 0" aria-hidden="true">
              <td colspan="5" :style="{ height: `${bottomSpacerHeight}px`, padding: 0, border: 0 }"></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 비밀번호 강제 설정 모달 -->
    <div class="modal fade" id="resetPwModal" tabindex="-1" aria-labelledby="resetPwModalLabel" aria-hidden="true" ref="modalEl">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 id="resetPwModalLabel" class="modal-title d-flex align-items-center gap-2">
              <MaterialIcon name="lock_reset" size="1.25rem" />
              비밀번호 설정
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="닫기"></button>
          </div>
          <div class="modal-body">
            <p class="text-muted small mb-3">
              <strong>{{ targetUser?.username }}</strong> 계정의 새 비밀번호를 입력하세요. (관리자 강제 설정)
            </p>
            <div class="mb-3">
              <label class="form-label">새 비밀번호</label>
              <input v-model="newPassword" type="password" class="form-control" autocomplete="new-password" minlength="6" placeholder="6자 이상">
            </div>
            <div class="mb-0">
              <label class="form-label">새 비밀번호 확인</label>
              <input v-model="newPasswordConfirm" type="password" class="form-control" autocomplete="new-password" minlength="6" placeholder="한 번 더 입력">
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">취소</button>
            <button type="button" class="btn btn-primary" :disabled="saving" @click="submitPassword">
              {{ saving ? '저장 중…' : '저장' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Modal } from 'bootstrap'
import { authApi, getApiErrorMessage } from '../api'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import { useVirtualRows } from '../composables/useVirtualRows'
import { getVirtualScrollOptions } from '../config/virtualScroll'

const emit = defineEmits(['flash'])

const users = ref([])
const modalEl = ref(null)
let modalInstance = null
const targetUser = ref(null)
const newPassword = ref('')
const newPasswordConfirm = ref('')
const saving = ref(false)
const loading = ref(true)
let usersAbortController = null
let usersReqId = 0

const {
  rowHeight,
  containerHeight,
  isVirtualEnabled,
  visibleItems: visibleUsers,
  topSpacerHeight,
  bottomSpacerHeight,
  onVirtualScroll,
  getRealIndex,
} = useVirtualRows(users, getVirtualScrollOptions('members', {
  rowHeight: 66,
  containerHeight: 520,
  threshold: 80,
}))

onMounted(async () => {
  try {
    await loadUsers()
  } finally {
    loading.value = false
  }
})

async function loadUsers() {
  if (usersAbortController) {
    usersAbortController.abort()
  }
  usersAbortController = new AbortController()
  const reqId = ++usersReqId
  try {
    const { data } = await authApi.getUsers({ signal: usersAbortController.signal })
    if (reqId !== usersReqId) return
    users.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    emit('flash', getApiErrorMessage(e, '사용자 목록을 불러오지 못했습니다.'), 'alert-danger')
  }
}

function openPasswordModal(user) {
  targetUser.value = user
  newPassword.value = ''
  newPasswordConfirm.value = ''
  if (!modalInstance && modalEl.value) {
    modalInstance = new Modal(modalEl.value)
  }
  modalInstance?.show()
}

async function submitPassword() {
  if (!targetUser.value) return
  if (newPassword.value.length < 6) {
    emit('flash', '비밀번호는 6자 이상이어야 합니다.', 'alert-warning')
    return
  }
  if (newPassword.value !== newPasswordConfirm.value) {
    emit('flash', '비밀번호 확인이 일치하지 않습니다.', 'alert-warning')
    return
  }
  saving.value = true
  try {
    const { data } = await authApi.resetUserPassword({
      user_id: targetUser.value.id,
      new_password: newPassword.value,
    })
    emit('flash', data.message || '비밀번호가 변경되었습니다.', 'alert-success')
    modalInstance?.hide()
    newPassword.value = ''
    newPasswordConfirm.value = ''
    targetUser.value = null
  } catch (e) {
    emit('flash', getApiErrorMessage(e, '저장에 실패했습니다.'), 'alert-danger')
  } finally {
    saving.value = false
  }
}

onBeforeUnmount(() => {
  usersAbortController?.abort()
  modalInstance?.hide()
})
</script>

<style scoped>
.text-gradient {
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.bg-primary-soft {
  background-color: rgba(37, 99, 235, 0.1);
}
.avatar {
  width: 32px;
  height: 32px;
  background: #f3f4f6;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 0.875rem;
  color: #4b5563;
}
</style>
