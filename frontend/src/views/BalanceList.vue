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
          class="mb-4 mb-xxl-5 balance-tag-section"
          :style="{ '--category-color': getThemeColorByTag(group.tag) }"
        >
          <!-- 대시보드 분류 카드와 동일한 사각 카드형태: 상단 그라데이션 바 + 좌측 색깔 테두리 + 타이포그래피 강조 -->
          <div class="card border-0 shadow-sm rounded-4 overflow-hidden balance-group-card" :style="{ borderLeft: '6px solid var(--category-color)' }">
            <div class="balance-group-card__header p-3 p-md-4">
              <div class="d-flex align-items-start gap-3">
                <div class="min-w-0 flex-grow-1">
                  <div class="balance-group-card__title text-truncate" :style="{ color: 'var(--category-color)' }">{{ group.tag }}</div>
                  <div class="balance-group-card__sub">{{ group.items.length }}개 계좌</div>
                </div>
              </div>

              <div class="balance-group-kpi-row mt-3">
                <div class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">총 평가</div>
                  <div class="balance-group-kpi-value" :style="{ color: 'var(--category-color)' }">{{ formatMoneyWonFull(group.totalAsset) }}</div>
                </div>
                <div class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">투자 원금</div>
                  <div class="balance-group-kpi-value" style="color: var(--ui-text-subtle);">{{ formatMoneyWonFull(group.totalPrincipal) }}</div>
                </div>
                <div class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">평가 손익</div>
                  <div class="balance-group-kpi-value" :class="group.totalReturn >= 0 ? 'text-profit' : 'text-loss'">
                    {{ formatSignedMoneyWonFull(group.totalReturn) }}
                    <span class="balance-kpi-pct" :class="pctFlagClass(group.totalReturn)">{{ group.totalReturn >= 0 ? '+' : '' }}{{ group.returnRate.toFixed(2) }}%</span>
                  </div>
                </div>
                <div v-if="group.prevDayReturnPct != null" class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">전일대비</div>
                  <div class="balance-group-kpi-value" :class="prevDayChangeClass(group.prevDayChangeSum)">
                    {{ formatPrevDayMoney(group.prevDayChangeSum) }}
                    <span class="balance-kpi-pct" :class="pctFlagClass(group.prevDayChangeSum)">{{ formatPrevDayPercent(group.prevDayReturnPct) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="balance-group-card__footer border-top border-light-subtle px-3 px-md-4 py-3">
              <div v-if="groupPriceUpdateLine(group.items)" class="text-muted mb-2 pb-2 border-bottom border-light-subtle" style="font-size: 0.8rem;">
                시세 {{ groupPriceUpdateLine(group.items) }}
              </div>
              <div class="balance-group-expand-bar">
                <button
                  type="button"
                  class="balance-group-expand-btn"
                  @click="toggleTagExpanded(group.tag)"
                  :aria-label="`${group.tag} 그룹 펼치기/접기`"
                >
                  <span class="balance-group-expand-btn__text">
                    {{ isTagExpanded(group.tag) ? '계좌 목록 접기' : `계좌 ${group.items.length}개 보기` }}
                  </span>
                  <MaterialIcon
                    :name="isTagExpanded(group.tag) ? 'expand_less' : 'expand_more'"
                    size="1.1rem"
                    class="balance-group-expand-btn__icon"
                  />
                </button>
              </div>
            </div>
          </div>

          <transition name="balance-acc-slide">
          <div v-show="isTagExpanded(group.tag)" class="balance-row-list mt-2">
            <div
              v-for="acc in group.items"
              :key="acc.account.id"
              class="balance-row"
              :style="{ borderLeft: '3px solid var(--category-color)' }"
              @click="goToDetail(acc.account.id)"
            >
              <div class="balance-row__top">
                <div class="balance-row__name min-w-0">
                  <div class="balance-row__title text-truncate d-flex align-items-center gap-1">
                    <span class="text-truncate">{{ acc.account.account_name }}</span>
                    <MaterialIcon name="open_in_new" size="0.85rem" class="opacity-40 flex-shrink-0" />
                  </div>
                  <div class="balance-row__meta">
                    <span class="balance-row__tag" :style="{ color: 'var(--category-color)' }">#{{ group.tag }}</span>
                    <span class="balance-row__num">{{ acc.account.account_number }}</span>
                  </div>
                </div>
                <div class="balance-row__metrics">
                  <div class="balance-row__metric">
                    <div class="balance-row__metric-label">총 자산</div>
                    <div class="balance-row__metric-value">{{ formatMoneyWonFull(acc.total_asset_value) }}</div>
                  </div>
                  <div class="balance-row__metric d-none d-sm-flex">
                    <div class="balance-row__metric-label">수익률</div>
                    <div class="balance-row__metric-value balance-row__metric-value--pct" :class="pctFlagClass(acc.investment_return)">
                      {{ acc.investment_return >= 0 ? '+' : '' }}{{ (acc.principal > 0 ? (acc.investment_return / acc.principal * 100) : 0).toFixed(1) }}%
                    </div>
                  </div>
                  <div v-if="acc.prev_day_return_vs_principal_pct != null" class="balance-row__metric">
                    <div class="balance-row__metric-label">전일대비</div>
                    <div class="balance-row__metric-value" :class="prevDayChangeClass(acc.prev_day_asset_change)">
                      {{ formatPrevDayMoney(acc.prev_day_asset_change) }}
                      <span class="balance-row__metric-pct" :class="pctFlagClass(acc.prev_day_asset_change)">{{ formatPrevDayPercent(acc.prev_day_return_vs_principal_pct) }}</span>
                    </div>
                  </div>
                  <MaterialIcon name="chevron_right" size="1rem" class="flex-shrink-0" style="color: var(--ui-text-muted); opacity: 0.5;" />
                </div>
              </div>

              <div class="balance-row__secondary">
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">투자 원금</span>
                  <span class="balance-row__secondary-value">{{ formatMoneyWonFull(acc.principal) }}</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">보유 종목</span>
                  <span class="balance-row__secondary-value">{{ accountHoldingsCount(acc) }}종목</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">현금 비중</span>
                  <span class="balance-row__secondary-value">{{ accountCashRatioPct(acc).toFixed(1) }}%</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">마지막 리밸런싱</span>
                  <span class="balance-row__secondary-value">{{ accountLastRebalancedLabel(acc) }}</span>
                </div>
                <div v-if="accountMaxDeviationPct(acc) != null" class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">최대 이격도</span>
                  <span class="balance-row__secondary-value" :class="deviationClass(accountMaxDeviationPct(acc))">{{ accountMaxDeviationPct(acc).toFixed(1) }}%</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">시세 갱신</span>
                  <span class="balance-row__secondary-value balance-row__secondary-value--muted">{{ formatAgeMinutes(Number(acc.oldest_price_age_minutes)) || '-' }}</span>
                </div>
              </div>
            </div>
          </div>
          </transition>
        </div>
      </div>

      <div v-if="sharedAccounts.length > 0" class="col-12 mt-1">
        <div class="mb-4 mb-xxl-5 balance-tag-section" :style="{ '--category-color': 'var(--ui-text-muted)' }">
          <!-- 공유받은 계좌도 나의 계좌 그룹과 동일한 사각 카드형태 -->
          <div class="card border-0 shadow-sm rounded-4 overflow-hidden balance-group-card" :style="{ borderLeft: '6px solid var(--category-color)' }">
            <div class="balance-group-card__header p-3 p-md-4">
              <div class="d-flex align-items-start gap-3">
                <div class="min-w-0 flex-grow-1">
                  <div class="balance-group-card__title text-truncate" :style="{ color: 'var(--category-color)' }">공유받은 계좌</div>
                  <div class="balance-group-card__sub">{{ sharedAccounts.length }}개 계좌</div>
                </div>
              </div>

              <div class="balance-group-kpi-row mt-3">
                <div class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">총 평가</div>
                  <div class="balance-group-kpi-value" :style="{ color: 'var(--category-color)' }">{{ formatMoneyWonFull(sharedAccountsSummary.totalAsset) }}</div>
                </div>
                <div class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">투자 원금</div>
                  <div class="balance-group-kpi-value" style="color: var(--ui-text-subtle);">{{ formatMoneyWonFull(sharedAccountsSummary.totalPrincipal) }}</div>
                </div>
                <div class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">평가 손익</div>
                  <div class="balance-group-kpi-value" :class="sharedAccountsSummary.totalReturn >= 0 ? 'text-profit' : 'text-loss'">
                    {{ formatSignedMoneyWonFull(sharedAccountsSummary.totalReturn) }}
                    <span class="balance-kpi-pct" :class="pctFlagClass(sharedAccountsSummary.totalReturn)">{{ sharedAccountsSummary.totalReturn >= 0 ? '+' : '' }}{{ sharedAccountsSummary.returnRate.toFixed(2) }}%</span>
                  </div>
                </div>
                <div v-if="sharedAccountsSummary.prevDayReturnPct != null" class="balance-group-kpi-item">
                  <div class="balance-group-kpi-label">전일대비</div>
                  <div class="balance-group-kpi-value" :class="prevDayChangeClass(sharedAccountsSummary.prevDayChangeSum)">
                    {{ formatPrevDayMoney(sharedAccountsSummary.prevDayChangeSum) }}
                    <span class="balance-kpi-pct" :class="pctFlagClass(sharedAccountsSummary.prevDayChangeSum)">{{ formatPrevDayPercent(sharedAccountsSummary.prevDayReturnPct) }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="balance-group-card__footer border-top border-light-subtle px-3 px-md-4 py-3">
              <div v-if="groupPriceUpdateLine(sharedAccounts)" class="text-muted mb-2 pb-2 border-bottom border-light-subtle" style="font-size: 0.8rem;">
                시세 {{ groupPriceUpdateLine(sharedAccounts) }}
              </div>
              <div class="balance-group-expand-bar">
                <button
                  type="button"
                  class="balance-group-expand-btn"
                  @click="toggleTagExpanded('__shared__')"
                  :aria-label="`공유받은 계좌 펼치기/접기`"
                >
                  <span class="balance-group-expand-btn__text">
                    {{ isTagExpanded('__shared__') ? '계좌 목록 접기' : `계좌 ${sharedAccounts.length}개 보기` }}
                  </span>
                  <MaterialIcon
                    :name="isTagExpanded('__shared__') ? 'expand_less' : 'expand_more'"
                    size="1.1rem"
                    class="balance-group-expand-btn__icon"
                  />
                </button>
              </div>
            </div>
          </div>

          <transition name="balance-acc-slide">
          <div v-show="isTagExpanded('__shared__')" class="balance-row-list mt-2">
            <div
              v-for="acc in sharedAccounts"
              :key="acc.account.id"
              class="balance-row"
              :style="{ borderLeft: `3px solid ${getThemeColorByTag(sharedTagLabel(acc))}` }"
              @click="goToDetail(acc.account.id)"
            >
              <div class="balance-row__top">
                <div class="balance-row__name min-w-0">
                  <div class="balance-row__title text-truncate d-flex align-items-center gap-1">
                    <span class="text-truncate">{{ acc.account.account_name }}</span>
                    <MaterialIcon name="open_in_new" size="0.85rem" class="opacity-40 flex-shrink-0" />
                  </div>
                  <div class="balance-row__meta">
                    <span class="balance-row__tag" :style="{ color: getThemeColorByTag(sharedTagLabel(acc)) }">#{{ sharedTagLabel(acc) }}</span>
                    <span class="balance-row__owner-tag">{{ acc.account.owner || '공유' }}</span>
                    <span class="balance-row__num">{{ acc.account.account_number }}</span>
                  </div>
                </div>
                <div class="balance-row__metrics">
                  <div class="balance-row__metric">
                    <div class="balance-row__metric-label">총 자산</div>
                    <div class="balance-row__metric-value">{{ formatMoneyWonFull(acc.total_asset_value) }}</div>
                  </div>
                  <div class="balance-row__metric d-none d-sm-flex">
                    <div class="balance-row__metric-label">수익률</div>
                    <div class="balance-row__metric-value balance-row__metric-value--pct" :class="pctFlagClass(acc.investment_return)">
                      {{ acc.investment_return >= 0 ? '+' : '' }}{{ (acc.principal > 0 ? (acc.investment_return / acc.principal * 100) : 0).toFixed(1) }}%
                    </div>
                  </div>
                  <div v-if="acc.prev_day_return_vs_principal_pct != null" class="balance-row__metric">
                    <div class="balance-row__metric-label">전일대비</div>
                    <div class="balance-row__metric-value" :class="prevDayChangeClass(acc.prev_day_asset_change)">
                      {{ formatPrevDayMoney(acc.prev_day_asset_change) }}
                      <span class="balance-row__metric-pct" :class="pctFlagClass(acc.prev_day_asset_change)">{{ formatPrevDayPercent(acc.prev_day_return_vs_principal_pct) }}</span>
                    </div>
                  </div>
                  <MaterialIcon name="chevron_right" size="1rem" class="flex-shrink-0" style="color: var(--ui-text-muted); opacity: 0.5;" />
                </div>
              </div>

              <div class="balance-row__secondary">
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">투자 원금</span>
                  <span class="balance-row__secondary-value">{{ formatMoneyWonFull(acc.principal) }}</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">보유 종목</span>
                  <span class="balance-row__secondary-value">{{ accountHoldingsCount(acc) }}종목</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">현금 비중</span>
                  <span class="balance-row__secondary-value">{{ accountCashRatioPct(acc).toFixed(1) }}%</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">마지막 리밸런싱</span>
                  <span class="balance-row__secondary-value">{{ accountLastRebalancedLabel(acc) }}</span>
                </div>
                <div v-if="accountMaxDeviationPct(acc) != null" class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">최대 이격도</span>
                  <span class="balance-row__secondary-value" :class="deviationClass(accountMaxDeviationPct(acc))">{{ accountMaxDeviationPct(acc).toFixed(1) }}%</span>
                </div>
                <div class="balance-row__secondary-item">
                  <span class="balance-row__secondary-label">시세 갱신</span>
                  <span class="balance-row__secondary-value balance-row__secondary-value--muted">{{ formatAgeMinutes(Number(acc.oldest_price_age_minutes)) || '-' }}</span>
                </div>
              </div>
            </div>
          </div>
          </transition>
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

/** 대시보드 그룹 카드와 동일: 전일대비 합계·원금대비 비율 */
function aggregatePrevDay(accounts) {
  let changeSum = 0
  let principalSum = 0
  for (const acc of accounts) {
    if (acc.prev_day_asset_change != null && !Number.isNaN(Number(acc.prev_day_asset_change))) {
      changeSum += Number(acc.prev_day_asset_change)
      principalSum += Number(acc.principal || 0)
    }
  }
  const pct = principalSum > 0 ? (changeSum / principalSum) * 100 : null
  return { changeSum, pct }
}

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
    .map(g => {
      const pd = aggregatePrevDay(g.items)
      return {
        ...g,
        returnRate: g.totalPrincipal > 0 ? (g.totalReturn / g.totalPrincipal) * 100 : 0,
        prevDayChangeSum: pd.changeSum,
        prevDayReturnPct: pd.pct,
      }
    })
    .sort((a, b) => a.tag.localeCompare(b.tag, 'ko'))
})

/** 공유받은 계좌 섹션도 그룹 카드와 동일한 KPI 요약을 보여주기 위한 합계 */
const sharedAccountsSummary = computed(() => {
  const items = sharedAccounts.value
  const totalAsset = items.reduce((s, a) => s + Number(a.total_asset_value || 0), 0)
  const totalPrincipal = items.reduce((s, a) => s + Number(a.principal || 0), 0)
  const totalReturn = items.reduce((s, a) => s + Number(a.investment_return || 0), 0)
  const pd = aggregatePrevDay(items)
  return {
    totalAsset,
    totalPrincipal,
    totalReturn,
    returnRate: totalPrincipal > 0 ? (totalReturn / totalPrincipal) * 100 : 0,
    prevDayChangeSum: pd.changeSum,
    prevDayReturnPct: pd.pct,
  }
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

/** 대시보드 분류 카드와 동일한 팔레트(--dash-cat-1..8)를 태그 이름 해시로 안정 배정 */
const getThemeColorByTag = (tag) => {
  if (!tag) return 'var(--dash-cat-1)';
  // Simple stable hash based on name
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % 8 + 1;
  return `var(--dash-cat-${index})`;
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


/** 계좌 목록 중 가장 오래된 시세 갱신 시각 — 전체(overview)뿐 아니라 태그 그룹별로도 재사용 */
function oldestPriceFromAccounts(accounts) {
  let oldestRaw = ''
  let oldestEpoch = Number.POSITIVE_INFINITY
  let oldestMinutes = null
  for (const acc of accounts) {
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
}

const listOldestPrice = computed(() => oldestPriceFromAccounts(overview.value))

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

function formatPriceUpdatedAtLabel(raw) {
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
}

const listOldestPriceUpdatedAtLabel = computed(() => formatPriceUpdatedAtLabel(listOldestPrice.value.raw))

const listOldestPriceAgeText = computed(() => formatAgeMinutes(Number(listOldestPrice.value.minutes)))

/** 대시보드 그룹 카드와 동일: 그룹(태그) 내 계좌 중 가장 오래된 시세 갱신 문구 */
function groupPriceUpdateLine(items) {
  const { raw, minutes } = oldestPriceFromAccounts(items)
  const label = formatPriceUpdatedAtLabel(raw)
  const age = formatAgeMinutes(Number(minutes))
  if (label && age) return `${label} (${age})`
  return ''
}

function goToDetail(accountId) {
  router.push(`/balances/${accountId}`)
}

/** 대시보드 계좌 카드와 동일한 표기: 억·만 축약 없이 원 단위 전체 표시 */
function formatMoneyWonFull(val) {
  if (!Number.isFinite(Number(val))) return '₩0'
  return '₩' + Math.round(Number(val)).toLocaleString()
}

/** 대시보드 그룹 카드와 동일: 부호 있는 원 단위 표시 */
function formatSignedMoneyWonFull(val) {
  const n = Number(val)
  if (!Number.isFinite(n)) return '—'
  const sign = n > 0 ? '+' : n < 0 ? '-' : ''
  return sign + '₩' + Math.abs(Math.round(n)).toLocaleString()
}

/** 대시보드와 동일: +/-/0 값을 플래그 배지 색으로 구분 */
function pctFlagClass(n) {
  const v = Number(n)
  if (!Number.isFinite(v) || v === 0) return 'bg-secondary-subtle text-muted'
  return v > 0 ? 'bg-profit-soft' : 'bg-loss-soft'
}

/** 대시보드와 동일: 보유 종목 수(현금 제외) */
function accountHoldingsCount(acc) {
  const holdings = Array.isArray(acc?.holdings) ? acc.holdings : []
  return holdings.filter((h) => h && h.ticker !== 'CASH').length
}

/** 대시보드와 동일: 총자산 대비 현금 비중(%) */
function accountCashRatioPct(acc) {
  const total = Number(acc?.total_asset_value || 0)
  if (total <= 0) return 0
  const cash = Number(acc?.cash_balance || 0)
  return Math.max(0, (cash / total) * 100)
}

/** 대시보드와 동일: 마지막 리밸런싱일로부터 경과일 */
function accountLastRebalancedLabel(acc) {
  const raw = acc?.last_rebalanced_date
  if (!raw) return '-'
  try {
    const last = new Date(raw)
    if (Number.isNaN(last.getTime())) return '-'
    last.setHours(0, 0, 0, 0)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const diffDays = Math.floor((today - last) / (1000 * 60 * 60 * 24))
    if (diffDays <= 0) return '오늘'
    return `${diffDays}일전`
  } catch (e) {
    return '-'
  }
}

/**
 * 대시보드와 동일: 종목별 목표 비중 대비 "상대" 이격도 중 최댓값(%).
 * 목표 비중이 0인 종목(포트폴리오 미편입 보유분)은 제외.
 */
function accountMaxDeviationPct(acc) {
  const holdings = Array.isArray(acc?.holdings) ? acc.holdings : []
  let max = 0
  let found = false
  for (const h of holdings) {
    const current = Number(h?.current_ratio)
    const target = Number(h?.target_ratio)
    if (!Number.isFinite(current) || !Number.isFinite(target) || target <= 0) continue
    found = true
    const dev = Math.abs(current - target) / target * 100
    if (dev > max) max = dev
  }
  return found ? max : null
}

/** 대시보드와 동일: 이격도 25%(5/25 규칙의 상대 기준) 이상이면 경고색 */
function deviationClass(pct) {
  if (!Number.isFinite(pct)) return ''
  if (pct >= 25) return 'balance-row__secondary-value--warn'
  return ''
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
    if (reqId === overviewReqId) {
      loading.value = false
    }
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

/* ── 플랫 · 매트 테마: 대시보드와 동일하게 이 화면의 카드/배지/버튼도 각지고 그림자 없이 ── */
.balance-list-root :deep(.rounded-4),
.balance-list-root :deep(.rounded-3),
.balance-list-root :deep(.rounded-circle),
.balance-list-root :deep(.rounded-pill) {
  border-radius: 2px !important;
}
.balance-list-root :deep(.shadow-sm) {
  box-shadow: none !important;
}

.balance-page-title {
  color: var(--ui-text);
}

.balance-list-status-bar {
  padding: 0.48rem 0.6rem;
  border-radius: 2px;
  border: 1px solid var(--ui-border);
  background: var(--ui-surface-soft);
}
.balance-list-status-text {
  font-size: 0.76rem;
}

.balance-tag-section {
  position: relative;
}

.balance-group-card__footer {
  background: color-mix(in srgb, var(--ui-surface-soft) 60%, transparent);
}

:global([data-theme="dark"]) .balance-group-card__footer {
  background: rgba(255, 255, 255, 0.02);
}

.balance-row-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

/* ── 태그 그룹 카드 — 대시보드 분류 카드(dashboard-group-big-card)와 동일한 사각 카드형태 ── */
.balance-group-card {
  position: relative;
  background: var(--ui-surface);
  transition: box-shadow 0.18s ease;
}

/* 배경 전체를 테마색으로 칠하면 얼룩처럼 보여 대시보드와 동일하게 상단 얇은 그라데이션 바로만 테마 표시 */
.balance-group-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--category-color) 0%, color-mix(in srgb, var(--category-color) 40%, transparent) 55%, transparent 100%);
}

.balance-group-card__header {
  /* 클릭 영역 아님: 하단 더보기 버튼으로 대체 */
}

/* 아이콘 없이 타이포그래피 자체를 굵고 크게 키워 태그를 강조 — 대시보드와 동일 */
.balance-group-card__title {
  font-size: 1.55rem;
  font-weight: 800;
  /* 한글은 자간을 좁히면 오히려 읽기 어려워지므로(라틴 타이포 관례와 반대) 자간 조정을 두지 않음 */
  line-height: 1.3;
}

.balance-group-card__sub {
  display: inline-flex;
  align-items: center;
  font-size: 0.78rem;
  color: var(--category-color);
  font-weight: 700;
  margin-top: 0.2rem;
  padding: 0.05rem 0.5rem;
  border-radius: 2px;
  background: color-mix(in srgb, var(--category-color) 14%, transparent);
}

/* KPI 행 그리드: 모바일 2열, 576px 이상 4열 — 대시보드와 동일 */
.balance-group-kpi-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem 1rem;
}

@media (min-width: 576px) {
  .balance-group-kpi-row {
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem 1.25rem;
  }
}

.balance-group-kpi-item {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  /* 그리드 아이템 기본 min-width:auto는 내용(줄바꿈 없는 금액+퍼센트)만큼 트랙을 밀어내 카드 밖으로 넘치게 한다 */
  min-width: 0;
}

.balance-group-kpi-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ui-text);
  letter-spacing: 0.03em;
  text-transform: uppercase;
  line-height: 1.3;
}

