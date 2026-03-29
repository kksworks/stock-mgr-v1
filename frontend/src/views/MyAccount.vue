<template>
  <section class="account-profile-page py-2 py-md-3">
    <div class="card border-0 shadow-sm">
      <div class="card-body p-3 p-md-4">
        <div class="d-flex align-items-center gap-2 mb-3">
          <MaterialIcon name="account_circle" class="text-primary" size="1.4rem" />
          <h1 class="h5 mb-0">내 계정 정보</h1>
        </div>

        <div v-if="loading" class="d-flex align-items-center gap-2 text-muted small">
          <span class="spinner-border spinner-border-sm text-primary" role="status" aria-hidden="true"></span>
          정보를 불러오는 중입니다...
        </div>

        <div v-else-if="errorMessage" class="alert alert-danger mb-0" role="alert">
          {{ errorMessage }}
        </div>

        <div v-else-if="user">
          <div class="table-responsive mb-3">
            <table class="table align-middle mb-0 profile-table">
              <tbody>
                <tr>
                  <th scope="row" class="text-muted fw-semibold">사용자 ID</th>
                  <td class="fw-medium">{{ user.id }}</td>
                </tr>
                <tr>
                  <th scope="row" class="text-muted fw-semibold">아이디</th>
                  <td class="fw-medium">{{ user.username }}</td>
                </tr>
                <tr>
                  <th scope="row" class="text-muted fw-semibold">이메일</th>
                  <td class="fw-medium">
                    <div class="d-flex align-items-center justify-content-between">
                      <span>{{ user.email || '미등록' }}</span>
                      <button type="button" class="btn btn-sm btn-outline-primary py-0" @click="openEmailModal">수정</button>
                    </div>
                  </td>
                </tr>
                <tr>
                  <th scope="row" class="text-muted fw-semibold">권한</th>
                  <td>
                    <span :class="['badge rounded-pill px-3 py-2', user.role === 'admin' ? 'bg-primary-soft text-primary' : 'bg-light text-secondary']">
                      {{ user.role }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="row g-2">
            <div class="col-12 col-md-6">
              <button
                type="button"
                class="btn btn-primary w-100 d-flex align-items-center justify-content-center gap-2 action-btn-lg"
                @click="openApiKeyModal"
              >
                <MaterialIcon name="vpn_key" size="1.1rem" />
                API Key 관리
              </button>
              <div class="small text-muted mt-1">API Key 발급/재발급 및 자동 로그인 URL 확인</div>
            </div>
            <div class="col-12 col-md-6">
              <button
                type="button"
                class="btn btn-outline-primary w-100 d-flex align-items-center justify-content-center gap-2 action-btn-lg"
                @click="openPasswordModal"
              >
                <MaterialIcon name="lock" size="1.1rem" />
                비밀번호 변경
              </button>
              <div class="small text-muted mt-1">현재 비밀번호 확인 후 새 비밀번호로 변경</div>
            </div>
          </div>
        </div>

        <div v-else class="alert alert-warning mb-0" role="alert">
          로그인된 사용자 정보를 찾을 수 없습니다. 다시 로그인해 주세요.
        </div>
      </div>
    </div>
  </section>

  <!-- API Key Modal -->
  <div
    v-if="showApiKeyModal"
    class="modal d-block account-modal"
    tabindex="-1"
    role="dialog"
    aria-modal="true"
    @click.self="closeApiKeyModal"
  >
    <div class="modal-dialog modal-dialog-centered modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title h5 mb-0 d-flex align-items-center gap-2">
            <MaterialIcon name="vpn_key" class="text-primary" size="1.1rem" />
            API Key 관리
          </h2>
          <button type="button" class="btn-close" aria-label="Close" @click="closeApiKeyModal"></button>
        </div>
        <div class="modal-body">
          <p class="text-muted mb-3">
            API Key는 로그인 없이 세션을 생성할 때 사용할 수 있습니다. 재발급하면 이전 키는 즉시 만료됩니다.
          </p>

          <div class="small mb-2">
            <strong>발급 상태:</strong>
            <span class="ms-1">{{ apiKeyInfo.hasApiKey ? '발급됨' : '미발급' }}</span>
            <span v-if="apiKeyInfo.createdAt" class="text-muted ms-2">({{ apiKeyInfo.createdAt }})</span>
          </div>

          <div v-if="issuedApiKey" class="alert alert-warning small py-2 mb-2" role="alert">
            새 API Key는 이번 1회만 표시됩니다. 안전한 곳에 저장해 주세요.
          </div>

          <label class="form-label text-muted mb-1">API Key</label>
          <div class="input-group mb-3">
            <input type="text" class="form-control" :value="issuedApiKey || '발급 후 표시됩니다.'" readonly>
            <button type="button" class="btn btn-outline-secondary" :disabled="!issuedApiKey" @click="copyText(issuedApiKey)">
              복사
            </button>
          </div>

          <label class="form-label text-muted mb-1">자동 로그인 URL</label>
          <div class="input-group mb-2">
            <input type="text" class="form-control" :value="loginUrl || '발급 후 표시됩니다.'" readonly>
            <button type="button" class="btn btn-outline-secondary" :disabled="!loginUrl" @click="copyText(loginUrl)">
              복사
            </button>
          </div>
          <div class="small text-muted">
            기능 URL: <code>/api/login-with-key?api_key=발급받은키&amp;next=/</code>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" @click="closeApiKeyModal">닫기</button>
          <button type="button" class="btn btn-primary" :disabled="issuingApiKey" @click="issueApiKey">
            {{ issuingApiKey ? '발급 중...' : (apiKeyInfo.hasApiKey ? 'API Key 재발급' : 'API Key 발급') }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <!-- Password Modal -->
  <div
    v-if="showPasswordModal"
    class="modal d-block account-modal"
    tabindex="-1"
    role="dialog"
    aria-modal="true"
    @click.self="closePasswordModal"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title h5 mb-0 d-flex align-items-center gap-2">
            <MaterialIcon name="lock" class="text-primary" size="1.1rem" />
            비밀번호 변경
          </h2>
          <button type="button" class="btn-close" aria-label="Close" @click="closePasswordModal"></button>
        </div>
        <form @submit.prevent="changePassword">
          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label text-muted mb-1">현재 비밀번호</label>
              <input v-model="passwordForm.currentPassword" type="password" class="form-control" autocomplete="current-password" required>
            </div>
            <div class="mb-2">
              <label class="form-label text-muted mb-1">새 비밀번호</label>
              <input v-model="passwordForm.newPassword" type="password" class="form-control" autocomplete="new-password" minlength="6" required>
            </div>
            <div>
              <label class="form-label text-muted mb-1">새 비밀번호 확인</label>
              <input v-model="passwordForm.confirmPassword" type="password" class="form-control" autocomplete="new-password" minlength="6" required>
            </div>

            <div class="small text-muted mt-2">새 비밀번호는 6자 이상이어야 합니다.</div>

            <div
              v-if="passwordMessage"
              :class="['alert', 'small', 'py-2', 'mt-2', passwordMessageType === 'success' ? 'alert-success' : 'alert-danger']"
              role="alert"
            >
              {{ passwordMessage }}
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="closePasswordModal">닫기</button>
            <button type="submit" class="btn btn-primary" :disabled="changingPassword">
              {{ changingPassword ? '변경 중...' : '비밀번호 변경' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <!-- Email Modal -->
  <div
    v-if="showEmailModal"
    class="modal d-block account-modal"
    tabindex="-1"
    role="dialog"
    aria-modal="true"
    @click.self="closeEmailModal"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h2 class="modal-title h5 mb-0 d-flex align-items-center gap-2">
            <MaterialIcon name="email" class="text-primary" size="1.1rem" />
            이메일 변경
          </h2>
          <button type="button" class="btn-close" aria-label="Close" @click="closeEmailModal"></button>
        </div>
        <form @submit.prevent="updateEmail">
          <div class="modal-body">
            <div class="mb-2">
              <label class="form-label text-muted mb-1">이메일 주소</label>
              <input v-model="emailForm.email" type="email" class="form-control" placeholder="example@email.com">
              <div class="small text-muted mt-2">비밀번호 분실 시 대처 등을 위해 사용됩니다.</div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline-secondary" @click="closeEmailModal">닫기</button>
            <button type="submit" class="btn btn-primary" :disabled="updatingEmail">
              {{ updatingEmail ? '저장 중...' : '저장' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div v-if="toast.show" class="toast-container position-fixed top-0 end-0 p-3">
    <div :class="['toast', 'show', toast.type === 'success' ? 'text-bg-success' : 'text-bg-danger']" role="status" aria-live="polite">
      <div class="toast-body py-2 px-3">
        {{ toast.message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import MaterialIcon from '../components/MaterialIcon.vue'
import { authApi, getApiErrorMessage } from '../api'
import { authStore } from '../stores/auth'

const loading = ref(true)
const errorMessage = ref('')
const user = ref(authStore.user)
const issuingApiKey = ref(false)
const issuedApiKey = ref('')
const loginUrl = ref('')
const changingPassword = ref(false)
const passwordMessage = ref('')
const passwordMessageType = ref('success')
const showApiKeyModal = ref(false)
const showPasswordModal = ref(false)
const showEmailModal = ref(false)
const updatingEmail = ref(false)
const emailForm = ref({
  email: '',
})
const toast = ref({
  show: false,
  message: '',
  type: 'success',
})
let toastTimer = null
const apiKeyInfo = ref({
  hasApiKey: false,
  createdAt: '',
})
const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

async function loadMyAccount() {
  loading.value = true
  errorMessage.value = ''
  try {
    const { data } = await authApi.me()
    if (data?.logged_in && data?.user) {
      user.value = data.user
      authStore.setUser(data.user)
      return
    }
    user.value = null
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, '계정 정보를 불러오지 못했습니다.')
  } finally {
    loading.value = false
  }
}

async function loadApiKeyInfo() {
  try {
    const { data } = await authApi.getMyApiKeyInfo()
    apiKeyInfo.value = {
      hasApiKey: Boolean(data?.has_api_key),
      createdAt: data?.api_key_created_at || '',
    }
  } catch (error) {
    console.error('Failed to load api key info', error)
  }
}

async function issueApiKey() {
  issuingApiKey.value = true
  errorMessage.value = ''
  try {
    const { data } = await authApi.issueMyApiKey()
    issuedApiKey.value = data?.api_key || ''
    loginUrl.value = data?.login_url || ''
    apiKeyInfo.value = {
      hasApiKey: true,
      createdAt: data?.api_key_created_at || '',
    }
    showToast(data?.message || 'API Key가 발급되었습니다.', 'success')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'API Key 발급에 실패했습니다.')
    showToast(errorMessage.value, 'error')
  } finally {
    issuingApiKey.value = false
  }
}

async function copyText(text) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    showToast('클립보드에 복사했습니다.', 'success')
  } catch (error) {
    console.error('Copy failed', error)
    showToast('복사에 실패했습니다. 브라우저 권한을 확인해 주세요.', 'error')
  }
}

function openApiKeyModal() {
  showApiKeyModal.value = true
}

function closeApiKeyModal() {
  showApiKeyModal.value = false
}

function openPasswordModal() {
  passwordMessage.value = ''
  showPasswordModal.value = true
}

function closePasswordModal() {
  showPasswordModal.value = false
}

function openEmailModal() {
  emailForm.value.email = user.value.email || ''
  showEmailModal.value = true
}

function closeEmailModal() {
  showEmailModal.value = false
}

function showToast(message, type = 'success') {
  if (toastTimer) {
    window.clearTimeout(toastTimer)
  }
  toast.value = {
    show: true,
    message,
    type,
  }
  toastTimer = window.setTimeout(() => {
    toast.value.show = false
  }, 2200)
}

function handleGlobalKeydown(event) {
  if (event.key === 'Escape') {
    if (showApiKeyModal.value) closeApiKeyModal()
    if (showPasswordModal.value) closePasswordModal()
    if (showEmailModal.value) closeEmailModal()
  }
}

async function updateEmail() {
  updatingEmail.value = true
  try {
    await authApi.updateProfile({ email: emailForm.value.email })
    user.value.email = emailForm.value.email
    authStore.setUser({ ...authStore.user, email: emailForm.value.email })
    showToast('이메일 정보가 업데이트되었습니다.', 'success')
    closeEmailModal()
  } catch (error) {
    showToast(getApiErrorMessage(error, '이메일 업데이트에 실패했습니다.'), 'error')
  } finally {
    updatingEmail.value = false
  }
}

async function changePassword() {
  passwordMessage.value = ''
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    passwordMessageType.value = 'error'
    passwordMessage.value = '새 비밀번호와 확인 값이 일치하지 않습니다.'
    return
  }

  changingPassword.value = true
  try {
    const { data } = await authApi.changeMyPassword({
      current_password: passwordForm.value.currentPassword,
      new_password: passwordForm.value.newPassword,
    })
    passwordMessageType.value = 'success'
    passwordMessage.value = data?.message || '비밀번호가 변경되었습니다.'
    passwordForm.value.currentPassword = ''
    passwordForm.value.newPassword = ''
    passwordForm.value.confirmPassword = ''
    showToast(passwordMessage.value, 'success')
    closePasswordModal()
  } catch (error) {
    passwordMessageType.value = 'error'
    passwordMessage.value = getApiErrorMessage(error, '비밀번호 변경에 실패했습니다.')
    showToast(passwordMessage.value, 'error')
  } finally {
    changingPassword.value = false
  }
}

onMounted(() => {
  loadMyAccount()
  loadApiKeyInfo()
  document.addEventListener('keydown', handleGlobalKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', handleGlobalKeydown)
  if (toastTimer) {
    window.clearTimeout(toastTimer)
  }
})

watch(
  () => showApiKeyModal.value || showPasswordModal.value,
  (isAnyModalOpen) => {
    document.body.style.overflow = isAnyModalOpen ? 'hidden' : ''
  }
)
</script>

<style scoped>
.account-profile-page {
  max-width: 760px;
  margin: 0 auto;
}

.profile-table th {
  width: 140px;
  white-space: nowrap;
}

.action-btn-lg {
  min-height: 48px;
  font-size: 0.98rem;
  font-weight: 600;
}

:global(:root[data-theme="dark"]) .profile-table th {
  color: var(--ui-text-muted) !important;
}

.modal {
  z-index: 1060;
}

.account-modal {
  background: rgba(20, 24, 31, 0.5);
}

.account-modal .modal-content {
  border: 1px solid var(--ui-border);
  border-radius: 14px;
}

.account-modal .modal-body {
  font-size: 0.97rem;
}

.account-modal .modal-header,
.account-modal .modal-footer {
  padding-top: 0.9rem;
  padding-bottom: 0.9rem;
}
</style>
