import { createRouter, createWebHistory } from 'vue-router'
import { authStore } from '../stores/auth'
import { authApi } from '../api'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { title: '로그인' } },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue'), meta: { title: '회원가입' } },
  { path: '/', name: 'Dashboard', component: () => import('../views/MainDashboard.vue'), meta: { title: 'Dashboard' } },
  { path: '/tickers', name: 'Tickers', component: () => import('../views/StockDashboard.vue'), meta: { title: '전체 티커 정보', requiresAuth: true } },
  { path: '/balances', name: 'Balances', component: () => import('../views/BalanceList.vue'), meta: { title: '계좌 잔고' } },
  { path: '/balances/:accountId', name: 'BalanceDetail', component: () => import('../views/BalanceDetail.vue'), meta: { title: '계좌 상세' } },
  { path: '/balances/history/:accountId', name: 'BalanceHistoryDetail', component: () => import('../views/BalanceHistoryDetail.vue'), meta: { title: '자산 추이 상세' } },
  { path: '/accounts', name: 'AccountManager', component: () => import('../views/AccountManager.vue'), meta: { title: '계좌 정보 설정', requiresAuth: true } },
  { path: '/my-account', name: 'MyAccount', component: () => import('../views/MyAccount.vue'), meta: { title: '내 계정 정보', requiresAuth: true } },
  { path: '/accounts/:accountId', name: 'AccountDetail', component: () => import('../views/AccountDetail.vue'), meta: { title: '계좌 상세 정보', requiresAuth: true } },
  { path: '/transactions', redirect: '/accounts' },
  { path: '/portfolios', name: 'Portfolios', component: () => import('../views/PortfolioManager.vue'), meta: { title: '포트폴리오 관리', requiresAuth: true } },
  { path: '/portfolios/:portfolioId', name: 'PortfolioDetail', component: () => import('../views/PortfolioDetail.vue'), meta: { title: '포트폴리오 상세', requiresAuth: true } },
  { path: '/site-guide', name: 'SiteGuide', component: () => import('../views/SiteGuide.vue'), meta: { title: '사이트 안내' } },
  { path: '/board/:postId', name: 'BoardDetail', component: () => import('../views/BoardDetail.vue'), meta: { title: '게시물 상세' } },
  { path: '/user-manual', name: 'UserManual', component: () => import('../views/UserManual.vue'), meta: { title: '사용자 매뉴얼' } },
  { path: '/settings/schedule', name: 'ScheduleSettings', component: () => import('../views/ScheduleSettings.vue'), meta: { title: '크롤링 스케줄', requiresAuth: true, requiresAdmin: true } },
  { path: '/users', name: 'MemberManagement', component: () => import('../views/MemberManagement.vue'), meta: { title: '멤버 관리', requiresAuth: true, requiresAdmin: true } },
  { path: '/logs', name: 'Logs', component: () => import('../views/LogViewer.vue'), meta: { title: '시스템 로그', requiresAuth: true, requiresAdmin: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (authStore.loading) {
    try {
      const { data } = await authApi.me({ timeout: 5000 })
      if (data.logged_in) {
        authStore.setUser(data.user)
      } else {
        authStore.clearUser()
      }
    } catch (e) {
      authStore.clearUser()
    }
  }

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.meta.requiresAdmin && !authStore.isAdmin) {
    next('/')
  } else if ((to.name === 'Login' || to.name === 'Register') && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} - 주식 정보 시스템` : '주식 정보 시스템'
})

export default router