.balance-group-kpi-value {
  font-size: 1.14rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.3;
  /* nowrap이면 좁은 컬럼에서 금액+퍼센트 배지가 카드 밖으로 넘친다 — 폭이 부족할 때만 자연스럽게 다음 줄로 */
  white-space: normal;
  font-variant-numeric: tabular-nums;
  font-family: var(--ui-num-font);
}

/* 퍼센트 수치: 작은 깃발(플래그) 배지 — 대시보드와 동일 */
.balance-kpi-pct {
  display: inline-flex;
  align-items: center;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0;
  margin-left: 0.4rem;
  padding: 0.08rem 0.5rem 0.08rem 0.65rem;
  line-height: 1.5;
  vertical-align: middle;
  clip-path: polygon(8px 0, 100% 0, 100% 100%, 8px 100%, 0 50%);
}

@media (min-width: 1200px) {
  .balance-group-kpi-row {
    gap: 0.6rem 2rem;
  }

  .balance-group-kpi-label {
    font-size: 0.86rem;
  }

  .balance-group-kpi-value {
    font-size: 1.34rem;
  }

  .balance-kpi-pct {
    font-size: 0.98rem;
  }
}

/* ── 더보기 버튼 ── */
.balance-group-expand-bar {
  display: flex;
  justify-content: center;
}

