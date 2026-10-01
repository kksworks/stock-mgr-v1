<template>
  <div class="stock-theme">
    <nav class="navbar navbar-expand-lg stock-nav">
      <div class="container-fluid px-2 px-md-3">
        <router-link class="navbar-brand d-flex align-items-center" to="/">
          <img src="/logo.png" alt="GrowMore" style="height: 1.8rem; width: auto;" />
        </router-link>
        <button
          class="navbar-toggler border-0 py-2"
          type="button"
          :aria-expanded="isMobileNavOpen ? 'true' : 'false'"
          aria-controls="navbarNav"
          aria-label="메뉴"
          @click="toggleMobileNav"
        >
          <span class="navbar-toggler-icon"></span>
        </button>
        <div id="navbarNav" class="collapse navbar-collapse" :class="{ show: isMobileNavOpen }">
          <ul class="navbar-nav me-auto gap-1">

            <template v-if="authStore.isAuthenticated">
              <li class="nav-item">
                <router-link class="nav-link d-flex align-items-center gap-2" to="/" @click="closeMobileNavIfNeeded">
                  <MaterialIcon name="dashboard" />
                  Dashboard
                </router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link d-flex align-items-center gap-2" to="/balances" @click="closeMobileNavIfNeeded">
                  <MaterialIcon name="account_balance_wallet" />
                  계좌 잔고
                </router-link>
              </li>
              <li class="nav-item">
                <router-link class="nav-link d-flex align-items-center gap-2" to="/my-account" @click="closeMobileNavIfNeeded">
                  <MaterialIcon name="person" />
                  내 정보
                </router-link>
              </li>
            </template>
            <li class="nav-item">
              <router-link class="nav-link d-flex align-items-center gap-2" to="/site-guide" @click="closeMobileNavIfNeeded">
                <MaterialIcon name="help_outline" />
                사이트 안내
              </router-link>
            </li>
            <template v-if="authStore.isAuthenticated">
              <li ref="settingsMenuRef" class="nav-item dropdown" :class="{ show: isSettingsOpen }">
                <button
                  type="button"
                  class="nav-link dropdown-toggle d-flex align-items-center gap-2 btn btn-link text-decoration-none"
                  :aria-expanded="isSettingsOpen ? 'true' : 'false'"
                  @click="toggleSettingsMenu"
                >
                  <MaterialIcon name="settings" />
                  설정
                </button>
                <ul class="dropdown-menu dropdown-menu-end" :class="{ show: isSettingsOpen }">
                  <li>
                    <router-link class="dropdown-item d-flex align-items-center gap-2" to="/portfolios" @click="closeMenusAfterNavigate">
                      <MaterialIcon name="pie_chart" size="1.125rem" />
                      포트폴리오
                    </router-link>
                  </li>
                  <li>
                    <router-link class="dropdown-item d-flex align-items-center gap-2" to="/accounts" @click="closeMenusAfterNavigate">
                      <MaterialIcon name="account_balance" size="1.125rem" />
                      계좌 설정
                    </router-link>
                  </li>
                  <li>
                    <router-link class="dropdown-item d-flex align-items-center gap-2" to="/tickers" @click="closeMenusAfterNavigate">
                      <MaterialIcon name="trending_up" size="1.125rem" />
                      티커 정보
                    </router-link>
                  </li>

                  <li v-if="authStore.isAdmin"><hr class="dropdown-divider"></li>
                  <li v-if="authStore.isAdmin">
                    <router-link class="dropdown-item d-flex align-items-center gap-2" to="/settings/schedule" @click="closeMenusAfterNavigate">
                      <MaterialIcon name="schedule" size="1.125rem" />
                      크롤링 스케줄
                    </router-link>
                  </li>
                  <li v-if="authStore.isAdmin">
                    <router-link class="dropdown-item d-flex align-items-center gap-2" to="/users" @click="closeMenusAfterNavigate">
                      <MaterialIcon name="group" size="1.125rem" />
                      멤버 관리
                    </router-link>
                  </li>
                  <li v-if="authStore.isAdmin">
                    <router-link class="dropdown-item d-flex align-items-center gap-2" to="/logs" @click="closeMenusAfterNavigate">
                      <MaterialIcon name="description" size="1.125rem" />
                      시스템 로그
                    </router-link>
                  </li>
                </ul>
              </li>
            </template>
          </ul>
          <div class="d-flex align-items-center gap-2">
            <template v-if="authStore.isAuthenticated">
            <button
              type="button"
              class="btn btn-theme-toggle rounded-circle d-inline-flex align-items-center justify-content-center p-0 me-ms-2 me-1"
              @click="toggleTheme"
              :aria-label="isDarkTheme ? '라이트 모드로 전환' : '다크 모드로 전환'"
              :title="isDarkTheme ? '라이트 모드' : '다크 모드'"
              style="width: 36px; height: 36px;"
            >
              <MaterialIcon :name="isDarkTheme ? 'light_mode' : 'dark_mode'" size="1.2rem" />
            </button>
            </template>
            <template v-if="authStore.isAuthenticated">
              <div class="d-flex align-items-center gap-2 me-1">
                <span class="badge bg-light text-secondary rounded-pill fw-bold border" style="font-size: 0.65rem; padding: 0.2rem 0.5rem; letter-spacing: 0.02em;">LV.{{ authStore.user?.level || 1 }}</span>
                <span class="text-muted fw-bold small">{{ authStore.user?.username }}</span>
              </div>
              <button type="button" class="btn nav-action-btn btn-sm" @click="handleLogout">로그아웃</button>
            </template>
            <template v-else>
              <router-link to="/login" class="btn btn-link text-muted hover-primary text-decoration-none p-0 small me-3" @click="closeMobileNavIfNeeded">로그인</router-link>
              <router-link to="/register" class="btn nav-action-btn-primary btn-sm px-3" @click="closeMobileNavIfNeeded">가입</router-link>
            </template>
          </div>
        </div>
      </div>
    </nav>

    <main class="stock-container pb-5">
      <div v-if="networkState.slowRequests > 0" class="alert alert-warning py-2 mb-3" role="status">
        서버 응답이 지연되고 있습니다. 데이터를 불러오는 중입니다.
      </div>
      <div
        v-if="networkState.lastErrorMessage"
        class="alert alert-danger alert-dismissible fade show py-2 mb-3"
        role="alert"
      >
        {{ networkState.lastErrorMessage }}
        <button type="button" class="btn-close" @click="networkState.lastErrorMessage = ''" aria-label="닫기"></button>
      </div>
      <div v-if="flash.message" :class="['alert', 'alert-dismissible', 'fade', 'show', flash.category || 'alert-info']" role="alert">
        {{ flash.message }}
        <button type="button" class="btn-close" @click="flash.message = ''" aria-label="닫기"></button>
      </div>
      <router-view v-slot="{ Component }">
        <component :is="Component" @flash="setFlash" />
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { authStore } from './stores/auth'
import { authApi, userApi } from './api'
import { networkState } from './stores/network'
import { applyCachedSiteColor, repaintSiteColor, setSiteColorLocal, isValidHexColor } from './stores/siteColor'

