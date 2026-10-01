import { reactive } from 'vue'

/**
 * 사이트 전체 브랜드 컬러(--ui-primary 등) 사용자 지정 테마.
 * App.vue(부팅 시 적용/테마 전환 시 재적용)와 MyAccount.vue(설정 화면)가 이 상태 하나를 공유한다.
 */

export const SITE_COLOR_PRESETS = [
  { id: 'pine', name: '파인 그린', hex: '#1f6f54' },
  { id: 'blue', name: '블루', hex: '#2563eb' },
  { id: 'violet', name: '바이올렛', hex: '#7c3aed' },
  { id: 'amber', name: '앰버', hex: '#b45309' },
  { id: 'rose', name: '로즈', hex: '#be123c' },
  { id: 'slate', name: '슬레이트', hex: '#475569' },
]

const STORAGE_KEY = 'stock_site_color'
const HEX_RE = /^#[0-9a-fA-F]{6}$/
const PRIMARY_VARS = ['--ui-primary', '--ui-primary-hover', '--ui-primary-soft', '--ui-focus-ring', '--ui-link', '--ui-link-hover']

export function isValidHexColor(hex) {
  return typeof hex === 'string' && HEX_RE.test(hex)
}

export const siteColorState = reactive({
  hex: '',
})

/** 문서 루트 CSS 변수에 실제로 반영(다크 모드에서는 더 밝은 톤으로 자동 보정) */
function paint(hex) {
  const root = document.documentElement
  if (!isValidHexColor(hex)) {
    PRIMARY_VARS.forEach((name) => root.style.removeProperty(name))
    return
  }
  const isDark = root.getAttribute('data-theme') === 'dark'
  const base = isDark ? `color-mix(in srgb, ${hex} 62%, white)` : hex
  root.style.setProperty('--ui-primary', base)
  root.style.setProperty('--ui-primary-hover', `color-mix(in srgb, ${base} 84%, black)`)
  root.style.setProperty('--ui-primary-soft', `color-mix(in srgb, ${base} ${isDark ? 16 : 10}%, transparent)`)
  root.style.setProperty('--ui-focus-ring', `color-mix(in srgb, ${base} ${isDark ? 32 : 22}%, transparent)`)
  root.style.setProperty('--ui-link', base)
  root.style.setProperty('--ui-link-hover', `color-mix(in srgb, ${base} 84%, black)`)
}

/** 현재 다크/라이트 모드 기준으로 저장된 색을 다시 칠한다(테마 전환 시 호출) */
export function repaintSiteColor() {
  paint(siteColorState.hex)
}

/** localStorage 캐시만 적용(로그인 확인 전 초기 페인트용) */
export function applyCachedSiteColor() {
  siteColorState.hex = localStorage.getItem(STORAGE_KEY) || ''
  paint(siteColorState.hex)
}

/** 서버 동기화 없이 즉시 반영 + 로컬 캐시(설정 화면에서 실시간 미리보기용) */
export function setSiteColorLocal(hex) {
  const value = isValidHexColor(hex) ? hex : ''
  siteColorState.hex = value
  if (value) {
    localStorage.setItem(STORAGE_KEY, value)
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
  paint(value)
}