.balance-group-expand-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem 1rem;
  border: 1px solid var(--ui-border-strong);
  border-radius: 2px;
  background: var(--ui-surface-soft);
  color: var(--ui-text-subtle);
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.12s ease, color 0.12s ease;
  letter-spacing: 0.01em;
}

.balance-group-expand-btn:hover {
  background: color-mix(in srgb, var(--category-color) 12%, var(--ui-border));
  border-color: var(--category-color);
  color: var(--category-color);
}

:global([data-theme="dark"]) .balance-group-expand-btn {
  background: var(--ui-surface-soft);
  border-color: var(--ui-border-strong);
  color: var(--ui-text-muted);
}

:global([data-theme="dark"]) .balance-group-expand-btn:hover {
  background: color-mix(in srgb, var(--category-color) 16%, var(--ui-border));
  border-color: var(--category-color);
  color: var(--category-color);
}

.balance-group-expand-btn__text {
  line-height: 1;
}

.balance-group-expand-btn__icon {
  color: inherit;
  opacity: 0.75;
}

/* ── 계좌 목록 아코디언 슬라이드 전환 — 대시보드와 동일 ── */
:global(.balance-acc-slide-enter-active),
:global(.balance-acc-slide-leave-active) {
  transition: opacity 0.18s ease;
}
:global(.balance-acc-slide-enter-from),
:global(.balance-acc-slide-leave-to) {
  opacity: 0;
}


