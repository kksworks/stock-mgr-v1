import axios from 'axios'
import {
  beginNetworkRequest,
  markSlowNetworkRequest,
  endNetworkRequest,
  notifyNetworkError,
} from './stores/network'

const DEFAULT_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 15000)
const SLOW_REQUEST_MS = Number(import.meta.env.VITE_API_SLOW_MS || 2500)
const RETRYABLE_STATUS = new Set([502, 503, 504])

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
  timeout: DEFAULT_TIMEOUT_MS,
})

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function shouldRetry(error, config) {
  if (!config || config.__retryAttempted) return false
  const status = error?.response?.status
  if (error?.code === 'ECONNABORTED') return true
  if (!error?.response) return true
  return RETRYABLE_STATUS.has(status)
}

export function getApiErrorMessage(error, fallback = '요청 처리 중 오류가 발생했습니다.') {
  if (!error) return fallback
  if (axios.isCancel(error) || error.code === 'ERR_CANCELED') return '요청이 취소되었습니다.'
  if (error.code === 'ECONNABORTED') return '서버 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.'
  if (!error.response) return '서버에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요.'

  const status = error.response.status
  const serverMsg = error.response?.data?.message || error.response?.data?.error
  if (serverMsg) return serverMsg

  if (status === 401) return '로그인이 필요하거나 세션이 만료되었습니다.'
  if (status === 403) return '요청 권한이 없습니다.'
  if (status === 404) return '요청한 데이터를 찾을 수 없습니다.'
  if (status >= 500) return '서버 처리 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.'
  return fallback
}

// Request Logger + Network State Interceptor
api.interceptors.request.use((config) => {
  const method = (config.method || 'GET').toUpperCase()
  const url = config.url || ''
  console.log(`[API Request] ${method} ${url}`, config.params || '', config.data || '')
  beginNetworkRequest()
  const reqMeta = {
    slowMarked: false,
    slowTimer: null,
  }
  reqMeta.slowTimer = window.setTimeout(() => {
    reqMeta.slowMarked = true
    markSlowNetworkRequest()
  }, SLOW_REQUEST_MS)
  config.__reqMeta = reqMeta
  return config
}, (error) => {
  console.error('[API Request Error]', error)
  notifyNetworkError(getApiErrorMessage(error))
  return Promise.reject(error)
})

async function finalizeResponse(responseOrErrorConfig) {
  const reqMeta = responseOrErrorConfig?.__reqMeta
  if (reqMeta?.slowTimer) {
    window.clearTimeout(reqMeta.slowTimer)
  }
  endNetworkRequest({ wasSlow: Boolean(reqMeta?.slowMarked) })
}

// Response Logger Interceptor
api.interceptors.response.use((response) => {
  const status = response.status
  const url = response.config?.url || ''
  console.log(`[API Response] ${status} ${url}`, response.data)
  finalizeResponse(response.config)
  return response
}, async (error) => {
  const config = error.config || {}
  const status = error.response?.status || 'Network Error'
  const url = config?.url || 'unknown'
  console.error(`[API Response Error] ${status} ${url}`, error.response?.data || error.message)

  // Idempotent 성격의 요청에 대해 1회 자동 재시도 (지연/일시 오류 완화)
  if ((config.method || 'get').toLowerCase() === 'get' && shouldRetry(error, config)) {
    finalizeResponse(config)
    config.__retryAttempted = true
    await sleep(250)
    return api.request(config)
  }
  finalizeResponse(config)
  if (!(axios.isCancel(error) || error.code === 'ERR_CANCELED')) {
    notifyNetworkError(getApiErrorMessage(error))
  }
  return Promise.reject(error)
})

export default api

export const userApi = {
  getPreferences: (options = {}) => api.get('/user/preferences', options),
  savePreferences: (data, options = {}) => api.put('/user/preferences', data, options),
}

export const authApi = {
  register: (data, options = {}) => api.post('/register', data, options),
  login: (data, options = {}) => api.post('/login', data, options),
  logout: (options = {}) => api.post('/logout', {}, options),
  me: (options = {}) => api.get('/me', options),
  getUsers: (options = {}) => api.get('/users', options),
  getMyApiKeyInfo: (options = {}) => api.get('/user/api-key', options),
  issueMyApiKey: (options = {}) => api.post('/user/api-key', {}, options),
  changeMyPassword: (data, options = {}) => api.post('/user/change-password', data, options),
  updateProfile: (data, options = {}) => api.post('/user/update-profile', data, options),
  /** 관리자: 사용자 비밀번호 강제 설정 */
  resetUserPassword: (data, options = {}) => api.post('/users/reset-password', data, options),
  /** 관리자: 사용자 레벨 지정 (1~5) */
  updateUserLevel: (data, options = {}) => api.post('/users/update-level', data, options),
}

