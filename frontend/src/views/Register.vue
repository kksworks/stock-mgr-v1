<template>
  <div class="login-wrapper d-flex align-items-center justify-content-center p-3">
    <div class="auth-card shadow-sm border rounded-4 bg-white">
      <div class="text-center mb-4 mt-2">
        <div class="brand-logo mb-3 mx-auto d-flex align-items-center justify-content-center">
          <MaterialIcon name="person_add" size="2.5rem" class="text-primary" />
        </div>
        <h3 class="fw-bold text-dark mb-1 letter-spacing-tight">회원가입</h3>
        <p class="text-muted small">새로운 계정을 만들고 시작하세요.</p>
      </div>

      <form @submit.prevent="handleRegister" class="auth-form">
        <div class="mb-3">
          <label class="form-label small fw-bold text-secondary">아이디</label>
          <input 
            v-model="form.username" 
            type="text" 
            class="form-control flat-input" 
            placeholder="아이디를 입력하세요"
            required
          />
        </div>

        <div class="mb-3">
          <label class="form-label small fw-bold text-secondary">비밀번호</label>
          <input 
            v-model="form.password" 
            type="password" 
            class="form-control flat-input" 
            placeholder="비밀번호를 입력하세요"
            required
          />
        </div>

        <div class="mb-3">
          <label class="form-label small fw-bold text-secondary">비밀번호 확인</label>
          <input 
            v-model="form.confirmPassword" 
            type="password" 
            class="form-control flat-input" 
            placeholder="비밀번호를 다시 입력하세요"
            required
          />
        </div>

        <div class="mb-4">
          <label class="form-label small fw-bold text-secondary">이메일 (선택)</label>
          <input 
            v-model="form.email" 
            type="email" 
            class="form-control flat-input" 
            placeholder="비밀번호 분실 시 사용될 이메일"
          />
        </div>

        <div v-if="error" class="alert alert-danger py-2 small mb-4">
           <MaterialIcon name="error" size="1.1rem" class="me-1" style="vertical-align: middle;" />
           {{ error }}
        </div>

        <button 
          type="submit" 
          class="btn btn-primary w-100 py-2 fw-bold mb-2 rounded-3"
          :disabled="loading"
        >
          <span v-if="!loading">가입하기</span>
          <span v-else class="spinner-border spinner-border-sm" role="status"></span>
        </button>
      </form>

      <div class="text-center mt-4 pt-3 border-top">
        <p class="small text-muted mb-0">
          이미 계정이 있으신가요? 
          <router-link to="/login" class="text-primary fw-bold text-decoration-none ms-1">
            로그인
          </router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { authApi, getApiErrorMessage } from '../api'
import MaterialIcon from '../components/MaterialIcon.vue'

const router = useRouter()
const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})
const loading = ref(false)
const error = ref('')

async function handleRegister() {
  if (form.password !== form.confirmPassword) {
    error.value = '비밀번호가 일치하지 않습니다.'
    return
  }
  
  if (loading.value) return
  loading.value = true
  error.value = ''
  
  try {
    await authApi.register({
      username: form.username,
      password: form.password,
      email: form.email
    })
    alert('회원가입이 완료되었습니다! 로그인 해주세요.')
    router.push('/login')
  } catch (e) {
    error.value = getApiErrorMessage(e, '회원가입에 실패했습니다. 다시 시도해 주세요.')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* style shared with Login.vue for consistency */
.login-wrapper {
  min-height: 100vh;
  width: 100%;
  background-color: #f1f5f9;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  padding: 2.5rem 2rem;
  border-color: #e2e8f0 !important;
}

.letter-spacing-tight {
  letter-spacing: -0.025em;
}

.brand-logo {
  width: 64px;
  height: 64px;
  background: #f8fafc;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
}

.flat-input {
  background-color: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
  padding: 0.6rem 0.75rem;
  font-size: 0.95rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.flat-input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  outline: none;
}

.btn-primary {
  background-color: #2563eb;
  border: none;
  font-size: 1rem;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.text-primary {
  color: #2563eb !important;
}

:global([data-theme="dark"]) .login-wrapper {
  background-color: #0f172a;
}
:global([data-theme="dark"]) .auth-card {
  background-color: #1e293b;
  border-color: #334155 !important;
}
:global([data-theme="dark"]) .text-dark {
  color: #f1f5f9 !important;
}
:global([data-theme="dark"]) .flat-input {
  background-color: #0f172a;
  border-color: #334155;
  color: #f1f5f9;
}
</style>