/* 손익 색 — 대시보드와 동일 토큰(다크모드는 --ui-up/--ui-down 자체가 재정의되므로 별도 오버라이드 불필요) */
.text-profit { color: var(--ui-up) !important; font-weight: 600; }
.text-loss { color: var(--ui-down) !important; font-weight: 600; }

.bg-profit-soft { background-color: color-mix(in srgb, var(--ui-up) 14%, transparent); color: var(--ui-up); }
.bg-loss-soft { background-color: color-mix(in srgb, var(--ui-down) 14%, transparent); color: var(--ui-down); }

/* 계좌 행 — 대시보드 계좌 목록(dash-acc-row)과 동일한 밀도 높은 리스트 스타일 */
.balance-row {
  display: flex;
  flex-direction: column;
  padding: 0.65rem 0.9rem;
  border-radius: 2px;
  background: var(--ui-surface);
  border: 1px solid var(--ui-border);
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.balance-row:hover {
  background: var(--ui-surface-soft);
}

.balance-row__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  min-height: 40px;
}

.balance-row__name {
  flex: 1;
  min-width: 0;
}

.balance-row__title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--ui-text);
  line-height: 1.3;
}

.balance-row__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem 0.5rem;
  margin-top: 0.12rem;
}

.balance-row__tag {
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1.3;
}

