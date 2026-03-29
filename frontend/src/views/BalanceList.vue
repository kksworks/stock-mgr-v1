<template>
  <div class="balance-list-root stock-theme pb-5 px-3 px-md-4">
    <div class="d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center gap-2 mb-4 mt-3">
      <h1 class="mb-0 d-flex align-items-center gap-2 h4 fw-bold balance-page-title">
        <MaterialIcon name="account_balance_wallet" size="2rem" class="text-primary opacity-90" />
        계좌 잔고
      </h1>
      <div class="btn-group-wrap d-flex flex-wrap align-items-center gap-2">
        <button
          v-if="authStore.isAuthenticated"
          type="button"
          class="btn btn-sm btn-tonal-neutral d-inline-flex align-items-center gap-1"
          :disabled="refreshing"
          @click="doRefresh"
        >
          <MaterialIcon name="sync" size="1.1rem" :class="{ 'rotate-animation': refreshing }" />
          <span class="d-none d-sm-inline">{{ refreshing ? '갱신 중…' : '현재가 갱신' }}</span>
          <span class="d-sm-none">갱신</span>
        </button>
        <router-link class="btn btn-sm btn-tonal-neutral d-inline-flex align-items-center gap-1" to="/accounts">
          <MaterialIcon name="settings" size="1.1rem" />
          <span class="d-none d-sm-inline">계좌 관리</span>
          <span class="d-sm-none">관리</span>
        </router-link>
      </div>
    </div>

    <!-- Status Bar (대시보드 상태바와 동일 톤) -->
    <div class="d-flex align-items-center justify-content-between mb-4 balance-list-status-bar small">
      <div class="text-muted d-flex align-items-center gap-1 ms-1 flex-wrap balance-list-status-text">
        <MaterialIcon name="info" size="0.85rem" />
        <span>잔고와 상세 내용을 확인하고 포트폴리오를 관리할 계좌를 선택하세요.</span>
        <template v-if="listOldestPriceAgeText">
          <span class="ms-1">·</span>
          <MaterialIcon name="history" size="0.85rem" />
          <span class="fw-medium">업데이트: {{ listOldestPriceUpdatedAtLabel }} ({{ listOldestPriceAgeText }})</span>
        </template>
      </div>
      <div class="d-flex align-items-center gap-3 me-2">
        <span v-if="!loading" class="text-muted d-none d-md-inline fw-medium" style="font-size: 0.75rem;">총 {{ overview.length }}개 계좌</span>
        <div v-if="loading || refreshing" class="spinner-border spinner-border-sm text-primary" role="status" style="width: 0.75rem; height: 0.75rem;"></div>
      </div>
    </div>

    <PageLoadingPlaceholder v-if="loading && overview.length === 0" variant="lines" :rows="7" />
    
    <div v-else-if="overview.length === 0 && !loading" class="card shadow-sm border-0 rounded-4 my-5 stock-fade-in">
      <div class="card-body text-center py-5 text-muted">
        <MaterialIcon name="account_balance" size="3rem" class="opacity-10 mb-3" />
        <p class="mb-0 text-secondary">등록된 계좌가 없습니다. <br/><router-link to="/accounts" class="fw-bold text-primary text-decoration-none border-bottom">계좌 관리</router-link>에서 먼저 계좌를 추가해 주세요.</p>
      </div>
    </div>

    <div v-else class="row g-4 stock-fade-in">
      <!-- 나의 계좌 그룹 -->
      <div v-if="myAccounts.length > 0" class="col-12">
        <div class="px-2 py-1 small fw-bold text-muted d-flex align-items-center gap-1 mb-3 opacity-75 text-uppercase letter-spacing-1">
          <MaterialIcon name="person" size="1.1rem" class="text-primary" />
          나의 계좌 ({{ myAccounts.length }})
        </div>

        <div
          v-for="group in myAccountTagGroups"
          :key="group.tag"
          class="mb-5 balance-tag-section"
          :style="{ '--balance-tag-accent': getThemeColorByTag(group.tag) }"
        >
          <!-- 태그(분류)별 레일 + 요약: 같은 태그 계좌가 한 묶음으로 보이도록 -->
          <div
            class="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center p-3 p-md-4 mb-4 rounded-4 border balance-group-summary"
            :class="{ 'balance-group-summary--expanded': isTagExpanded(group.tag) }"
            :style="{ 
              background: 'var(--ui-surface)', 
              borderColor: 'var(--ui-border)', 
              borderTop: `2px solid ${getThemeColorByTag(group.tag)}` 
            }"
            role="button"
            tabindex="0"
            @click="toggleTagExpanded(group.tag)"
            @keydown.enter.prevent="toggleTagExpanded(group.tag)"
            @keydown.space.prevent="toggleTagExpanded(group.tag)"
          >
            <div class="d-flex align-items-center gap-3 mb-3 mb-lg-0">
               <div
                 class="p-2 rounded-circle d-flex align-items-center justify-content-center balance-group-icon-ring"
                 :style="{ background: 'var(--ui-surface)', color: getThemeColorByTag(group.tag), border: `2px solid ${getThemeColorByTag(group.tag)}` }"
               >
                 <MaterialIcon name="label" size="1.5rem" weight="700" />
               </div>
               <div class="d-flex flex-column">
                 <div class="d-flex align-items-center gap-2 flex-wrap">
                    <span class="balance-group-flag-label rounded-pill" :style="{ borderColor: getThemeColorByTag(group.tag), color: getThemeColorByTag(group.tag) }">
                      <MaterialIcon name="flag" size="0.7rem" class="balance-group-flag-icon" />
                      TAG
                    </span>
                    <span class="balance-group-tag-title">{{ group.tag }}</span>
                 </div>
                 <span class="balance-group-subtitle">{{ group.items.length }}개 계좌 · 같은 TAG 멤버</span>
               </div>
            </div>
            
            <div class="d-flex flex-wrap align-items-center gap-4 gap-lg-5">
               <div class="d-flex flex-column text-lg-end">
                 <span class="text-muted fw-bold text-uppercase opacity-75" style="font-size: 0.65rem; letter-spacing: 0.05em;">그룹 총 자산</span>
                 <span class="fw-bold tabular-nums h5 mb-0" style="color: var(--ui-text);">₩{{ Math.round(group.totalAsset).toLocaleString() }}</span>
               </div>
               <div class="d-flex flex-column text-lg-end border-start ps-4 border-light-subtle">
                 <span class="text-muted fw-bold text-uppercase opacity-75" style="font-size: 0.65rem; letter-spacing: 0.05em;">누적 손익</span>
                 <div class="d-flex align-items-center gap-2 fw-bold tabular-nums" :class="group.totalReturn >= 0 ? 'text-profit' : 'text-loss'">
                    <span>{{ group.totalReturn >= 0 ? '+' : '' }}₩{{ Math.round(group.totalReturn).toLocaleString() }}</span>
                    <span class="small opacity-75" style="font-size: 0.75rem;">({{ group.returnRate.toFixed(1) }}%)</span>
                 </div>
               </div>
               <button
                 type="button"
                 class="btn balance-group-accordion-btn ms-lg-2"
                 @click.stop="toggleTagExpanded(group.tag)"
                 :aria-label="`${group.tag} 그룹 펼치기/접기`"
               >
                 <MaterialIcon :name="isTagExpanded(group.tag) ? 'keyboard_arrow_up' : 'keyboard_arrow_down'" size="1.35rem" />
                 <span class="ms-1">{{ isTagExpanded(group.tag) ? '멤버 접기' : '멤버 펼치기' }}</span>
               </button>
            </div>
          </div>
          
          <div v-show="isTagExpanded(group.tag)" class="row g-0 balance-card-stack balance-group-members">
            <div v-for="acc in group.items" :key="acc.account.id" class="col-12 balance-card-stack-item">
              <div
                class="card border-0 rounded-4 cursor-pointer balance-acc-card overflow-hidden position-relative"
                @click="goToDetail(acc.account.id)"
                :style="{ borderLeft: `4px solid ${getThemeColorByTag(group.tag)}` }"
              >
                <div class="card-body p-3 p-md-4 pt-4">
                  <!-- Account Header -->
                  <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-3 pb-3 border-bottom border-light-subtle">
                    <div class="d-flex align-items-center gap-3">
                      <div
                        class="rounded-circle d-flex align-items-center justify-content-center balance-acc-icon-ring balance-acc-icon-ring--md"
                        :style="{ background: 'var(--ui-surface)', color: getThemeColorByTag(group.tag), border: `1px solid ${getThemeColorByTag(group.tag)}` }"
                      >
                        <MaterialIcon name="account_balance" size="1.35rem" weight="300" />
                      </div>
                      <div>
                        <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
                          <h5 class="fw-semibold mb-0" style="font-size: 0.95rem; letter-spacing: -0.01em; color: var(--ui-text-subtle);">{{ acc.account.account_name }}</h5>
                          <span class="badge rounded-pill" :style="{ background: 'transparent', border: `1px solid ${getThemeColorByTag(group.tag)}`, color: getThemeColorByTag(group.tag), fontSize: '0.65rem', padding: '0.1rem 0.4rem', fontWeight: '500' }">
                            {{ group.tag }}
                          </span>
                        </div>
                        <div class="d-flex align-items-center gap-2 flex-wrap">
                          <span class="text-muted small fw-medium" style="font-size: 0.8rem;">{{ acc.account.account_number }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="d-flex align-items-center gap-4 text-end ms-md-auto">
                      <div class="d-flex flex-column">
                        <span class="text-muted small fw-bold text-uppercase opacity-75" style="font-size: 0.65rem;">현재 평가 자산</span>
                        <span class="fw-bold tabular-nums text-success h5 mb-0">₩{{ Number(acc.total_asset_value || 0).toLocaleString() }}</span>
                      </div>
                      <div v-if="acc.prev_day_asset_change != null" class="d-flex flex-column align-items-end">
                        <span class="text-muted small fw-bold text-uppercase opacity-75" style="font-size: 0.65rem;">전일 대비</span>
                        <div class="d-flex align-items-center gap-1 fw-bold" :class="prevDayChangeClass(acc.prev_day_asset_change)" style="font-size: 0.9rem;">
                           <MaterialIcon :name="acc.prev_day_asset_change >= 0 ? 'arrow_drop_up' : 'arrow_drop_down'" size="1.1rem" />
                           <span class="tabular-nums">{{ formatPrevDayMoney(acc.prev_day_asset_change) }}</span>
                           <span class="opacity-75" style="font-size: 0.72rem;">({{ formatPrevDayPercent(acc.prev_day_return_vs_principal_pct) }})</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Quick Stats Grid -->
                  <div class="row g-3">
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">투자 원금</span>
                        <span class="fw-bold tabular-nums small">₩{{ Number(acc.principal || 0).toLocaleString() }}</span>
                      </div>
                    </div>
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">평가 손익</span>
                        <span class="fw-bold tabular-nums small" :class="(acc.investment_return || 0) >= 0 ? 'text-profit' : 'text-loss'">
                          {{ (acc.investment_return || 0) >= 0 ? '+' : '' }}₩{{ Number(Math.abs(acc.investment_return || 0)).toLocaleString() }}
                        </span>
                      </div>
                    </div>
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">수익률(ROI)</span>
                        <span class="fw-bold tabular-nums small" :class="(acc.investment_return || 0) >= 0 ? 'text-profit' : 'text-loss'">
                          {{ (acc.investment_return || 0) >= 0 ? '+' : '' }}{{ (acc.principal > 0 ? (acc.investment_return / acc.principal * 100) : 0).toFixed(2) }}%
                        </span>
                      </div>
                    </div>
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">업데이트</span>
                        <span class="text-muted x-small fw-medium">{{ formatAgeMinutes(Number(acc.oldest_price_age_minutes)) || '-' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="sharedAccounts.length > 0" class="col-12 mt-5">
        <div class="balance-tag-section mb-5" :style="{ '--balance-tag-accent': 'var(--ui-text-muted)' }">
          <!-- Group Header for Shared Accounts -->
          <div
            class="d-flex flex-column flex-lg-row justify-content-between align-items-lg-center p-3 p-md-4 mb-4 rounded-4 border balance-group-summary"
            :class="{ 'balance-group-summary--expanded': isTagExpanded('__shared__') }"
            role="button"
            tabindex="0"
            @click="toggleTagExpanded('__shared__')"
            @keydown.enter.prevent="toggleTagExpanded('__shared__')"
            @keydown.space.prevent="toggleTagExpanded('__shared__')"
          >
            <div class="d-flex align-items-center gap-3">
               <div
                 class="p-2 rounded-circle d-flex align-items-center justify-content-center balance-group-icon-ring"
                 :style="{ background: 'var(--ui-surface)', color: 'var(--ui-text-muted)', border: '1px solid var(--ui-border)' }"
               >
                 <MaterialIcon name="group" size="1.5rem" weight="700" />
               </div>
               <div class="d-flex flex-column">
                 <div class="d-flex align-items-center gap-2 flex-wrap">
                    <span class="balance-group-tag-title">공유받은 계좌</span>
                 </div>
                 <span class="balance-group-subtitle">{{ sharedAccounts.length }}개 계좌</span>
               </div>
            </div>
            
            <div class="d-flex align-items-center gap-4">
               <button
                 type="button"
                 class="btn balance-group-accordion-btn ms-lg-2"
                 @click.stop="toggleTagExpanded('__shared__')"
                 :aria-label="`공유받은 계좌 펼치기/접기`"
               >
                 <MaterialIcon :name="isTagExpanded('__shared__') ? 'keyboard_arrow_up' : 'keyboard_arrow_down'" size="1.35rem" />
                 <span class="ms-1">{{ isTagExpanded('__shared__') ? '멤버 접기' : '멤버 펼치기' }}</span>
               </button>
            </div>
          </div>

          <div v-show="isTagExpanded('__shared__')" class="row g-0 balance-card-stack balance-group-members">
            <div v-for="acc in sharedAccounts" :key="acc.account.id" class="col-12 balance-card-stack-item">
              <div
                class="card border-0 rounded-4 cursor-pointer balance-acc-card overflow-hidden position-relative"
                @click="goToDetail(acc.account.id)"
                :style="{ borderLeft: `6px solid ${getThemeColorByTag(sharedTagLabel(acc))}` }"
              >
                <div class="card-body p-3 p-md-4 pt-4">
                  <!-- Header: Icon, Name, Total Asset -->
                  <div class="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3 mb-3 pb-3 border-bottom border-light-subtle">
                    <div class="d-flex align-items-center gap-3">
                      <div
                        class="rounded-circle d-flex align-items-center justify-content-center balance-acc-icon-ring balance-acc-icon-ring--md"
                        :style="{ background: 'var(--ui-surface)', color: getThemeColorByTag(sharedTagLabel(acc)), border: `1px solid ${getThemeColorByTag(sharedTagLabel(acc))}` }"
                      >
                        <MaterialIcon name="account_balance" size="1.35rem" weight="300" />
                      </div>
                      <div>
                        <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
                          <h5 class="fw-semibold mb-0" style="font-size: 0.93rem; letter-spacing: -0.01em; color: var(--ui-text-subtle);">
                            {{ acc.account.account_name }}
                          </h5>
                          <span class="badge rounded-pill" :style="{ background: 'transparent', border: `1px solid ${getThemeColorByTag(sharedTagLabel(acc))}`, color: getThemeColorByTag(sharedTagLabel(acc)), fontSize: '0.65rem', padding: '0.1rem 0.4rem', fontWeight: '500' }">
                            {{ sharedTagLabel(acc) }}
                          </span>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                          <span class="text-muted small fw-medium" style="font-size: 0.8rem;">소유자: {{ acc.account.owner }}</span>
                          <span class="text-muted small opacity-50">·</span>
                          <span class="text-muted small fw-medium" style="font-size: 0.8rem;">{{ acc.account.account_number }}</span>
                        </div>
                      </div>
                    </div>
                    <div class="d-flex align-items-center gap-4 text-end ms-md-auto">
                      <div class="d-flex flex-column">
                        <span class="text-muted small fw-bold text-uppercase opacity-75" style="font-size: 0.65rem;">현재 평가 자산</span>
                        <span class="fw-bold tabular-nums text-success h5 mb-0">₩{{ Number(acc.total_asset_value || 0).toLocaleString() }}</span>
                      </div>
                      <div v-if="acc.prev_day_asset_change != null" class="d-flex flex-column align-items-end">
                        <span class="text-muted small fw-bold text-uppercase opacity-75" style="font-size: 0.65rem;">전일 대비</span>
                        <div class="d-flex align-items-center gap-1 fw-bold" :class="prevDayChangeClass(acc.prev_day_asset_change)" style="font-size: 0.9rem;">
                           <MaterialIcon :name="acc.prev_day_asset_change >= 0 ? 'arrow_drop_up' : 'arrow_drop_down'" size="1.1rem" />
                           <span class="tabular-nums">{{ formatPrevDayMoney(acc.prev_day_asset_change) }}</span>
                           <span class="opacity-75" style="font-size: 0.72rem;">({{ formatPrevDayPercent(acc.prev_day_return_vs_principal_pct) }})</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- Flat Grid -->
                  <div class="row g-3">
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">투자 원금</span>
                        <span class="fw-bold tabular-nums small">₩{{ Number(acc.principal || 0).toLocaleString() }}</span>
                      </div>
                    </div>
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">평가 손익</span>
                        <span class="fw-bold tabular-nums small" :class="(acc.investment_return || 0) >= 0 ? 'text-profit' : 'text-loss'">
                          {{ (acc.investment_return || 0) >= 0 ? '+' : '' }}₩{{ Number(Math.abs(acc.investment_return || 0)).toLocaleString() }}
                        </span>
                      </div>
                    </div>
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">수익률(ROI)</span>
                        <span class="fw-bold tabular-nums small" :class="(acc.investment_return || 0) >= 0 ? 'text-profit' : 'text-loss'">
                          {{ (acc.investment_return || 0) >= 0 ? '+' : '' }}{{ (acc.principal > 0 ? (acc.investment_return / acc.principal * 100) : 0).toFixed(2) }}%
                        </span>
                      </div>
                    </div>
                    <div class="col-6 col-md-3">
                      <div class="d-flex justify-content-between align-items-center border-bottom border-soft pb-1">
                        <span class="text-muted small fw-bold">업데이트</span>
                        <span class="text-muted x-small fw-medium">{{ formatAgeMinutes(Number(acc.oldest_price_age_minutes)) || '-' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { accountApi, userApi, getApiErrorMessage } from '../api'
import { pollUntilBalanceOverviewFresh } from '../composables/useBalanceRefreshPolling'
import { authStore } from '../stores/auth'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import MaterialIcon from '../components/MaterialIcon.vue'
import {
  formatPrevDayMoney,
  formatPrevDayPercent,
  prevDayChangeClass,
} from '../utils/prevDayAsset'

const emit = defineEmits(['flash'])
const router = useRouter()

const overview = ref([])
const loading = ref(true)
const refreshing = ref(false)
const categories = ref([])
const accountCategoryMap = ref({})
const expandedTagNames = ref(new Set())

const loadDashboardPrefs = async () => {
  if (!authStore.isAuthenticated) return;
  try {
    const { data } = await userApi.getPreferences();
    const prefs = data?.preferences;
    if (prefs) {
      categories.value = prefs.categories || [];
      accountCategoryMap.value = prefs.account_category_map || {};
    }
  } catch (e) {
    console.warn('Failed to load dashboard prefs for theming:', e);
  }
};

let overviewAbortController = null
let overviewReqId = 0

const myAccounts = computed(() => {
  return overview.value.filter(acc => acc.account.user_id === authStore.user?.id)
})

const sharedAccounts = computed(() => {
  return overview.value.filter(acc => acc.account.user_id !== authStore.user?.id)
})

const myAccountTagGroups = computed(() => {
  const groups = new Map()
  for (const item of myAccounts.value) {
    const rawTags = Array.isArray(item?.account?.tags) ? item.account.tags : []
    const tags = rawTags.length > 0 ? rawTags : ['미분류']
    for (const tag of tags) {
      if (!groups.has(tag)) {
        groups.set(tag, {
          tag,
          items: [],
          totalAsset: 0,
          totalPrincipal: 0,
          totalReturn: 0
        })
      }
      const g = groups.get(tag)
      g.items.push(item)
      g.totalAsset += Number(item.total_asset_value || 0)
      g.totalPrincipal += Number(item.principal || 0)
      g.totalReturn += Number(item.investment_return || 0)
    }
  }
  return Array.from(groups.values())
    .map(g => ({
      ...g,
      returnRate: g.totalPrincipal > 0 ? (g.totalReturn / g.totalPrincipal) * 100 : 0
    }))
    .sort((a, b) => a.tag.localeCompare(b.tag, 'ko'))
})

watch(
  [myAccountTagGroups, sharedAccounts],
  ([groups, shared]) => {
    const prev = expandedTagNames.value
    const next = new Set()
    for (const g of groups) {
      if (prev.has(g.tag)) next.add(g.tag)
      else next.add(g.tag)
    }
    if (shared.length > 0) {
      if (prev.has('__shared__')) next.add('__shared__')
      else next.add('__shared__')
    }
    expandedTagNames.value = next
  },
  { immediate: true }
)

const getThemeColorByTag = (tag) => {
  if (!tag) return 'var(--color-category-1)';
  // Simple stable hash based on name
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % 8 + 1;
  return `var(--color-category-${index})`;
}

/** 공유 계좌 카드 리본·테두리용 태그 라벨 */
function sharedTagLabel(acc) {
  const raw = Array.isArray(acc?.account?.tags) ? acc.account.tags : []
  if (raw.length > 0) return String(raw[0])
  return '미분류'
}

function isTagExpanded(tag) {
  return expandedTagNames.value.has(tag)
}

function toggleTagExpanded(tag) {
  const next = new Set(expandedTagNames.value)
  if (next.has(tag)) next.delete(tag)
  else next.add(tag)
  expandedTagNames.value = next
}


const listOldestPrice = computed(() => {
  let oldestRaw = ''
  let oldestEpoch = Number.POSITIVE_INFINITY
  let oldestMinutes = null
  for (const acc of overview.value) {
    const raw = acc?.oldest_price_updated_at
    const minutes = Number(acc?.oldest_price_age_minutes)
    if (!raw || !Number.isFinite(minutes) || minutes < 0) continue
    const parsed = new Date(raw)
    if (Number.isNaN(parsed.getTime())) continue
    const epoch = parsed.getTime()
    if (epoch < oldestEpoch) {
      oldestEpoch = epoch
      oldestRaw = raw
      oldestMinutes = minutes
    }
  }
  return { raw: oldestRaw, minutes: oldestMinutes }
})

function formatAgeMinutes(minutes) {
  if (!Number.isFinite(minutes) || minutes < 0) return ''
  if (minutes < 1) return '방금'
  if (minutes < 60) return `${minutes}분전`
  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  if (hours < 24) {
    return remainMinutes > 0 ? `${hours}시간${remainMinutes}분전` : `${hours}시간전`
  }
  const days = Math.floor(hours / 24)
  const remainHours = hours % 24
  return remainHours > 0 ? `${days}일${remainHours}시간전` : `${days}일전`
}

const listOldestPriceUpdatedAtLabel = computed(() => {
  const raw = listOldestPrice.value.raw
  if (!raw) return ''
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
})

const listOldestPriceAgeText = computed(() => formatAgeMinutes(Number(listOldestPrice.value.minutes)))

function goToDetail(accountId) {
  router.push(`/balances/${accountId}`)
}

async function loadOverview() {
  if (overviewAbortController) {
    overviewAbortController.abort()
  }
  overviewAbortController = new AbortController()
  const reqId = ++overviewReqId
  try {
    const { data } = await accountApi.getBalancesOverview({ signal: overviewAbortController.signal })
    if (reqId !== overviewReqId) return
    overview.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    if (reqId !== overviewReqId) return
    overview.value = []
    emit('flash', getApiErrorMessage(e, '계좌 현황을 불러오지 못했습니다.'), 'alert-danger')
  } finally {
    if (reqId !== overviewReqId) return
    loading.value = false
  }
}

async function loadOverviewUntilFresh() {
  await loadOverview()
  if (!authStore.isAuthenticated) return
  if (!overview.value.some((a) => a.is_stale)) return
  await pollUntilBalanceOverviewFresh({
    loadOverview,
    isStale: () => overview.value.some((a) => a.is_stale),
  })
}

async function doRefresh() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    let refreshQueued = true
    if (authStore.isAuthenticated) {
      try {
        const { data } = await accountApi.refreshAllBalances()
        if (data && data.queued === false) {
          refreshQueued = false
          emit('flash', data.message || '갱신 요청을 처리하지 못했습니다.', 'alert-warning')
        }
      } catch (e) {
        emit('flash', getApiErrorMessage(e, '현재가 갱신 요청에 실패했습니다.'), 'alert-danger')
        await loadOverview()
        return
      }
    }
    await loadOverview()
    if (
      refreshQueued
      && authStore.isAuthenticated
      && overview.value.some((a) => a.is_stale)
    ) {
      const stillStale = () => overview.value.some((a) => a.is_stale)
      const ok = await pollUntilBalanceOverviewFresh({
        loadOverview,
        isStale: stillStale,
      })
      if (!ok) {
        emit('flash', '갱신이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.', 'alert-warning')
      }
    }
  } finally {
    refreshing.value = false
  }
}

onMounted(async () => {
  loadDashboardPrefs()
  await loadOverviewUntilFresh()
})

onBeforeUnmount(() => {
  overviewAbortController?.abort()
})
</script>

<style scoped>
.tabular-nums { font-variant-numeric: tabular-nums; }
.letter-spacing-1 { letter-spacing: 0.05rem; }
.cursor-pointer { cursor: pointer; }

.balance-page-title {
  color: var(--ui-text);
}

.balance-list-status-bar {
  padding: 0.48rem 0.6rem;
  border-radius: 12px;
  border: 1px solid var(--ui-border);
  background: var(--ui-surface-soft);
}
.balance-list-status-text {
  font-size: 0.76rem;
}

.balance-tag-section {
  position: relative;
}

.balance-card-stack {
  border: 1px solid var(--ui-border);
  border-radius: 12px;
  overflow: hidden;
  background: var(--ui-surface);
}

.balance-group-members {
  margin-top: 0 !important;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  background: color-mix(in srgb, var(--ui-bg) 85%, var(--ui-surface-soft));
  box-shadow: inset 0 3px 6px -3px rgba(0,0,0,0.08);
  border: 1px solid var(--ui-border);
  border-top: 0;
}

.balance-card-stack-item + .balance-card-stack-item .balance-acc-card {
  border-top: 1px solid var(--ui-border) !important;
}


.balance-group-summary {
  box-shadow: var(--ui-shadow);
  border-radius: 12px !important;
  margin-bottom: 0.5rem !important;
  padding-top: 1rem !important;
  padding-bottom: 1rem !important;
  background: color-mix(in srgb, var(--balance-tag-accent) 4%, var(--ui-surface)) !important;
  border: 1px solid color-mix(in srgb, var(--balance-tag-accent) 20%, var(--ui-border)) !important;
  transition: all 0.2s ease;
}

.balance-group-summary:hover {
  background: color-mix(in srgb, var(--balance-tag-accent) 8%, var(--ui-surface)) !important;
  border-color: color-mix(in srgb, var(--balance-tag-accent) 30%, var(--ui-border)) !important;
}

.balance-group-summary--expanded {
  border-bottom-left-radius: 0 !important;
  border-bottom-right-radius: 0 !important;
  margin-bottom: 0 !important;
  box-shadow: none;
}
.balance-group-flag-label {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
  font-size: 0.62rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  padding: 0.15rem 0.45rem;
  text-transform: uppercase;
  background: transparent;
  border: 1px solid var(--ui-border);
}
.balance-group-flag-icon {
  opacity: 0.8;
}
.balance-group-tag-title {
  color: var(--ui-text);
  letter-spacing: -0.01em;
  font-size: 1.05rem;
  font-weight: 700;
  line-height: 1.2;
}

.balance-group-subtitle {
  color: var(--ui-text-muted);
  font-size: 0.78rem;
  font-weight: 500;
  margin-top: 0.1rem;
}
.balance-group-icon-ring {
  box-shadow: none;
  border-width: 1px !important;
}

.balance-group-accordion-btn {
  border: 1px solid var(--ui-border);
  border-radius: 10px;
  color: var(--ui-text);
  background: color-mix(in srgb, var(--ui-surface-soft) 70%, transparent);
  box-shadow: none;
  padding: 0.42rem 0.72rem;
  min-height: 2.35rem;
  font-size: 0.82rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
}
.balance-group-accordion-btn:hover {
  color: var(--ui-text);
  border-color: color-mix(in srgb, var(--ui-text-muted) 30%, var(--ui-border));
  background: color-mix(in srgb, var(--ui-surface-soft) 90%, transparent);
}


.balance-acc-card {
  border: 0 !important;
  border-radius: 0 !important;
  background: var(--ui-surface) !important;
  transition: box-shadow 0.2s ease, transform 0.2s ease, background-color 0.2s;
  box-shadow: none;
}

.balance-acc-card:hover {
  background: color-mix(in srgb, var(--balance-tag-accent) 2%, var(--ui-surface)) !important;
  z-index: 5;
}
.balance-acc-icon-ring {
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

@media (max-width: 767.98px) {
  .balance-group-summary {
    padding-top: 0.78rem !important;
    padding-bottom: 0.78rem !important;
  }

  .balance-group-tag-title {
    font-size: 0.98rem;
  }

  .balance-group-subtitle {
    font-size: 0.74rem;
  }
}
.balance-acc-icon-ring--md {
  width: 2.45rem;
  height: 2.45rem;
  flex-shrink: 0;
}

.balance-card-stack-item:first-child .balance-acc-card {
  border-top-left-radius: 12px !important;
  border-top-right-radius: 12px !important;
}

.balance-card-stack-item:last-child .balance-acc-card {
  border-bottom-left-radius: 12px !important;
  border-bottom-right-radius: 12px !important;
}

/* 손익 색 — 대시보드와 동일 토큰 */
.text-profit { color: var(--ui-up) !important; font-weight: 600; }
.text-loss { color: var(--ui-down) !important; font-weight: 600; }
:global([data-theme="dark"]) .text-profit { color: #fb7185 !important; }
:global([data-theme="dark"]) .text-loss { color: #60a5fa !important; }

.border-soft { border-color: rgba(0,0,0,0.06) !important; }
:global([data-theme="dark"]) .border-soft { border-color: rgba(255,255,255,0.08) !important; }

</style>