const router = useRouter()
const route = useRoute()
const flash = reactive({ message: '', category: 'alert-info' })
const isSettingsOpen = ref(false)
const isMobileNavOpen = ref(false)
const settingsMenuRef = ref(null)
const themeMode = ref('light')
const isDarkTheme = computed(() => themeMode.value === 'dark')
const THEME_STORAGE_KEY = 'stock_theme_mode'
let themeMediaQuery = null
let flashTimer = null
let networkErrorTimer = null

watch(() => networkState.lastErrorMessage, (newMsg) => {
  if (newMsg) {
    if (networkErrorTimer) clearTimeout(networkErrorTimer)
    networkErrorTimer = setTimeout(() => {
      networkState.lastErrorMessage = ''
    }, 5000)
  }
})

function toggleSettingsMenu() {
  isSettingsOpen.value = !isSettingsOpen.value
}

function closeSettingsMenu() {
  isSettingsOpen.value = false
}

function isMobileViewport() {
  return typeof window !== 'undefined' && window.innerWidth < 992
}

function toggleMobileNav() {
  if (!isMobileViewport()) return
  isMobileNavOpen.value = !isMobileNavOpen.value
}

function closeMobileNavIfNeeded() {
  if (!isMobileViewport()) return
  isMobileNavOpen.value = false
}