.balance-row__num {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--ui-text-muted);
  line-height: 1.3;
}

.balance-row__owner-tag {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ui-text-subtle);
  background: var(--ui-surface-soft);
  border: 1px solid var(--ui-border);
  padding: 0 0.4rem;
  line-height: 1.5;
}

.balance-row__metrics {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-shrink: 0;
}

.balance-row__metric {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.08rem;
}

/* 항목 간 구분선: 총자산 · 수익률 · 전일대비가 서로 붙어 보이지 않도록 */
.balance-row__metric:not(:first-child) {
  padding-left: 0.85rem;
  border-left: 1px solid var(--ui-border);
}

.balance-row__metric-label {
  font-size: 0.8rem;
  color: var(--ui-text);
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  white-space: nowrap;
  line-height: 1.3;
}

.balance-row__metric-value {
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.25;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  font-family: var(--ui-num-font);
  color: var(--ui-text);
}

.balance-row__metric-value--pct {
  display: inline-flex;
  align-items: center;
  font-size: 1rem;
  font-weight: 700;
  padding: 0.1rem 0.55rem 0.1rem 0.7rem;
  clip-path: polygon(9px 0, 100% 0, 100% 100%, 9px 100%, 0 50%);
}

.balance-row__metric-pct {
  display: inline-flex;
  align-items: center;
  font-size: 0.83rem;
  font-weight: 700;
  margin-left: 0.4rem;
  padding: 0.06rem 0.45rem 0.06rem 0.6rem;
  vertical-align: middle;
  clip-path: polygon(7px 0, 100% 0, 100% 100%, 7px 100%, 0 50%);
}