export const stockApi = {
  getTickers: (q, options = {}) => api.get('/tickers', { params: { q }, ...options }),
  getTickerDetail: (ticker, options = {}) => api.get(`/tickers/${ticker}`, options),
  crawl: (options = {}) => api.post('/crawl', {}, options),
  getTickerPrices: (tickers, options = {}) => api.get('/tickers/prices', { params: { tickers: tickers.join(',') }, ...options }),
  addField: (ticker, fieldName, fieldValue, options = {}) =>
    api.post('/add_field', { ticker, field_name: fieldName, field_value: fieldValue }, options),
  updateAssetClass: (ticker, assetClass, options = {}) =>
    api.post(`/tickers/${ticker}/asset_class`, { asset_class: assetClass }, options),
}

export const accountApi = {
  getAccounts: (options = {}) => api.get('/accounts', options),
  getAccount: (id, options = {}) => api.get(`/accounts/${id}`, options),
  updateAccount: (data, options = {}) => api.post('/accounts', data, options),
  deleteAccount: (id, options = {}) => api.delete(`/accounts/${id}`, options),
  getTransactions: (accountId, params = {}, options = {}) => api.get('/transactions', { params: { account_id: accountId, ...params }, ...options }),
  saveTransaction: (data, options = {}) => api.post('/transactions', data, options),
  deleteTransaction: (id, options = {}) => api.delete(`/transactions/${id}`, options),
  getBalances: (options = {}) => api.get('/balances', options),
  getBalancesOverview: (options = {}) => api.get('/balances/overview', options),
  /** 강제 현재가 갱신. body: { account_id? } — 없으면 접근 가능한 전체 계좌 */
  refreshBalances: (data = {}, options = {}) => api.post('/balances/refresh', data, options),
  refreshAllBalances: (options = {}) => api.post('/balances/refresh-all', {}, options),
  getBalanceDetail(accountId, options = {}) {
    return api.get(`/balances/detail?account_id=${accountId}`, options);
  },
  fetchBalanceHistory(accountId, startDate, endDate, rebalancedOnly = false, options = {}) {
    let url = `/balances/history?account_id=${accountId}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    if (rebalancedOnly) url += `&rebalanced_only=true`;
    return api.get(url, options);
  },
  /** balance_history 컬렉션 해당 일자 문서 원시 JSON (동일 날짜 복수 건이면 documents 배열) */
  fetchBalanceHistoryRaw(accountId, date, options = {}) {
    return api.get('/balances/history/raw', {
      params: { account_id: accountId, date },
      ...options,
    });
  },
  updateBalance(data, options = {}) {
    return api.post('/balances/update', data, options);
  },
}

export const portfolioApi = {
  getPortfolios: (options = {}) => api.get('/portfolios', options),
  savePortfolio: (data, options = {}) => api.post('/portfolios', data, options),
  deletePortfolio: (id, options = {}) => api.delete(`/portfolios/${id}`, options),
  searchTicker: (q, options = {}) => api.get('/portfolios/search_ticker', { params: { q }, ...options }),
  getPortfolio: (id, options = {}) => api.get(`/portfolios/${id}`, options),
  getAssetClasses: (options = {}) => api.get('/portfolios/asset_classes', options),
  updateAssetClasses: (classes, options = {}) => api.post('/portfolios/asset_classes', { classes }, options),
}

export const systemApi = {
  getLogs: (options = {}) => api.get('/logs', options),
  clearLogs: (options = {}) => api.post('/logs/clear', {}, options),
  getSchedule: (options = {}) => api.get('/settings/schedule', options),
  updateSchedule: (data, options = {}) => api.put('/settings/schedule', data, options),
  getPriceSettings: (options = {}) => api.get('/settings/price', options),
  updatePriceSettings: (data, options = {}) => api.put('/settings/price', data, options),
  getSiteGuide: (options = {}) => api.get('/settings/site-guide', options),
  updateSiteGuide: (data, options = {}) => api.put('/settings/site-guide', data, options),
}

export const scheduleApi = {
  getSchedule: (options = {}) => api.get('/settings/schedule', options),
  updateSchedule: (data, options = {}) => api.put('/settings/schedule', data, options),
  getPortfolioSchedule: (options = {}) => api.get('/settings/schedule/portfolio', options),
  updatePortfolioSchedule: (data, options = {}) => api.put('/settings/schedule/portfolio', data, options),
  getPriceSettings: (options = {}) => api.get('/settings/price', options),
  updatePriceSettings: (data, options = {}) => api.put('/settings/price', data, options),
  runRefreshNow: (options = {}) => api.post('/balances/refresh-all-admin', {}, options),
  runPortfolioRefreshNow: (options = {}) => api.post('/portfolios/refresh-all-admin', {}, options),
}

export const boardApi = {
  listPosts: (page = 1, options = {}) => api.get('/board/posts', { params: { page }, ...options }),
  getPost: (postId, options = {}) => api.get(`/board/posts/${postId}`, options),
  createPost: (data, options = {}) => api.post('/board/posts', data, options),
  updatePost: (postId, data, options = {}) => api.put(`/board/posts/${postId}`, data, options),
  deletePost: (postId, options = {}) => api.delete(`/board/posts/${postId}`, options),
  togglePin: (postId, options = {}) => api.put(`/board/posts/${postId}/toggle-pin`, {}, options),
}