function closeMenusAfterNavigate() {
  closeSettingsMenu()
  closeMobileNavIfNeeded()
}

function handleClickOutside(event) {
  const root = settingsMenuRef.value
  if (!root) return
  if (!root.contains(event.target)) {
    closeSettingsMenu()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside, true)
  applyTheme(detectInitialTheme())
  applyCachedSiteColor()
  themeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
  themeMediaQuery.addEventListener('change', handleSystemThemeChange)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside, true)
  if (themeMediaQuery) {
    themeMediaQuery.removeEventListener('change', handleSystemThemeChange)
  }
})

watch(() => route.fullPath, () => {
  closeSettingsMenu()
  isMobileNavOpen.value = false
})

function setFlash(msg, category = 'alert-info') {
  flash.message = msg
  flash.category = category
  if (flashTimer) clearTimeout(flashTimer)
  flashTimer = setTimeout(() => {
    flash.message = ''
  }, 5000)
}

function applyTheme(mode) {
  themeMode.value = mode === 'dark' ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', themeMode.value)
  document.documentElement.setAttribute('data-bs-theme', themeMode.value)
  // 다크/라이트 전환 시 사이트 컬러도 해당 모드에 맞게 재보정
  repaintSiteColor()
}

function detectInitialTheme() {
  if (!authStore.isAuthenticated) {
    return 'light'
  }
  const saved = localStorage.getItem(THEME_STORAGE_KEY)
  if (saved === 'dark' || saved === 'light') {
    return saved
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function toggleTheme() {
  const next = isDarkTheme.value ? 'light' : 'dark'
  applyTheme(next)
  localStorage.setItem(THEME_STORAGE_KEY, next)
  if (authStore.isAuthenticated) {
    userApi.savePreferences({ theme: next }).catch(err => {
      console.warn('Failed to save theme to server:', err)
    })
  }
}

function handleSystemThemeChange(event) {
  if (!authStore.isAuthenticated) {
    applyTheme('light')
    return
  }
  const saved = localStorage.getItem(THEME_STORAGE_KEY)
  if (saved === 'dark' || saved === 'light') return
  applyTheme(event.matches ? 'dark' : 'light')
}

watch(() => authStore.isAuthenticated, async (isAuthenticated) => {
  if (!isAuthenticated) {
    applyTheme('light')
    setSiteColorLocal('')
    return
  }

  // 서버에서 테마/컬러 설정 가져오기
  try {
    const { data } = await userApi.getPreferences()
    const serverTheme = data.preferences?.theme
    if (serverTheme === 'dark' || serverTheme === 'light') {
      applyTheme(serverTheme)
      localStorage.setItem(THEME_STORAGE_KEY, serverTheme)
    } else {
      applyTheme(detectInitialTheme())
    }

    const serverSiteColor = data.preferences?.site_color
    setSiteColorLocal(isValidHexColor(serverSiteColor) ? serverSiteColor : '')
  } catch (e) {
    console.warn('Failed to fetch theme preferences:', e)
    applyTheme(detectInitialTheme())
  }
})

async function handleLogout() {
  try {
    await authApi.logout()
    authStore.clearUser()
    isMobileNavOpen.value = false
    closeSettingsMenu()
    router.push('/login')
  } catch (e) {
    console.error('Logout failed', e)
  }
}
</script>

<style scoped>
.btn-theme-toggle {
  border: 1px solid var(--ui-border);
  background: var(--ui-surface-soft);
  color: var(--ui-text-muted);
  transition: all 0.2s ease;
}

.btn-theme-toggle:hover {
  border-color: var(--ui-primary);
  color: var(--ui-primary);
  background: var(--ui-primary-soft);
  transform: rotate(15deg) scale(1.05);
}
</style>