/*
 * 상세 지표 밴드(투자원금 · 보유종목 · 현금비중 · 마지막 리밸런싱 · 최대 이격도 · 시세갱신)는
 * 모바일에서도 그대로 보여준다. 폭이 좁을 땐 한 줄에 한 항목씩 세로로 나열(라벨 좌/값 우)해
 * 카드가 길어지더라도 정보 손실 없이 다 보이게 하고, 1200px 이상에서만 그리드로 압축한다.
 */
.balance-row__secondary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px dashed var(--ui-border);
}

.balance-row__secondary-item {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  min-width: 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed var(--ui-border);
}

.balance-row__secondary-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.balance-row__secondary-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  line-height: 1.3;
  color: var(--ui-text-muted);
  flex-shrink: 0;
}

.balance-row__secondary-value {
  font-size: 0.92rem;
  font-weight: 700;
  font-family: var(--ui-num-font);
  font-variant-numeric: tabular-nums;
  color: var(--ui-text-subtle);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: right;
}

.balance-row__secondary-value--muted {
  font-weight: 500;
  color: var(--ui-text-muted);
}

/* 목표 비중 대비 이격도가 큰(리밸런싱 필요) 종목이 있을 때 경고색으로 강조 */
.balance-row__secondary-value--warn {
  color: var(--ui-alert-warning-text);
}

/* PC 화면: 계좌 상세정보 가독성 강화 — 여백을 넓히고 글자를 키우며, 상세 지표를 그리드로 압축 */
@media (min-width: 1200px) {
  .balance-row {
    padding: 0.85rem 1.15rem;
  }

  .balance-row__title {
    font-size: 1.08rem;
  }

  .balance-row__tag,
  .balance-row__num,
  .balance-row__owner-tag {
    font-size: 0.9rem;
  }

  .balance-row__metrics {
    gap: 1.6rem;
  }

  .balance-row__metric:not(:first-child) {
    padding-left: 1.6rem;
  }

  .balance-row__metric-label {
    font-size: 0.86rem;
  }

  .balance-row__metric-value {
    font-size: 1.1rem;
  }

  .balance-row__metric-value--pct {
    font-size: 1.2rem;
  }

  .balance-row__metric-pct {
    font-size: 0.92rem;
  }

  .balance-row__secondary {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 0.5rem 1.5rem;
    margin-top: 0.7rem;
    padding-top: 0.65rem;
  }

  .balance-row__secondary-item {
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    gap: 0.1rem;
    padding-bottom: 0;
    border-bottom: none;
  }

  .balance-row__secondary-item:not(:first-child) {
    padding-left: 1.6rem;
    border-left: 1px solid var(--ui-border);
  }

  .balance-row__secondary-label {
    font-size: 0.88rem;
  }

  .balance-row__secondary-value {
    font-size: 1.02rem;
    text-align: left;
  }
}

@media (max-width: 767.98px) {
  /* 계좌명이 지표 열과 나란히 있으면 폭이 눌려 이름은 왼쪽에서 빈 듯 짜부라지고 지표만 오른쪽에 몰린다 — 계좌명을 윗줄로, 지표를 아랫줄로 분리 */
  .balance-row__top {
    flex-direction: column;
    align-items: stretch;
    min-height: 0;
    gap: 0.5rem;
  }

  .balance-row__name {
    flex: none;
  }

  /* 지표 칸이 내용 폭만큼만 좌우 끝에 걸쳐 가운데가 비어 보이던 것을 — 각 지표가 폭을 균등하게 나눠 갖도록 변경 */
  .balance-row__metrics {
    width: 100%;
    justify-content: flex-start;
  }

  .balance-row__metric {
    flex: 1 1 0;
    align-items: flex-start;
    min-width: 0;
  }
}
</style>
