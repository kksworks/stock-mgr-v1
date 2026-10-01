<template>
  <div class="dashboard-root dashboard-page pb-4 pb-xl-5 px-3 px-sm-4 px-xl-5">
    <!-- Header Section -->
    <div class="d-flex flex-column flex-lg-row justify-content-between align-items-stretch align-items-lg-center gap-3 mb-3 mt-2 mt-lg-3 dashboard-page-header">
      <h1 class="mb-0 d-flex align-items-center gap-3 h4 fw-bold dashboard-title">
        <MaterialIcon name="account_balance" size="2rem" class="text-primary" />
        <span class="mt-1">Dashboard</span>
      </h1>
      <div class="d-flex flex-wrap align-items-center gap-2 justify-content-lg-end dashboard-header-actions">

        <button v-if="authStore.isAuthenticated" type="button" class="btn btn-sm btn-tonal-neutral" @click="openGroupModal">
          <MaterialIcon name="tune" size="1.1rem" />
          <span class="d-none d-sm-inline">분류/노출 설정</span>
          <span class="d-sm-none">설정</span>
        </button>
        <button v-if="authStore.isAuthenticated" type="button" class="btn btn-sm btn-tonal-neutral" :disabled="refreshing" @click="doRefresh">
          <MaterialIcon name="sync" size="1.1rem" :class="{ 'rotate-animation': refreshing }" />
          <span class="d-none d-sm-inline">{{ refreshing ? '갱신 중…' : '현재가 갱신' }}</span>
          <span class="d-sm-none">갱신</span>
        </button>
        <router-link to="/balances" class="btn btn-sm btn-tonal-neutral">
          <MaterialIcon name="wallet" size="1.1rem" />
          <span class="d-none d-sm-inline">계좌 잔고</span>
          <span class="d-sm-none">잔고</span>
        </router-link>
      </div>
    </div>

    <div v-if="showMarketOverviewStrip" class="dashboard-market-overview mb-3 mb-lg-4 mt-1 stock-fade-in">
      <template v-for="sec in marketIndexSections" :key="sec.id">
        <div v-if="sec.items.length > 0" class="dashboard-index-row">
          <div class="dashboard-index-row-label">
            <MaterialIcon :name="sec.icon" size="1rem" class="text-primary opacity-90" />
            <span>{{ sec.title }}</span>
          </div>
          <div class="dashboard-index-row-grid">
            <component
              v-for="idx in sec.items"
              :key="idx.cardId"
              :is="idx.naverUrl ? 'a' : 'div'"
              class="naver-index-card-wrap text-reset"
              :class="{ 'text-decoration-none': !!idx.naverUrl }"
              v-bind="idx.naverUrl ? { href: idx.naverUrl, target: '_blank', rel: 'noopener noreferrer' } : {}"
              :title="idx.naverUrl ? `${idx.name} — 네이버 증권` : undefined"
            >
              <div class="card index-card h-100">
                <div class="card-body p-2 p-md-3 d-flex flex-column gap-2">
                  <div class="d-flex justify-content-between align-items-center">
                    <span class="fw-bold text-muted small letter-spacing-1">{{ idx.name }}</span>
                    <MaterialIcon :name="indexTrendIcon(idx.prev_day_change)"
                                  :class="indexTrendClass(idx.prev_day_change)"
                                  size="1.15rem" />
                  </div>
                  <div class="dashboard-index-card-main d-flex justify-content-between gap-2">
                    <span class="tabular-nums dashboard-index-price">{{ formatIndexPrice(idx.price) }}</span>
                    <div class="dashboard-index-delta d-flex gap-1">
                      <span class="dashboard-index-delta-amount tabular-nums" :class="indexTrendClass(idx.prev_day_change)">
                        <MaterialIcon :name="indexTrendIcon(idx.prev_day_change)" size="0.95rem" />
                        {{ formatIndexDelta(idx.prev_day_change) }}{{ indexDeltaUnit(idx) }}
                      </span>
                      <span class="dashboard-index-pct-flag tabular-nums" :class="indexPctBadgeClass(idx.prev_day_change_pct)">
                        {{ formatIndexPct(idx.prev_day_change_pct) }}
                      </span>
                    </div>
                  </div>
                  <div class="dashboard-index-card-footer d-flex align-items-center justify-content-between">
                    <span v-if="formatIndexPriceUpdateLine(idx)" class="dashboard-index-update-line text-muted">
                      {{ formatIndexPriceUpdateLine(idx) }}
                    </span>
                    <span class="dashboard-index-prevclose d-none d-xl-inline-flex tabular-nums text-muted">
                      전일종가 {{ formatIndexPrevClose(idx) }}
                    </span>
                  </div>
                </div>
                <div class="index-card-line" :class="indexLineClass(idx.prev_day_change)"></div>
              </div>
            </component>
          </div>
        </div>
      </template>

      <!-- 계좌전체 요약: 전체 폭 히어로 -->
      <div v-if="portfolioTotals.count > 0" class="dashboard-index-row">
        <div class="card index-card dash-portfolio-hero">
          <div class="card-body p-3 p-md-4">
            <div class="d-flex flex-column flex-xl-row align-items-xl-center justify-content-xl-between gap-3">
              <div class="dash-portfolio-hero__headline">
                <div class="d-flex align-items-center gap-2 mb-1">
                  <MaterialIcon name="api" size="1.15rem" class="dash-portfolio-hero-label" />
                  <span class="fw-bold dash-portfolio-hero-label letter-spacing-1">PORTFOLIO ROI</span>
                </div>
                <span class="dashboard-index-price dash-portfolio-hero-number">
                  {{ portfolioTotals.roi >= 0 ? '+' : '' }}{{ portfolioTotals.roi.toFixed(2) }}%
                </span>
                <div class="dash-portfolio-hero-label fw-bold mt-1">
                  전일대비 {{ formatPrevDayPercent(portfolioTotals.prev_day_return_vs_principal_pct) }}
                </div>
              </div>
              <div class="dash-portfolio-hero__stats">
                <div class="dash-portfolio-hero__stat">
                  <span class="dash-portfolio-hero__stat-label">계좌 수</span>
                  <span class="dash-portfolio-hero__stat-value tabular-nums">{{ portfolioTotals.count }}개</span>
                </div>
                <div class="dash-portfolio-hero__stat">
                  <span class="dash-portfolio-hero__stat-label">투자 원금</span>
                  <span class="dash-portfolio-hero__stat-value tabular-nums">{{ formatMoneyKR(portfolioTotals.principal) }}</span>
                </div>
                <div class="dash-portfolio-hero__stat">
                  <span class="dash-portfolio-hero__stat-label">총 평가자산</span>
                  <span class="dash-portfolio-hero__stat-value tabular-nums">{{ formatMoneyKR(portfolioTotals.total_asset_value) }}</span>
                </div>
              </div>
            </div>
            <div v-if="portfolioPriceUpdateLine" class="dash-portfolio-hero__meta">
              <MaterialIcon name="schedule" size="0.85rem" />
              시세 갱신 {{ portfolioPriceUpdateLine }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Status Bar -->
    <div v-if="overview.length > 0" class="dashboard-status-bar d-flex align-items-center justify-content-end mb-3 mb-lg-4">
      <div class="d-flex align-items-center gap-3 me-2">
        <span class="text-muted d-none d-md-inline fw-medium dashboard-status-text">총 {{ overview.length }}개 계좌</span>
        <div v-if="refreshing" class="spinner-border spinner-border-sm text-primary" role="status" style="width: 0.75rem; height: 0.75rem;"></div>
      </div>
    </div>

    <!-- Conditional Views -->
    <div v-if="loading && overview.length === 0" class="py-5">
      <PageLoadingPlaceholder variant="table" :rows="8" />
    </div>

    <div v-else-if="overview.length === 0 && !loading" class="card shadow-sm border-0 rounded-4 my-4 mx-auto dashboard-empty-accounts stock-fade-in">
      <div class="card-body text-center py-4 py-md-5 text-muted">
        <MaterialIcon name="info" size="3rem" class="opacity-10 mb-3" />
        <p class="mb-0 text-secondary">등록된 계좌가 없습니다. <br/><router-link to="/accounts" class="fw-bold text-primary text-decoration-none border-bottom">계좌 설정</router-link>에서 추가해 주세요.</p>
      </div>
    </div>

    <div v-else class="dashboard-main-content stock-fade-in">
      <div class="row g-3 g-xl-4">
        <div class="col-12">
          <!-- ========== 카드 뷰 (통합) ========== -->

            <!-- 분류별 큰 카드 + 아코디언(계좌) -->
            <div
              v-for="(group, gIdx) in dashboardVisibleGroups"
              :key="`card-g-${group.category.id}`"
              class="mb-4 mb-xxl-5 dashboard-account-group"
              :style="{ '--category-color': getCategoryColor(group.category, gIdx) }"
            >
              <div
                class="card border-0 shadow-sm rounded-4 overflow-hidden dashboard-group-big-card"
                :style="{ borderLeft: '6px solid var(--category-color)' }"
              >
                <!-- ── 그룹 헤더: 항상 노출 ── -->
                <div class="dashboard-group-big-card__header p-3 p-md-4">

                  <!-- 상단 행: 이름(타이포그래피 강조) -->
                  <div class="d-flex align-items-start gap-3">
                    <div class="min-w-0 flex-grow-1">
                      <div class="dashboard-group-big-card__title text-truncate" :style="{ color: 'var(--category-color)' }">{{ group.category.name }}</div>
                      <div class="dashboard-group-big-card__sub">{{ group.items.length }}개 계좌</div>
                    </div>
                  </div>

                  <!-- KPI 행: 모바일부터 전부 표시 -->
                  <div class="dashboard-group-kpi-row mt-3">
                    <div class="dashboard-group-kpi-item">
                      <div class="dashboard-group-kpi-label">총 평가</div>
                      <div class="dashboard-group-kpi-value" :style="{ color: 'var(--category-color)' }">{{ formatMoneyWonFull(group.total_asset_value) }}</div>
                    </div>
                    <div class="dashboard-group-kpi-item">
                      <div class="dashboard-group-kpi-label">투자 원금</div>
                      <div class="dashboard-group-kpi-value" style="color: var(--ui-text-subtle);">{{ formatMoneyWonFull(group.principal) }}</div>
                    </div>
                    <div class="dashboard-group-kpi-item">
                      <div class="dashboard-group-kpi-label">평가 손익</div>
                      <div class="dashboard-group-kpi-value" :class="group.investment_return >= 0 ? 'text-profit' : 'text-loss'">
                        {{ formatSignedMoneyWonFull(group.investment_return) }}
                        <span class="dashboard-kpi-pct" :class="pctFlagClass(group.investment_return)">{{ group.investment_return >= 0 ? '+' : '' }}{{ group.roi.toFixed(2) }}%</span>
                      </div>
                    </div>
                    <div v-if="group.prev_day_return_vs_principal_pct != null" class="dashboard-group-kpi-item">
                      <div class="dashboard-group-kpi-label">전일대비</div>
                      <div class="dashboard-group-kpi-value" :class="prevDayChangeClass(group.prev_day_change_sum)">
                        {{ formatPrevDayMoney(group.prev_day_change_sum) }}
                        <span class="dashboard-kpi-pct" :class="pctFlagClass(group.prev_day_change_sum)">{{ formatPrevDayPercent(group.prev_day_return_vs_principal_pct) }}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 차트 영역 -->
                <div class="dashboard-group-charts border-top border-light-subtle px-3 px-md-4 py-3" @click.stop>
                  <div class="row g-3 align-items-stretch">
                    <div class="col-12 col-xl-7">
                      <div class="dashboard-chart-label">최근 12개월 수익금 추이</div>
                      <div class="dashboard-group-chart-wrap">
                        <Line
                          v-if="groupYearProfitSeries(group).data.length"
                          :key="`dash-line-${groupCategoryKey(group)}-${groupTrendMeta(group).end || ''}`"
                          :data="groupLineChartConfig(group, gIdx)"
                          :options="dashboardGroupLineOptions"
                        />
                        <div v-else class="text-muted small py-4 text-center">표시할 월별 데이터가 없습니다.</div>
                      </div>
                    </div>
                    <div class="col-12 col-xl-5">
                      <div class="dashboard-chart-label">자산분류별 비중</div>
                      <div
                        class="dashboard-group-chart-wrap dashboard-group-chart-wrap--bar"
                        :style="{ height: groupBarChartHeight(group) + 'px' }"
                      >
                        <Bar
                          v-if="groupHoldingsBreakdown(group).data.length"
                          :key="`dash-bar-${groupCategoryKey(group)}-${group.items.map((a) => a.account.id).join('-')}`"
                          :data="groupBarChartConfig(group, gIdx)"
                          :options="dashboardGroupBarOptions"
                          :plugins="[ChartDataLabels]"
                        />
                        <div v-else class="text-muted small py-4 text-center">보유 종목이 없습니다.</div>
                      </div>
                    </div>
                  </div>
                  <div v-if="groupPriceUpdateLine(group)" class="text-muted mt-2 pt-2 border-top border-light-subtle" style="font-size: 0.8rem;">
                    시세 {{ groupPriceUpdateLine(group) }}
                  </div>

                  <!-- ── 더보기 버튼: 차트 아래 카드 내부 하단 ── -->
                  <div class="dashboard-group-expand-bar mt-3 pt-2 border-top border-light-subtle">
                    <button
                      type="button"
                      class="dashboard-group-expand-btn"
                      @click.stop="toggleDashboardGroup(groupCategoryKey(group))"
                    >
                      <span class="dashboard-group-expand-btn__text">
                        {{ isDashboardGroupExpanded(groupCategoryKey(group)) ? '계좌 목록 접기' : `계좌 ${group.items.length}개 보기` }}
                      </span>
                      <MaterialIcon
                        :name="isDashboardGroupExpanded(groupCategoryKey(group)) ? 'expand_less' : 'expand_more'"
                        size="1.1rem"
                        class="dashboard-group-expand-btn__icon"
                      />
                    </button>
                  </div>
                </div>
              </div>

              <!-- 하위 계좌 목록 (아코디언) -->
              <transition name="dash-acc-slide">
                <div v-show="isDashboardGroupExpanded(groupCategoryKey(group))" class="dashboard-acc-list mt-2">
                  <div
                    v-for="acc in group.items"
                    :key="`card-acc-${acc.account.id}`"
                    class="dash-acc-row"
                    :style="{ borderLeft: '3px solid var(--category-color)' }"
                    @click.stop="$router.push(`/balances/${acc.account.id}`)"
                  >
                    <div class="dash-acc-row__top">
                      <!-- 왼쪽: 계좌명 + 메타 -->
                      <div class="dash-acc-row__name min-w-0">
                        <div class="dash-acc-row__title text-truncate d-flex align-items-center gap-1">
                          <span class="text-truncate">{{ acc.account.account_name }}</span>
                          <MaterialIcon name="open_in_new" size="0.85rem" class="opacity-40 flex-shrink-0" />
                        </div>
                        <div class="dash-acc-row__meta">
                          <span v-if="acc.portfolio_name" class="dash-acc-row__tag" :style="{ color: 'var(--category-color)' }">#{{ acc.portfolio_name }}</span>
                          <span v-if="isSharedAccount(acc)" class="dash-acc-row__owner-tag">{{ acc.account.owner || '공유' }}</span>
                          <span v-if="accountPriceUpdateLine(acc)" class="dash-acc-row__time">
                            <MaterialIcon name="schedule" size="0.68rem" class="opacity-50" />
                            {{ accountPriceUpdateLine(acc) }}
                          </span>
                          <span v-else class="dash-acc-row__time opacity-50">시세 없음</span>
                        </div>
                      </div>

                      <!-- 오른쪽: 핵심 지표 -->
                      <div class="dash-acc-row__metrics">
                        <!-- 총 자산 -->
                        <div class="dash-acc-row__metric">
                          <div class="dash-acc-row__metric-label">총 자산</div>
                          <div class="dash-acc-row__metric-value dash-acc-row__metric-value--accent">{{ formatMoneyWonFull(acc.total_asset_value) }}</div>
                        </div>
                        <!-- 수익률 (sm 이상) -->
                        <div class="dash-acc-row__metric d-none d-sm-flex">
                          <div class="dash-acc-row__metric-label">수익률</div>
                          <div class="dash-acc-row__metric-value dash-acc-row__metric-value--pct" :class="pctFlagClass(acc.investment_return)">
                            {{ acc.investment_return >= 0 ? '+' : '' }}{{ (acc.principal > 0 ? (acc.investment_return / acc.principal * 100) : 0).toFixed(1) }}%
                          </div>
                        </div>
                        <!-- 전일대비 -->
                        <div v-if="acc.prev_day_return_vs_principal_pct != null" class="dash-acc-row__metric">
                          <div class="dash-acc-row__metric-label">전일대비</div>
                          <div class="dash-acc-row__metric-value" :class="prevDayChangeClass(acc.prev_day_asset_change)">
                            {{ formatPrevDayMoney(acc.prev_day_asset_change) }}
                            <span class="dash-acc-row__metric-pct" :class="pctFlagClass(acc.prev_day_asset_change)">{{ formatPrevDayPercent(acc.prev_day_return_vs_principal_pct) }}</span>
                          </div>
                        </div>
                        <MaterialIcon name="chevron_right" size="1rem" class="flex-shrink-0" style="color: var(--ui-text-muted); opacity: 0.5;" />
                      </div>
                    </div>

                    <!-- 상세 지표: 검정 일변도를 피하려고 분류색 강조(투자원금·보유종목)와 상태 플래그(현금비중·리밸런싱·이격도)를 함께 사용 -->
                    <div class="dash-acc-row__secondary">
                      <div class="dash-acc-row__secondary-item">
                        <span class="dash-acc-row__secondary-label">투자 원금</span>
                        <span class="dash-acc-row__secondary-value dash-acc-row__secondary-value--accent">{{ formatMoneyWonFull(acc.principal) }}</span>
                      </div>
                      <div class="dash-acc-row__secondary-item">
                        <span class="dash-acc-row__secondary-label">보유 종목</span>
                        <span class="dash-acc-row__secondary-value dash-acc-row__secondary-value--accent">{{ accountHoldingsCount(acc) }}종목</span>
                      </div>
                      <div class="dash-acc-row__secondary-item">
                        <span class="dash-acc-row__secondary-label">현금 비중</span>
                        <span class="dash-acc-row__secondary-value" :class="cashRatioFlagClass(accountCashRatioPct(acc))">{{ accountCashRatioPct(acc).toFixed(1) }}%</span>
                      </div>
                      <div class="dash-acc-row__secondary-item">
                        <span class="dash-acc-row__secondary-label">마지막 리밸런싱</span>
                        <span class="dash-acc-row__secondary-value" :class="rebalanceFlagClass(acc)">{{ accountLastRebalancedLabel(acc) }}</span>
                      </div>
                      <div v-if="accountMaxDeviationPct(acc) != null" class="dash-acc-row__secondary-item">
                        <span class="dash-acc-row__secondary-label">최대 이격도</span>
                        <span class="dash-acc-row__secondary-value" :class="deviationClass(accountMaxDeviationPct(acc))">{{ accountMaxDeviationPct(acc).toFixed(1) }}%</span>
                      </div>
                      <div class="dash-acc-row__secondary-item">
                        <span class="dash-acc-row__secondary-label">계좌 번호</span>
                        <span class="dash-acc-row__secondary-value dash-acc-row__secondary-value--muted">{{ acc.account.account_number || '—' }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </transition>
            </div>
        </div>
      </div>
    </div>

    <!-- Active Loading Overlay Overlay -->
    <div v-if="refreshing && overview.length > 0" class="position-fixed bottom-0 end-0 m-4 shadow-sm p-3 dashboard-refresh-toast rounded-4 border d-flex align-items-center gap-2 stock-fade-in-up" style="z-index: 2000;">
       <div class="spinner-border spinner-border-sm text-primary" role="status"></div>
       <div class="fw-bold text-primary x-small">데이터 갱신 중…</div>
    </div>

    <!-- Group Management Modal (Clean) -->
    <div class="modal fade" id="groupManagerModal" tabindex="-1" aria-hidden="true" ref="groupModalRef">
      <div class="modal-dialog modal-lg modal-dialog-centered">
        <div class="modal-content shadow-sm border-0 rounded-4">
          <div class="modal-header border-0 pb-2 pt-4 px-4 bg-light bg-opacity-10">
            <h5 class="modal-title fw-bold d-flex align-items-center gap-2 h5">
              <MaterialIcon name="tune" class="text-primary opacity-75" />
              대시보드 설정
            </h5>
            <button type="button" class="btn-close shadow-none" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body px-4 pb-4">
            <p class="small text-muted mb-3 mb-md-4">
              분류·노출·대시보드 체크 선택은 <strong class="text-body">현재 로그인한 계정</strong>마다 이 브라우저에 따로 저장됩니다. 다른 계정으로 로그인하면 해당 계정 설정으로 복구됩니다.
            </p>
            <!-- 1. Visibility Settings -->
            <div class="mb-4 p-3 bg-light rounded-3 border border-light-subtle shadow-sm">
              <div class="form-check form-switch pt-1">
                <input class="form-check-input cursor-pointer" type="checkbox" role="switch" id="showSharedSwitch" v-model="showShared" @change="persistVisibility">
                <label class="form-check-label ms-2 cursor-pointer fw-bold small text-secondary" for="showSharedSwitch">공유받은 계좌를 대시보드 및 합계에 표시</label>
              </div>
            </div>

            <div class="row g-3">
              <!-- 2. Category Management -->
              <div class="col-md-5">
                <label class="fw-bold small mb-2 text-muted px-1">분류 그룹 편집</label>
                <div class="input-group input-group-sm mb-3 shadow-sm rounded-3 overflow-hidden">
                  <input v-model="newCatName" type="text" class="form-control border-light-subtle" placeholder="새 분류 이름" @keyup.enter="addCategory">
                  <button class="btn btn-primary px-3 fw-bold" type="button" @click="addCategory">추가</button>
                </div>
                <div class="list-group list-group-flush border rounded-3 overflow-hidden shadow-sm overflow-auto" style="max-height: 250px;">
                    <div v-for="(cat, idx) in categories" :key="cat.id" class="list-group-item d-flex align-items-center justify-content-between py-2 px-3 shadow-none">
                      <div class="d-flex align-items-center gap-2 min-w-0">
                        <label class="cat-color-swatch" :style="{ background: cat.color || defaultCategoryHex(idx) }" title="분류 색상 선택">
                          <input type="color" :value="cat.color || defaultCategoryHex(idx)" @input="setCategoryColor(cat, $event.target.value)">
                        </label>
                        <span class="fw-bold text-dark small text-truncate">{{ cat.name }}</span>
                      </div>
                     <div class="d-flex gap-1">
                        <button class="btn btn-outline-secondary btn-sm p-1" :disabled="idx === 0" @click="moveCategory(idx, -1)" aria-label="위로 이동">
                          <MaterialIcon name="arrow_upward" size="1rem" />
                        </button>
                        <button class="btn btn-outline-secondary btn-sm p-1 border-0" :disabled="idx === categories.length - 1" @click="moveCategory(idx, 1)" aria-label="아래로 이동">
                          <MaterialIcon name="arrow_downward" size="1rem" />
                        </button>
                        <button class="btn btn-outline-danger btn-sm p-1 ms-1" @click="removeCategory(cat.id)" aria-label="삭제">
                          <MaterialIcon name="delete" size="1rem" />
                        </button>
                     </div>
                   </div>
                   <div v-if="categories.length === 0" class="list-group-item text-center text-muted py-4 small">등록된 분류 없음</div>
                </div>
              </div>

              <!-- 3. Account Assignment -->
              <div class="col-md-7">
                <label class="fw-bold small mb-2 text-muted px-1">계좌별 그룹 할당</label>
                <div class="border rounded-3 overflow-hidden overflow-auto shadow-sm" style="max-height: 300px; background: var(--ui-surface);">
                  <table class="table table-sm table-hover align-middle mb-0 small">
                    <thead class="bg-light bg-opacity-50">
                      <tr>
                        <th class="ps-3 py-2 border-0">계좌명</th>
                        <th class="py-2 border-0 text-center" style="width: 70px;">표시</th>
                        <th class="pe-3 py-2 border-0 text-end">분류 지정</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="acc in settingsAccountList" :key="`assign-${acc.account.id}`" class="border-light-subtle">
                        <td class="ps-3 py-2 text-truncate fw-medium text-dark" style="max-width: 140px;">
                          {{ acc.account.account_name }}
                          <span
                            v-if="authStore.isAuthenticated && String(acc.account.user_id) !== String(authStore.user?.id)"
                            class="badge bg-light text-muted border ms-1"
                            style="font-size: 10px; font-weight: 500;"
                          >공유</span>
                        </td>
                        <td class="text-center align-middle py-1">
                          <div class="form-check form-switch p-0 m-0 d-flex justify-content-center">
                            <input
                              class="form-check-input cursor-pointer ms-0 mt-0 shadow-none"
                              type="checkbox"
                              role="switch"
                              :checked="!hiddenAccountIds.has(acc.account.id)"
                              @change="toggleAccountVisibility(acc.account.id, $event.target.checked)"
                            >
                          </div>
                        </td>
                        <td class="pe-3 py-1 text-end align-middle">
                          <select class="form-select form-select-sm py-0 border-0 shadow-none text-primary fw-bold" :value="accountCategoryMap[acc.account.id] || 'default'" @change="assignCategory(acc.account.id, $event.target.value)">
                            <option value="default" class="text-muted fw-normal">미분류</option>
                            <option v-for="cat in categories" :key="`opt-${cat.id}`" :value="cat.id">{{ cat.name }}</option>
                          </select>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-footer border-0 px-4 pb-4 pt-2">
            <button type="button" class="btn btn-secondary w-100 py-2 fw-bold rounded-pill" data-bs-dismiss="modal">확인</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { Modal } from 'bootstrap'
import { authStore } from '../stores/auth'
import { accountApi, userApi, stockApi, getApiErrorMessage } from '../api'
import { pollUntilBalanceOverviewFresh } from '../composables/useBalanceRefreshPolling'
import PageLoadingPlaceholder from '../components/PageLoadingPlaceholder.vue'
import MaterialIcon from '../components/MaterialIcon.vue'
import {
  formatPrevDayMoney,
  formatPrevDayPercent,
  prevDayChangeClass,
} from '../utils/prevDayAsset'
import { Line, Bar } from 'vue-chartjs'
import ChartDataLabels from 'chartjs-plugin-datalabels'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  CategoryScale,
  BarElement,
  LineController,
  BarController,
} from 'chart.js'

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  Filler,
  LineElement,
  LinearScale,
  PointElement,
  CategoryScale,
  BarElement,
  LineController,
  BarController,
)

const emit = defineEmits(['flash'])
const HIDDEN_ACCOUNTS_KEY = 'mainDashboard_hiddenAccountIds'
const CATEGORIES_KEY = 'balance_categories_config'
const ACCOUNT_CAT_MAP_KEY = 'balance_account_category_map'
const SHOW_SHARED_KEY = 'balance_show_shared'

/** 로그인 사용자별 / 비로그인 guest 별로 대시보드 설정 분리 */
function dashboardPrefsSegment() {
  if (authStore.isAuthenticated && authStore.user?.id != null && String(authStore.user.id) !== '') {
    return `u${String(authStore.user.id)}`
  }
  return 'guest'
}

function scopedDashboardKey(baseKey) {
  return `${baseKey}__${dashboardPrefsSegment()}`
}

/**
 * 계정(또는 guest) 전용 키에 없으면 예전 전역 키를 한 번 읽어 이전 후 제거(업그레이드).
 */
function readScopedOrLegacyJson(baseKey, defaultValue) {
  const sk = scopedDashboardKey(baseKey)
  const scopedRaw = localStorage.getItem(sk)
  if (scopedRaw != null && scopedRaw !== '') {
    try {
      return JSON.parse(scopedRaw)
    } catch {
      /* fall through */
    }
  }
  const legacyRaw = localStorage.getItem(baseKey)
  if (legacyRaw != null && legacyRaw !== '') {
    try {
      const v = JSON.parse(legacyRaw)
      try {
        localStorage.setItem(sk, JSON.stringify(v))
      } catch {
        /* ignore */
      }
      return v
    } catch {
      /* ignore */
    }
  }
  return defaultValue
}

function readScopedOrLegacyString(baseKey, defaultValue) {
  const sk = scopedDashboardKey(baseKey)
  let v = localStorage.getItem(sk)
  if (v != null && v !== '') return v
  const leg = localStorage.getItem(baseKey)
  if (leg != null && leg !== '') {
    try {
      localStorage.setItem(sk, leg)
    } catch {
      /* ignore */
    }
    return leg
  }
  return defaultValue
}

const overview = ref([])
const loading = ref(true)
const refreshing = ref(false)
const hiddenAccountIds = ref(new Set())
const marketIndices = ref([])
/** 분류(그룹)별 계좌 아코디언 — 기본 접힘 */
const expandedDashboardGroups = ref(new Set())

/** 분류 카드 좌측 컬러(--dash-cat-1..8, 이 파일 scoped style)와 동일 순서 — 카드 색과 라인차트 색이 항상 일치하도록 */
const CHART_LINE_HEX = ['#10926d', '#cb7716', '#524cda', '#d22750', '#138ead', '#8d3bdf', '#659d1c', '#da5b1b']
/** 자산분류 막대그래프: 원색 그대로는 과해서 살짝 톤다운 + 확장 2색(기타/미분류용은 또렷한 회색) */
const CHART_COLORS = [
  '#0ba875', '#e78b09', '#5956eb', '#eb2e53',
  '#07a4c3', '#9e44f1', '#75b812', '#f26611',
  '#0895d8', '#64748b',
]

function hexToRgba(hex, alpha) {
  const h = String(hex || '').replace('#', '')
  if (h.length !== 6) return `rgba(100,116,139,${alpha})`
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r},${g},${b},${alpha})`
}

/** 대시보드 선그래프 Y축: 억 / 천만 / 만 단위로 짧게 */
function formatDashboardLineYAxisWon(n) {
  if (!Number.isFinite(n)) return ''
  if (n === 0) return '₩0'
  const sign = n < 0 ? '-' : ''
  const v = Math.abs(n)
  const body = (scaled) => {
    const a = Math.abs(scaled)
    if (a >= 100) return Math.round(scaled).toLocaleString()
    if (a >= 10) return String(Math.round(scaled * 10) / 10).replace(/\.0$/, '')
    const t = Math.round(scaled * 100) / 100
    return String(t).replace(/\.?0+$/, '')
  }
  if (v >= 1e8) return `${sign}₩${body(v / 1e8)}억`
  if (v >= 1e7) return `${sign}₩${body(v / 1e7)}천만`
  if (v >= 1e4) return `${sign}₩${body(v / 1e4)}만`
  return `${sign}₩${Math.round(v).toLocaleString()}`
}

/** 백엔드 crawler.fetch_index_price와 동일 (네이버 시세 지수 페이지) */
function naverSiseIndexPageUrl(code) {
  return `https://finance.naver.com/sise/sise_index.naver?code=${encodeURIComponent(String(code).toUpperCase())}`
}

/** 백엔드 crawler.fetch_world_sise_quote와 동일 (네이버 해외 시세지수) */
function naverWorldSisePageUrl(symbol) {
  return `https://finance.naver.com/world/sise.naver?symbol=${encodeURIComponent(symbol)}`
}

/** 백엔드 crawler.fetch_exchange_detail_quote와 동일 (네이버 시장지표 환율) */
function naverExchangeDetailPageUrl(marketindexCd) {
  return `https://finance.naver.com/marketindex/exchangeDetail.naver?marketindexCd=${encodeURIComponent(marketindexCd)}`
}

/** API quote에서 카드에 쓸 필드만 사용 (불필요 키가 name/naverUrl 등을 덮어쓰지 않도록) */
function pickIndexQuote(raw) {
  if (!raw || typeof raw !== 'object') return {}
  return {
    price: raw.price,
    prev_day_change: raw.prev_day_change,
    prev_day_change_pct: raw.prev_day_change_pct,
    price_updated_at: raw.price_updated_at,
  }
}

function indexNum(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function indexChangeDir(prevChange) {
  const n = indexNum(prevChange)
  if (n === null) return 'flat'
  if (n > 0) return 'up'
  if (n < 0) return 'down'
  return 'flat'
}

function indexTrendIcon(prevChange) {
  const d = indexChangeDir(prevChange)
  if (d === 'up') return 'trending_up'
  if (d === 'down') return 'trending_down'
  return 'trending_flat'
}

function indexTrendClass(prevChange) {
  const d = indexChangeDir(prevChange)
  if (d === 'up') return 'text-profit'
  if (d === 'down') return 'text-loss'
  return 'text-muted'
}

function indexLineClass(prevChange) {
  const d = indexChangeDir(prevChange)
  if (d === 'up') return 'bg-profit'
  if (d === 'down') return 'bg-loss'
  return 'bg-secondary'
}

function indexPctBadgeClass(prevPct) {
  const n = indexNum(prevPct)
  if (n === null) return 'bg-secondary-subtle text-muted'
  if (n > 0) return 'bg-profit-soft'
  if (n < 0) return 'bg-loss-soft'
  return 'bg-secondary-subtle text-muted'
}

/** 계좌/분류 카드의 퍼센트 수치를 작은 플래그 배지로 표시할 때 쓰는 색상 클래스 */
function pctFlagClass(n) {
  const v = Number(n)
  if (!Number.isFinite(v) || v === 0) return 'bg-secondary-subtle text-muted'
  return v > 0 ? 'bg-profit-soft' : 'bg-loss-soft'
}

function formatIndexPrice(v) {
  const n = indexNum(v)
  if (n === null || n <= 0) return '—'
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatIndexDelta(v) {
  const n = indexNum(v)
  if (n === null) return '—'
  const sign = n > 0 ? '+' : ''
  return sign + n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function formatIndexPct(v) {
  const n = indexNum(v)
  if (n === null) return '—'
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toFixed(2)}%`
}

/** PC 카드 전용 보조 정보: 등락 단위(포인트/원) */
function indexDeltaUnit(idx) {
  return idx?.cardId === 'USDKRW' ? '원' : 'pt'
}

/** PC 카드 전용 보조 정보: 전일 종가 */
function formatIndexPrevClose(idx) {
  const price = indexNum(idx?.price)
  const change = indexNum(idx?.prev_day_change)
  if (price === null || change === null) return '—'
  const prevClose = price - change
  return prevClose.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function indexTrendLabel(prevChange) {
  const dir = indexChangeDir(prevChange)
  if (dir === 'up') return '상승'
  if (dir === 'down') return '하락'
  return '보합'
}

function indexSourceLabel(idx) {
  if (idx?.cardId === 'USDKRW') return '네이버 시장지표'
  if (idx?.section === 'domestic') return '네이버 국내지수'
  if (idx?.section === 'global') return '네이버 해외지수'
  return '네이버'
}

function formatSignedMoneyKR(v) {
  const n = indexNum(v)
  if (n === null) return '—'
  const sign = n > 0 ? '+' : n < 0 ? '-' : ''
  return sign + formatMoneyKR(Math.abs(n))
}

/** 분류 합산 영역: 억·만 축약 없이 원 단위 전체 표시 */
function formatMoneyWonFull(val) {
  if (!Number.isFinite(Number(val))) return '₩0'
  return '₩' + Math.round(Number(val)).toLocaleString()
}

function formatSignedMoneyWonFull(v) {
  const n = indexNum(v)
  if (n === null) return '—'
  const sign = n > 0 ? '+' : n < 0 ? '-' : ''
  return sign + '₩' + Math.abs(Math.round(n)).toLocaleString()
}

async function loadMarketIndices() {
  try {
    const { data } = await stockApi.getTickerPrices(['KOSPI', 'KOSDAQ', 'NASDAQ', 'SP500', 'USDKRW'])

    const results = []
    // 티커 대소문자 구분 없이 처리하기 위해 키 이름을 대문자로 변환해서 체크
    const normalizedData = {}
    if (data && typeof data === 'object') {
       Object.keys(data).forEach(k => { normalizedData[k.toUpperCase()] = data[k] })
    }

    if (normalizedData.KOSPI) {
      results.push({
        ...pickIndexQuote(normalizedData.KOSPI),
        cardId: 'KOSPI',
        section: 'domestic',
        name: 'KOSPI',
        naverUrl: naverSiseIndexPageUrl('KOSPI'),
      })
    }
    if (normalizedData.KOSDAQ) {
      results.push({
        ...pickIndexQuote(normalizedData.KOSDAQ),
        cardId: 'KOSDAQ',
        section: 'domestic',
        name: 'KOSDAQ',
        naverUrl: naverSiseIndexPageUrl('KOSDAQ'),
      })
    }
    if (normalizedData.NASDAQ) {
      results.push({
        ...pickIndexQuote(normalizedData.NASDAQ),
        cardId: 'NASDAQ',
        section: 'global',
        name: '나스닥',
        naverUrl: naverWorldSisePageUrl('NAS@IXIC'),
      })
    }
    if (normalizedData.SP500) {
      results.push({
        ...pickIndexQuote(normalizedData.SP500),
        cardId: 'SP500',
        section: 'global',
        name: 'S&P 500',
        naverUrl: naverWorldSisePageUrl('SPI@SPX'),
      })
    }
    if (normalizedData.USDKRW) {
      results.push({
        ...pickIndexQuote(normalizedData.USDKRW),
        cardId: 'USDKRW',
        section: 'fx',
        name: 'USD/KRW',
        naverUrl: naverExchangeDetailPageUrl('FX_USDKRW'),
      })
    }
    
    marketIndices.value = results
  } catch (e) {
    console.warn("[Dashboard] Failed to load market indices", e)
  }
}

/** 상단 시세 카드: 국내증시 → 해외증시 → 환율 순 (데이터 있는 구역만 표시) */
const marketIndexSections = computed(() => {
  const domestic = []
  const global = []
  const fx = []
  for (const idx of marketIndices.value) {
    if (idx.section === 'domestic') domestic.push(idx)
    else if (idx.section === 'global') global.push(idx)
    else if (idx.section === 'fx') fx.push(idx)
  }
  return [
    { id: 'domestic', title: '국내증시', icon: 'location_city', items: domestic },
    { id: 'global', title: '해외증시', icon: 'public', items: global },
    { id: 'fx', title: '환율', icon: 'currency_exchange', items: fx },
  ]
})

// Grouping & Visibility State (계정별 loadDashboardPrefsForUser에서 채움)
const categories = ref([])
const accountCategoryMap = ref({})
const showShared = ref(true)

function loadDashboardGroupingPrefs() {
  const rawCats = readScopedOrLegacyJson(CATEGORIES_KEY, [])
  categories.value = Array.isArray(rawCats) ? rawCats : []
  const rawMap = readScopedOrLegacyJson(ACCOUNT_CAT_MAP_KEY, {})
  accountCategoryMap.value = rawMap && typeof rawMap === 'object' && !Array.isArray(rawMap) ? rawMap : {}
  /* 비로그인: 공개 계좌만 보므로 항상 전체 노출 (showShared=false + user 없음 필터 버그 방지) */
  if (!authStore.isAuthenticated) {
    showShared.value = true
    return
  }
  const rawShow = readScopedOrLegacyJson(SHOW_SHARED_KEY, true)
  showShared.value = typeof rawShow === 'boolean' ? rawShow : true
}

function loadHiddenAccountsForUser() {
  const skHidden = scopedDashboardKey(HIDDEN_ACCOUNTS_KEY)
  let raw = localStorage.getItem(skHidden)
  if (raw) {
    try {
      hiddenAccountIds.value = new Set(JSON.parse(raw))
    } catch (e) {
      console.error('Failed to parse hidden accounts', e)
      hiddenAccountIds.value = new Set()
    }
  } else {
    hiddenAccountIds.value = new Set()
  }
}

function loadDashboardPrefsForUser() {
  loadDashboardGroupingPrefs()
  loadHiddenAccountsForUser()
}

// ── Server-side preference sync ────────────────────────────────────────────
let _serverSyncTimer = null

/** 서버로 현재 설정 전체를 저장 (debounced, 5s). 비로그인 시 skip. */
function scheduleServerSync() {
  if (!authStore.isAuthenticated) return
  if (_serverSyncTimer) clearTimeout(_serverSyncTimer)
  _serverSyncTimer = setTimeout(() => _doServerSync(), 1500)
}

async function _doServerSync() {
  if (!authStore.isAuthenticated) return
  try {
    await userApi.savePreferences({
      categories: categories.value,
      account_category_map: accountCategoryMap.value,
      show_shared: showShared.value,
      hidden_account_ids: [...hiddenAccountIds.value],
    })
  } catch (e) {
    // 서버 동기화 실패는 조용히 무시 (로컬 저장은 이미 완료)
    console.warn('[Dashboard] server prefs sync failed', e)
  }
}

/** 로그인 후 서버에서 설정 로드 → 로컬 refs 및 localStorage 갱신 */
async function loadPrefsFromServer() {
  if (!authStore.isAuthenticated) return
  try {
    const { data } = await userApi.getPreferences()
    const prefs = data?.preferences
    if (!prefs || Object.keys(prefs).length === 0) return

    if (Array.isArray(prefs.categories)) {
      categories.value = prefs.categories
      try { localStorage.setItem(scopedDashboardKey(CATEGORIES_KEY), JSON.stringify(prefs.categories)) } catch { /* ignore */ }
    }
    if (prefs.account_category_map && typeof prefs.account_category_map === 'object') {
      accountCategoryMap.value = prefs.account_category_map
      try { localStorage.setItem(scopedDashboardKey(ACCOUNT_CAT_MAP_KEY), JSON.stringify(prefs.account_category_map)) } catch { /* ignore */ }
    }
    if (typeof prefs.show_shared === 'boolean') {
      showShared.value = prefs.show_shared
      try { localStorage.setItem(scopedDashboardKey(SHOW_SHARED_KEY), JSON.stringify(prefs.show_shared)) } catch { /* ignore */ }
    }
    if (Array.isArray(prefs.hidden_account_ids)) {
      hiddenAccountIds.value = new Set(prefs.hidden_account_ids)
      try {
        localStorage.setItem(scopedDashboardKey(HIDDEN_ACCOUNTS_KEY), JSON.stringify(prefs.hidden_account_ids))
      } catch { /* ignore */ }
    }
  } catch (e) {
    // 서버 로드 실패 시 localStorage 값 유지
    console.warn('[Dashboard] failed to load server prefs, using localStorage', e)
  }
}

watch(
  () => [authStore.isAuthenticated, authStore.user?.id],
  async ([isAuth]) => {
    loadDashboardPrefsForUser()
    if (isAuth) {
      // 서버 설정을 로드하여 localStorage 위에 덮어씌움 (다른 기기 설정 복구)
      await loadPrefsFromServer()
    }
  },
  { immediate: true }
)

const groupModalRef = ref(null)
let groupBootstrapModal = null
const newCatName = ref('')

function openGroupModal() {
  if (!groupBootstrapModal && groupModalRef.value) {
    groupBootstrapModal = new Modal(groupModalRef.value)
  }
  groupBootstrapModal?.show()
}

function addCategory() {
  const name = newCatName.value.trim()
  if (!name) return
  const id = 'cat-' + Date.now()
  categories.value.push({
    id,
    name,
    order: categories.value.length
  })
  newCatName.value = ''
  persistCategories()
}

function removeCategory(id) {
  if (!confirm('이 분류를 삭제하시겠습니까? (배정된 계좌는 미분류로 이동합니다)')) return
  categories.value = categories.value.filter(c => c.id !== id)
  // Clean up mapping
  const newMap = { ...accountCategoryMap.value }
  Object.keys(newMap).forEach(accId => {
    if (newMap[accId] === id) delete newMap[accId]
  })
  accountCategoryMap.value = newMap
  persistCategories()
  persistMapping()
}

function moveCategory(index, delta) {
  const targetIndex = index + delta
  if (targetIndex < 0 || targetIndex >= categories.value.length) return
  
  const cats = [...categories.value]
  const temp = cats[index]
  cats[index] = cats[targetIndex]
  cats[targetIndex] = temp
  
  // Update orders
  cats.forEach((c, i) => { c.order = i })
  categories.value = cats
  persistCategories()
}

/** 분류에 색상이 지정되지 않았을 때 보여줄 기본 색(카드/차트와 동일한 순환 팔레트) */
function defaultCategoryHex(idx) {
  return CHART_LINE_HEX[idx % CHART_LINE_HEX.length]
}

function setCategoryColor(cat, hex) {
  categories.value = categories.value.map((c) => (c.id === cat.id ? { ...c, color: hex } : c))
  persistCategories()
}

function assignCategory(accountId, categoryId) {
  if (categoryId === 'default') {
    const newMap = { ...accountCategoryMap.value }
    delete newMap[accountId]
    accountCategoryMap.value = newMap
  } else {
    accountCategoryMap.value = {
      ...accountCategoryMap.value,
      [accountId]: categoryId
    }
  }
  persistMapping()
}

function persistCategories() {
  try {
    localStorage.setItem(scopedDashboardKey(CATEGORIES_KEY), JSON.stringify(categories.value))
  } catch {
    /* ignore */
  }
  scheduleServerSync()
}

function persistMapping() {
  try {
    localStorage.setItem(scopedDashboardKey(ACCOUNT_CAT_MAP_KEY), JSON.stringify(accountCategoryMap.value))
  } catch {
    /* ignore */
  }
  scheduleServerSync()
}

function persistVisibility() {
  try {
    localStorage.setItem(scopedDashboardKey(SHOW_SHARED_KEY), JSON.stringify(showShared.value))
  } catch {
    /* ignore */
  }
  scheduleServerSync()
}

const settingsAccountList = computed(() => {
  let list = overview.value
  if (authStore.isAuthenticated && !showShared.value) {
    list = list.filter((acc) => String(acc.account.user_id) === String(authStore.user?.id))
  }
  return list
})

const filteredOverview = computed(() => {
  let list = overview.value
  if (authStore.isAuthenticated) {
    if (!showShared.value) {
      list = list.filter((acc) => String(acc.account.user_id) === String(authStore.user?.id))
    }
    list = list.filter((acc) => !hiddenAccountIds.value.has(acc.account.id))
  }
  return list
})

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
  return { changeSum, principalSum, pct }
}

/** 노출 중인 계좌 전체 합계 (KPI 카드용) */
const portfolioTotals = computed(() => {
  const items = filteredOverview.value
  const principal = items.reduce((s, a) => s + Number(a.principal || 0), 0)
  const investment_return = items.reduce((s, a) => s + Number(a.investment_return || 0), 0)
  const total_asset_value = items.reduce((s, a) => s + Number(a.total_asset_value || 0), 0)
  const pd = aggregatePrevDay(items)
  return {
    principal,
    investment_return,
    total_asset_value,
    roi: principal > 0 ? (investment_return / principal) * 100 : 0,
    prev_day_change_sum: pd.changeSum,
    prev_day_return_vs_principal_pct: pd.pct,
    count: items.length,
  }
})

const showMarketOverviewStrip = computed(
  () => marketIndices.value.length > 0 || portfolioTotals.value.count > 0,
)

const groupedOverview = computed(() => {
  if (!authStore.isAuthenticated) {
    const items = filteredOverview.value
    const principal = items.reduce((s, a) => s + (a.principal || 0), 0)
    const investment_return = items.reduce((s, a) => s + (a.investment_return || 0), 0)
    const total_asset_value = items.reduce((s, a) => s + (a.total_asset_value || 0), 0)
    const pd = aggregatePrevDay(items)
    return [{
      category: { id: 'default', name: '전체 계좌' },
      items,
      principal,
      investment_return,
      total_asset_value,
      roi: principal > 0 ? (investment_return / principal) * 100 : 0,
      prev_day_change_sum: pd.changeSum,
      prev_day_return_vs_principal_pct: pd.pct,
    }]
  }

  const groups = []
  const cats = [...categories.value].sort((a, b) => a.order - b.order)
  
  // Create group objects
  const groupMap = {}
  cats.forEach(c => {
    groupMap[c.id] = { category: c, items: [], principal: 0, investment_return: 0, total_asset_value: 0 }
    groups.push(groupMap[c.id])
  })
  
  // Uncategorized group
  const uncategorized = { category: { id: 'default', name: '미분류', order: 999 }, items: [], principal: 0, investment_return: 0, total_asset_value: 0 }
  
  filteredOverview.value.forEach(acc => {
    const catId = accountCategoryMap.value[acc.account.id]
    const g = groupMap[catId] || uncategorized
    g.items.push(acc)
    g.principal += (acc.principal || 0)
    g.investment_return += (acc.investment_return || 0)
    g.total_asset_value += (acc.total_asset_value || 0)
  })
  
  if (uncategorized.items.length > 0) {
    groups.push(uncategorized)
  }
  
  return groups.map((g) => {
    const pd = aggregatePrevDay(g.items)
    return {
      ...g,
      roi: g.principal > 0 ? (g.investment_return / g.principal) * 100 : 0,
      prev_day_change_sum: pd.changeSum,
      prev_day_return_vs_principal_pct: pd.pct,
    }
  })
})

const dashboardVisibleGroups = computed(() =>
  groupedOverview.value.filter((g) => (g.items?.length || 0) > 0),
)

function groupCategoryKey(group) {
  return String(group?.category?.id ?? 'default')
}

function isDashboardGroupExpanded(key) {
  return expandedDashboardGroups.value.has(String(key))
}

function toggleDashboardGroup(key) {
  const k = String(key)
  const next = new Set(expandedDashboardGroups.value)
  if (next.has(k)) next.delete(k)
  else next.add(k)
  expandedDashboardGroups.value = next
}

/** 최근 n개월 라벨 (당월까지, 월초 기준) — 월 키 없이 길이만 맞출 때 보조용 */
function lastNMonthLabels(n) {
  if (n <= 0) return []
  const labels = []
  const d = new Date()
  for (let k = n - 1; k >= 0; k--) {
    const x = new Date(d.getFullYear(), d.getMonth() - k, 1)
    labels.push(`${x.getFullYear()}.${String(x.getMonth() + 1).padStart(2, '0')}`)
  }
  return labels
}

function normalizeMonthKey(raw) {
  if (raw == null) return ''
  const s = String(raw).trim()
  if (/^\d{4}-\d{2}$/.test(s)) return s
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) return s.slice(0, 7)
  return ''
}

function incrementMonthYm(ym) {
  let y = parseInt(ym.slice(0, 4), 10)
  let mo = parseInt(ym.slice(5, 7), 10)
  mo++
  if (mo > 12) {
    mo = 1
    y++
  }
  return `${y}-${String(mo).padStart(2, '0')}`
}

/** 백엔드 `monthly_cutoff_key` ~ `monthly_trend_end_month` 구간 (YYYY-MM, 양끝 포함) */
function buildInclusiveMonthAxis(minStr, endStr) {
  const a = normalizeMonthKey(minStr)
  const b = normalizeMonthKey(endStr)
  if (!a || !b || a > b) return []
  const out = []
  let cur = a
  while (cur <= b) {
    out.push(cur)
    if (cur === b) break
    cur = incrementMonthYm(cur)
  }
  return out
}

/** 계좌별 월→수익금 (동일 월 중복 행은 합산) */
function accountMonthValueMap(acc) {
  const m = new Map()
  const months = Array.isArray(acc.history_months) ? acc.history_months : []
  const pts = Array.isArray(acc.history_points) ? acc.history_points.map((x) => Number(x)) : []
  if (months.length !== pts.length) return m
  for (let i = 0; i < months.length; i++) {
    const mk = normalizeMonthKey(months[i])
    if (!mk) continue
    const v = Number.isFinite(pts[i]) ? pts[i] : 0
    m.set(mk, (m.get(mk) || 0) + v)
  }
  return m
}

function groupTrendMeta(group) {
  const items = group.items || []
  const a = items.find((x) => x.monthly_trend_min_month && x.monthly_trend_end_month)
  if (a) {
    return { min: a.monthly_trend_min_month, end: a.monthly_trend_end_month }
  }
  return { min: '', end: '' }
}

/**
 * 분류 내 계좌 월별 수익금 합산.
 * - 서버가 내린 월 축(`monthly_trend_min_month` ~ `monthly_trend_end_month`)에서 최근 12개월만 사용.
 * - 각 월마다 모든 계좌를 더하며, 해당 월 데이터가 없는 계좌는 0으로 간주.
 */
function groupYearProfitSeries(group) {
  const accounts = group.items || []
  if (accounts.length === 0) {
    return { labels: [], data: [] }
  }

  const { min: minM, end: endM } = groupTrendMeta(group)
  let axis = []
  if (minM && endM) {
    axis = buildInclusiveMonthAxis(minM, endM)
    if (axis.length > 12) {
      axis = axis.slice(-12)
    }
  }

  if (axis.length > 0) {
    const perAcc = accounts.map((acc) => accountMonthValueMap(acc))
    const data = axis.map((monthKey) =>
      perAcc.reduce((sum, map) => sum + (map.get(monthKey) ?? 0), 0),
    )
    const labels = axis.map((m) => `${m.slice(0, 4)}.${m.slice(5, 7)}`)
    return { labels, data }
  }

  const byMonth = new Map()
  for (const acc of accounts) {
    const map = accountMonthValueMap(acc)
    for (const [k, v] of map) {
      byMonth.set(k, (byMonth.get(k) || 0) + v)
    }
  }
  if (byMonth.size > 0) {
    const sortedMonths = [...byMonth.keys()].sort()
    const take = Math.min(12, sortedMonths.length)
    const slice = sortedMonths.slice(-take)
    const data = slice.map((mk) => byMonth.get(mk) ?? 0)
    const labels = slice.map((m) => `${m.slice(0, 4)}.${m.slice(5, 7)}`)
    return { labels, data }
  }

  if (accounts.length === 1) {
    const acc = accounts[0]
    const pts = Array.isArray(acc.history_points) ? acc.history_points.map((x) => Number(x)) : []
    if (pts.length === 0) {
      const total = Number(acc.investment_return || 0)
      const m = lastNMonthLabels(1)
      return { labels: m.length ? m : ['—'], data: [total] }
    }
    const take = Math.min(12, pts.length)
    const data = pts.slice(-take)
    const labels = lastNMonthLabels(data.length)
    return { labels, data }
  }

  const total = accounts.reduce((s, a) => s + Number(a.investment_return || 0), 0)
  const m = lastNMonthLabels(1)
  return { labels: m.length ? m : ['—'], data: [total] }
}

function groupLineChartConfig(group, gIdx) {
  const { labels, data } = groupYearProfitSeries(group)
  const c = group.category?.color || CHART_LINE_HEX[gIdx % CHART_LINE_HEX.length]
  return {
    labels,
    datasets: [
      {
        label: '수익금',
        data,
        borderColor: c,
        backgroundColor: (ctx) => {
          const chart = ctx.chart
          const { ctx: cnv, chartArea } = chart
          if (!chartArea) return hexToRgba(c, 0.12)
          const g = cnv.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
          g.addColorStop(0, hexToRgba(c, 0.42))
          g.addColorStop(0.5, hexToRgba(c, 0.1))
          g.addColorStop(1, hexToRgba(c, 0))
          return g
        },
        fill: true,
        tension: 0.28,
        pointRadius: 0,
        pointHoverRadius: 0,
        pointHitRadius: 12,
        borderWidth: 2,
      },
    ],
  }
}

function groupHoldingsBreakdown(group) {
  const map = new Map()
  let cashSum = 0
  for (const acc of group.items || []) {
    cashSum += Math.max(0, Number(acc.cash_balance || 0))
    const holdings = Array.isArray(acc.holdings) ? acc.holdings : []
    for (const h of holdings) {
      if (!h || h.ticker === 'CASH') continue
      const raw = h.asset_class
      const key = raw != null && String(raw).trim() !== '' ? String(raw).trim() : '미분류'
      const v = Number(h.value || 0)
      if (!Number.isFinite(v) || v <= 0) continue
      map.set(key, (map.get(key) || 0) + v)
    }
  }
  if (cashSum > 0) {
    map.set('현금', (map.get('현금') || 0) + cashSum)
  }
  const entries = [...map.entries()].sort((a, b) => b[1] - a[1])
  if (entries.length === 0) return { labels: [], data: [] }
  const top = 7
  const head = entries.slice(0, top)
  const rest = entries.slice(top).reduce((s, [, v]) => s + v, 0)
  const labels = head.map(([k]) => k)
  const data = head.map(([, v]) => v)
  if (rest > 0) {
    labels.push('기타')
    data.push(rest)
  }
  return { labels, data }
}

/** 막대그래프는 위→아래로 큰 값부터 보이도록 배열을 뒤집어서 그린다(Chart.js 수평 막대 기본은 아래→위) */
function groupBarChartConfig(group, gIdx) {
  const { labels, data } = groupHoldingsBreakdown(group)
  const bg = labels.map((_, i) => CHART_COLORS[(i + gIdx) % CHART_COLORS.length])
  return {
    labels: [...labels].reverse(),
    datasets: [
      {
        data: [...data].reverse(),
        backgroundColor: [...bg].reverse(),
        borderRadius: 0,
        barPercentage: 0.72,
      },
    ],
  }
}

/** 분류 항목 수에 맞춰 막대그래프 높이를 조절(항목이 많을수록 세로로 길어짐) */
function groupBarChartHeight(group) {
  const count = groupHoldingsBreakdown(group).data.length
  return Math.max(160, Math.min(320, 44 + count * 34))
}

const dashboardGroupLineOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx) => `₩${Number(ctx.raw || 0).toLocaleString()}`,
      },
    },
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: {
        maxRotation: 0,
        autoSkip: true,
        maxTicksLimit: 5,
        font: { size: 10 },
      },
    },
    y: {
      grid: { color: 'rgba(148,163,184,0.22)' },
      ticks: {
        font: { size: 9 },
        maxTicksLimit: 6,
        callback: (v) => formatDashboardLineYAxisWon(Number(v)),
      },
    },
  },
}

/** 자산분류 수평 막대그래프: 막대 끝에 비중(%)만 표기 — 금액까지 같이 넣으면 카드 폭이 애매한 모바일 구간에서 고정 여백을 넘어가 잘려 보였다. 금액은 툴팁에서 확인 가능 */
const dashboardGroupBarOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  layout: {
    padding: { right: 44 },
  },
  plugins: {
    legend: {
      display: false,
    },
    datalabels: {
      color: '#64748b',
      anchor: 'end',
      align: 'end',
      offset: 4,
      clamp: true,
      font: {
        weight: '600',
        size: 11,
        family: '"Noto Sans KR", sans-serif',
      },
      formatter: (value, ctx) => {
        const v = Number(value)
        if (!Number.isFinite(v) || v <= 0) return null
        const arr = ctx.chart?.data?.datasets?.[0]?.data || []
        const total = arr.reduce((a, b) => a + Number(b || 0), 0) || 1
        const pct = (v / total) * 100
        return `${pct.toFixed(1)}%`
      },
    },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const v = Number(ctx.raw ?? ctx.parsed?.x ?? 0)
          const arr = ctx.dataset?.data || []
          const total = arr.reduce((a, b) => a + Number(b || 0), 0) || 1
          const pct = ((v / total) * 100).toFixed(1)
          return `${ctx.label}: ₩${v.toLocaleString()} (${pct}%)`
        },
      },
    },
  },
  scales: {
    x: {
      display: false,
      grid: { display: false },
    },
    y: {
      grid: { display: false },
      ticks: {
        font: { size: 11, weight: '600' },
        color: '#64748b',
      },
    },
  },
}

let overviewAbortController = null
let lastOverviewRequestId = 0

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

function aggregateOldestPriceFromAccounts(accounts) {
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

function formatOldestPriceLine(raw, minutes) {
  const label = formatPriceUpdatedAtLabel(raw)
  const age = formatAgeMinutes(Number(minutes))
  if (label && age) return `${label} (${age})`
  return ''
}

function formatIndexPriceUpdateLine(idx) {
  const raw = idx?.price_updated_at
  if (!raw) return ''
  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return ''
  const minutes = Math.floor((Date.now() - parsed.getTime()) / 60000)
  return formatOldestPriceLine(raw, minutes)
}

function accountPriceUpdateLine(acc) {
  return formatOldestPriceLine(acc?.oldest_price_updated_at, acc?.oldest_price_age_minutes)
}

function groupPriceUpdateLine(group) {
  const { raw, minutes } = aggregateOldestPriceFromAccounts(group?.items || [])
  return formatOldestPriceLine(raw, minutes)
}

const portfolioPriceUpdateLine = computed(() => {
  const { raw, minutes } = aggregateOldestPriceFromAccounts(filteredOverview.value)
  return formatOldestPriceLine(raw, minutes)
})

function toggleAccountVisibility(id, visible) {
  if (visible) {
    hiddenAccountIds.value.delete(id)
  } else {
    hiddenAccountIds.value.add(id)
  }
  hiddenAccountIds.value = new Set(hiddenAccountIds.value)
  persistHiddenAccounts()
}

function persistHiddenAccounts() {
  try {
    localStorage.setItem(scopedDashboardKey(HIDDEN_ACCOUNTS_KEY), JSON.stringify([...hiddenAccountIds.value]))
  } catch {
    /* ignore */
  }
  scheduleServerSync()
}

async function loadOverview() {
  if (overviewAbortController) {
    overviewAbortController.abort()
  }
  overviewAbortController = new AbortController()
  const requestId = ++lastOverviewRequestId
  try {
    const { data } = await accountApi.getBalancesOverview({ signal: overviewAbortController.signal })
    if (requestId !== lastOverviewRequestId) return
    overview.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    overview.value = []
    emit('flash', getApiErrorMessage(e, '계좌 현황을 불러오지 못했습니다.'), 'alert-danger')
  } finally {
    if (requestId === lastOverviewRequestId) {
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
    await Promise.all([loadOverview(), loadMarketIndices()])
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
        emit('flash', '갱신이 지연되고 있습니다. 잠시 후 다시 불러오기 해 주세요.', 'alert-warning')
      }
    }
  } finally {
    refreshing.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadOverviewUntilFresh(), loadMarketIndices()])
})

onBeforeUnmount(() => {
  if (overviewAbortController) {
    overviewAbortController.abort()
  }
})

const EOK_WON = 100_000_000
const MAN_FORMAT_MIN_WON = 100_000

function formatMoneyKR(val) {
  if (!Number.isFinite(Number(val))) return '₩0'
  const num = Number(val)
  const abs = Math.abs(num)
  const sign = num < 0 ? '-' : ''

  if (abs < MAN_FORMAT_MIN_WON) return '₩' + num.toLocaleString()

  if (abs >= EOK_WON) {
    return sign + (abs / EOK_WON).toFixed(1) + '억'
  }

  const man = Math.floor(abs / 10_000)
  return sign + man.toLocaleString() + '만원'
}

function getCategoryColor(category, index) {
  if (category?.color) return category.color;
  const num = (index % 8) + 1;
  return `var(--dash-cat-${num})`;
}

/** 계좌 상세 정보 밀도: 보유 종목 수(현금 제외) */
function accountHoldingsCount(acc) {
  const holdings = Array.isArray(acc?.holdings) ? acc.holdings : []
  return holdings.filter((h) => h && h.ticker !== 'CASH').length
}

/** 계좌 상세 정보 밀도: 총자산 대비 현금 비중(%) */
function accountCashRatioPct(acc) {
  const total = Number(acc?.total_asset_value || 0)
  if (total <= 0) return 0
  const cash = Number(acc?.cash_balance || 0)
  return Math.max(0, (cash / total) * 100)
}

/** 현금 비중이 높으면(투자되지 않은 자금이 많으면) 경고 플래그로 강조 — 30%는 흔히 쓰는 "현금 과다" 기준 */
function cashRatioFlagClass(pct) {
  const cls = pct >= 30 ? 'dash-acc-row__flag--warn' : 'dash-acc-row__flag--neutral'
  return `dash-acc-row__flag ${cls}`
}

/** 계좌 상세 정보 밀도: 마지막 리밸런싱일로부터 경과일 (BalanceDetail.vue의 daysSinceLastRebalanced와 동일 규칙) */
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

/** 마지막 리밸런싱이 오래됐거나(90일 이상) 기록이 없으면 경고 플래그로 강조 */
function rebalanceFlagClass(acc) {
  const raw = acc?.last_rebalanced_date
  let stale = true
  if (raw) {
    const last = new Date(raw)
    if (!Number.isNaN(last.getTime())) {
      last.setHours(0, 0, 0, 0)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      const diffDays = Math.floor((today - last) / (1000 * 60 * 60 * 24))
      stale = diffDays >= 90
    }
  }
  const cls = stale ? 'dash-acc-row__flag--warn' : 'dash-acc-row__flag--neutral'
  return `dash-acc-row__flag ${cls}`
}

/**
 * 계좌 상세 정보 밀도: 종목별 목표 비중 대비 "상대" 이격도 중 최댓값(%) — 리밸런싱 필요도의 대략적인 신호.
 * 절대 이격도(현재-목표, %p)가 아니라 목표 대비 비율로 계산한다: 목표 10%에서 1%p 벗어난 것과
 * 목표 20%에서 1%p 벗어난 것은 리밸런싱 관점에서 심각도가 다르기 때문 (전자가 목표 대비 2배 더 벗어남).
 * 목표 비중이 0인 종목(포트폴리오에 편입되지 않은 보유분)은 "목표 대비 비율"이 정의되지 않아 제외한다.
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

/** 이격도(목표 대비 상대 %) 값이 클수록(리밸런싱 필요도가 높을수록) 경고 플래그로 강조. 25%는 리밸런싱 밴드로 흔히 쓰는 "5/25 규칙"의 상대 기준을 따름 */
function deviationClass(pct) {
  if (!Number.isFinite(pct)) return ''
  const cls = pct >= 25 ? 'dash-acc-row__flag--warn' : 'dash-acc-row__flag--neutral'
  return `dash-acc-row__flag ${cls}`
}

/** 로그인 사용자 본인 소유가 아닌(=공유받은) 계좌인지 */
function isSharedAccount(acc) {
  return authStore.isAuthenticated && String(acc?.account?.user_id) !== String(authStore.user?.id)
}

const colorPalette = ['#1e40af', '#3b82f6', '#16a34a', '#eab308', '#f97316', '#ef4444', '#a855f7', '#ec4899', '#94a3b8'];

function getPortfolioData(holdings) {
  if (!holdings || holdings.length === 0) return { gradient: 'conic-gradient(#e2e8f0 0% 100%)', items: [] };
  
  const sorted = [...holdings].sort((a, b) => (b.value || 0) - (a.value || 0));
  
  let topItems = sorted.slice(0, 3);
  let othersValue = sorted.slice(3).reduce((sum, item) => sum + (item.value || 0), 0);
  
  const totalValue = topItems.reduce((sum, item) => sum + (item.value || 0), 0) + othersValue;
  if (totalValue <= 0) return { gradient: 'conic-gradient(#e2e8f0 0% 100%)', items: [] };

  const items = [];
  let currentPercentage = 0;
  let gradientStops = [];
  
  topItems.forEach((item, index) => {
    const percentage = ((item.value || 0) / totalValue) * 100;
    const color = colorPalette[index % colorPalette.length];
    
    // Add gap using white space in gradient
    if (currentPercentage > 0) {
      gradientStops.push(`white ${currentPercentage}% ${currentPercentage + 1}%`);
      currentPercentage += 1; // 1% gap
    }
    
    gradientStops.push(`${color} ${currentPercentage}% ${currentPercentage + percentage}%`);
    items.push({ name: item.name || item.ticker, color, percentage });
    currentPercentage += percentage;
  });
  
  if (othersValue > 0) {
    const percentage = (othersValue / totalValue) * 100;
    const color = colorPalette[3];
    if (currentPercentage > 0) {
      gradientStops.push(`white ${currentPercentage}% ${currentPercentage + 1}%`);
      currentPercentage += 1;
    }
    gradientStops.push(`${color} ${currentPercentage}% ${currentPercentage + percentage}%`);
    items.push({ name: '기타 종목', color, percentage });
  }

  // Ensure last color reaches 100% just in case
  const lastStop = gradientStops[gradientStops.length - 1];
  if (lastStop && !lastStop.includes(' 100%')) {
     const cleanColor = lastStop.split(' ')[0];
     gradientStops.push(`${cleanColor} ${currentPercentage}% 100%`);
  }

  return {
    gradient: `conic-gradient(${gradientStops.join(', ')})`,
    items
  };
}
</script>

<style scoped>
.tabular-nums { font-variant-numeric: tabular-nums; }
.letter-spacing-1 { letter-spacing: 0.05rem; }
.letter-spacing-2 { letter-spacing: 0.1rem; }
.cursor-pointer { cursor: pointer; }
.x-small { font-size: 0.7rem; }

/* 분류 편집 목록의 색상 선택 스와치 */
.cat-color-swatch {
  position: relative;
  width: 1.4rem;
  height: 1.4rem;
  border-radius: 4px;
  box-shadow: 0 0 0 1px var(--ui-border-strong);
  flex-shrink: 0;
  cursor: pointer;
  overflow: hidden;
}

.cat-color-swatch input[type="color"] {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  cursor: pointer;
  border: none;
  padding: 0;
}

.dashboard-page {
  width: 100%;
  /* 분류 팔레트(--dash-cat-1..8)는 style.css :root에서 전역으로 정의 — 잔고 목록(BalanceList) 그룹 카드와 공유 */
  --dash-hero-grad: linear-gradient(135deg, #10b981 0%, #0ea5e9 100%);
  /* 회색 캡션/보조 텍스트 가독성 강화: 이 페이지의 .text-muted·보조 라벨을 더 진한 톤으로 */
  --ui-text-muted: var(--ui-text-subtle);
  /* 라이트 모드 본문 검정이 순검정(#0f172a)이라 너무 진하게 느껴져 한 톤 부드러운 슬레이트로 낮춤 */
  --ui-text: #1e293b;
}

:global([data-theme="dark"]) .dashboard-page {
  /* 다크 모드 텍스트는 이미 밝은 톤이라(검정 아님) 손대지 않고 원래 값 유지 */
  --ui-text: #e5edf7;
}

/* ── 플랫 · 매트 테마: 이 페이지의 카드/배지/버튼은 각지고 그림자 없이 ── */
.dashboard-page :deep(.rounded-4),
.dashboard-page :deep(.rounded-3),
.dashboard-page :deep(.rounded-circle),
.dashboard-page :deep(.rounded-pill) {
  border-radius: 2px !important;
}
.dashboard-page :deep(.shadow-sm) {
  box-shadow: none !important;
}

.dashboard-title {
  color: var(--ui-text);
}

.dashboard-strong-text {
  color: var(--ui-text);
}

/* 시세 카드: 국내증시 · 해외증시 · 환율을 각각 독립된 행으로 — 항목이 늘어도(확장성) 해당 행만 늘어남 */
.dashboard-index-row {
  margin-bottom: 0.65rem;
}

.dashboard-index-row:last-child {
  margin-bottom: 0;
}

.dashboard-index-row-label {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--ui-text-muted);
  margin-bottom: 0.4rem;
  padding: 0 0.1rem;
}

.dashboard-index-row-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.65rem;
}

@media (min-width: 640px) {
  .dashboard-index-row-grid {
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  }
}

@media (min-width: 1200px) {
  .dashboard-index-row-grid {
    gap: 0.85rem;
  }
}

/* 항목이 적어 카드가 넓어질 때 정보가 비어 보이지 않도록: 가격/변동을 한 줄로 펼쳐 폭을 활용 */
.dashboard-index-card-main {
  flex-wrap: nowrap;
  align-items: flex-end;
}

.dashboard-index-delta {
  flex-direction: column;
  align-items: flex-end;
}

/* 나스닥처럼 자릿수가 긴 지수는 좁은 화면에서 가격+등락이 한 줄에 눌려 등락 정보가 다음 줄로 밀리고 오른쪽이 비어 보인다 — 세로로 쌓아 카드 폭을 그대로 쓴다. md(768px) 미만은 모두 모바일 레이아웃으로 취급 */
@media (max-width: 767.98px) {
  .dashboard-index-card-main {
    flex-direction: column;
    align-items: stretch;
    gap: 0.3rem;
  }

  .dashboard-index-delta {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }
}

.dashboard-index-card-footer {
  font-size: 0.8rem;
  min-height: 1.1rem;
}

.dashboard-index-prevclose {
  align-items: center;
  gap: 0.25rem;
  white-space: nowrap;
}

.dashboard-index-price {
  font-size: clamp(1.15rem, 1rem + 1vw, 1.6rem);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
  font-family: var(--ui-num-font);
}

.dashboard-index-meta {
  font-size: 0.72rem;
  color: var(--ui-text-muted);
}

.dashboard-index-state-badge {
  font-size: 0.66rem;
  letter-spacing: 0.02em;
}

.dashboard-index-source {
  font-size: 0.68rem;
  line-height: 1.2;
}

.dashboard-index-update-line {
  font-size: 0.8rem;
  font-weight: 500;
  line-height: 1.35;
  display: block;
}

.dashboard-group-update-line {
  font-size: 0.65rem;
  max-width: 14rem;
  line-height: 1.35;
}

.tiny-label {
  font-size: 0.68rem;
  letter-spacing: 0.02em;
  line-height: 1.2;
}

/* ── 그룹 카드 ── */
.dashboard-group-big-card {
  position: relative;
  background: var(--ui-surface);
  transition: box-shadow 0.18s ease;
}

/* 배경 전체를 테마색으로 칠하면 옅은 색이 얼룩처럼 보여 어색했다 — 대신 상단에 얇은 그라데이션 바로만 테마를 표시 */
.dashboard-group-big-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--category-color) 0%, color-mix(in srgb, var(--category-color) 40%, transparent) 55%, transparent 100%);
}

.dashboard-group-big-card__header {
  /* 클릭 영역 아님: 더보기 버튼으로 대체 */
}

/* 아이콘 타일 대신 제목 타이포그래피 자체를 굵고 크게 키워 분류를 강조 */
.dashboard-group-big-card__title {
  font-size: 1.55rem;
  font-weight: 800;
  /* 한글은 자간을 좁히면 오히려 읽기 어려워지므로(라틴 타이포 관례와 반대) 자간 조정을 두지 않음 */
  line-height: 1.3;
}

.dashboard-group-big-card__sub {
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

/* KPI 행 그리드: 모바일 2열, md 이상 4열 */
.dashboard-group-kpi-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem 1rem;
}

@media (min-width: 576px) {
  .dashboard-group-kpi-row {
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem 1.25rem;
  }
}

.dashboard-group-kpi-item {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  /* 그리드 아이템 기본 min-width:auto는 내용(줄바꿈 없는 금액+퍼센트)만큼 트랙을 밀어내 카드 밖으로 넘치게 한다 — 0으로 낮춰 폭에 맞게 줄바꿈되도록 함 */
  min-width: 0;
}

.dashboard-group-kpi-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ui-text);
  letter-spacing: 0.03em;
  text-transform: uppercase;
  line-height: 1.3;
}

.dashboard-group-kpi-value {
  font-size: 1.14rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.3;
  /* nowrap이면 좁은 컬럼(태블릿 4열 그리드 등)에서 금액+퍼센트 배지가 카드 밖으로 넘친다 — 폭이 부족할 때만 배지가 자연스럽게 다음 줄로 내려가도록 허용 */
  white-space: normal;
  font-variant-numeric: tabular-nums;
  font-family: var(--ui-num-font);
}

/* 퍼센트 수치: 작은 깃발(플래그) 배지 — 금액과 시각적으로 분리 */
.dashboard-kpi-pct {
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

/* PC 화면: 통계정보(KPI) 가독성 강화 — 글자를 키우고 여백을 넉넉히 */
@media (min-width: 1200px) {
  .dashboard-group-kpi-row {
    gap: 0.6rem 2rem;
  }

  .dashboard-group-kpi-label {
    font-size: 0.86rem;
  }

  .dashboard-group-kpi-value {
    font-size: 1.34rem;
  }

  .dashboard-kpi-pct {
    font-size: 0.98rem;
  }
}

/* ── 더보기 버튼 ── */
.dashboard-group-expand-bar {
  display: flex;
  justify-content: center;
}

.dashboard-group-expand-btn {
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

.dashboard-group-expand-btn:hover {
  background: color-mix(in srgb, var(--category-color) 12%, var(--ui-border));
  border-color: var(--category-color);
  color: var(--category-color);
}

:global([data-theme="dark"]) .dashboard-group-expand-btn {
  background: var(--ui-surface-soft);
  border-color: var(--ui-border-strong);
  color: var(--ui-text-muted);
}

:global([data-theme="dark"]) .dashboard-group-expand-btn:hover {
  background: color-mix(in srgb, var(--category-color) 16%, var(--ui-border));
  border-color: var(--category-color);
  color: var(--category-color);
}

.dashboard-group-expand-btn__text {
  line-height: 1;
}

.dashboard-group-expand-btn__icon {
  color: inherit;
  opacity: 0.75;
}

/* ── 아코디언 슬라이드 전환 ── */
:global(.dash-acc-slide-enter-active),
:global(.dash-acc-slide-leave-active) {
  transition: opacity 0.18s ease;
}
:global(.dash-acc-slide-enter-from),
:global(.dash-acc-slide-leave-to) {
  opacity: 0;
}

/* ── 계좌 리스트 행 ── */
.dashboard-acc-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.dash-acc-row {
  display: flex;
  flex-direction: column;
  padding: 0.65rem 0.9rem;
  border-radius: 2px;
  background: var(--ui-surface);
  border: 1px solid var(--ui-border);
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.dash-acc-row:hover {
  background: var(--ui-surface-soft);
}

.dash-acc-row__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  min-height: 40px;
}

/*
 * 상세 지표 밴드(투자원금 · 보유종목 · 현금비중 · 마지막 리밸런싱 · 최대 이격도 · 계좌번호)는
 * 더 이상 PC 전용이 아니라 모바일에서도 그대로 보여준다. 폭이 좁을 땐 한 줄에 한 항목씩
 * 세로로 나열(라벨 좌/값 우)해 카드가 길어지더라도 정보 손실 없이 다 보이게 하고,
 * 1200px 이상에서만 기존 6열 그리드로 압축한다.
 */
.dash-acc-row__secondary {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.6rem;
  padding-top: 0.6rem;
  border-top: 1px dashed var(--ui-border);
}

.dash-acc-row__secondary-item {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  min-width: 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px dashed var(--ui-border);
}

.dash-acc-row__secondary-item:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.dash-acc-row__secondary-label {
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  line-height: 1.3;
  color: var(--ui-text-muted);
  flex-shrink: 0;
}

.dash-acc-row__secondary-value {
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

.dash-acc-row__secondary-value--muted {
  font-weight: 500;
  color: var(--ui-text-muted);
}

/* 투자원금·보유종목처럼 검정 텍스트 일변도를 피할 값 — 해당 계좌가 속한 분류색을 옅게 섞어 은은하게 구분 */
.dash-acc-row__secondary-value--accent {
  color: color-mix(in srgb, var(--category-color) 55%, var(--ui-text-subtle));
}

/* 현금비중 · 마지막 리밸런싱 · 최대 이격도 — 상태를 한눈에 보여주는 작은 플래그 배지 */
.dash-acc-row__flag {
  display: inline-flex;
  align-items: center;
  padding: 0.06rem 0.5rem;
  border-radius: 999px;
  font-weight: 700;
}

.dash-acc-row__flag--neutral {
  background: var(--ui-surface-soft);
  color: var(--ui-text-subtle);
}

.dash-acc-row__flag--warn {
  background: color-mix(in srgb, var(--ui-alert-warning-text) 16%, transparent);
  color: var(--ui-alert-warning-text);
}

.dash-acc-row__owner-tag {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ui-text-subtle);
  background: var(--ui-surface-soft);
  border: 1px solid var(--ui-border);
  padding: 0 0.4rem;
  line-height: 1.5;
}

.dash-acc-row__name {
  flex: 1;
  min-width: 0;
}

.dash-acc-row__title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--ui-text);
  line-height: 1.3;
}

.dash-acc-row__meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.3rem 0.5rem;
  margin-top: 0.12rem;
}

.dash-acc-row__tag {
  font-size: 0.85rem;
  font-weight: 700;
  line-height: 1.3;
}

.dash-acc-row__time {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--ui-text-muted);
  display: inline-flex;
  align-items: center;
  gap: 0.18rem;
  line-height: 1.3;
}

.dash-acc-row__metrics {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  flex-shrink: 0;
}

.dash-acc-row__metric {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.08rem;
}

/* 항목 간 구분선: 총자산 · 수익률 · 전일대비가 서로 붙어 보이지 않도록 */
.dash-acc-row__metric:not(:first-child) {
  padding-left: 0.85rem;
  border-left: 1px solid var(--ui-border);
}

.dash-acc-row__metric-label {
  font-size: 0.8rem;
  color: var(--ui-text);
  font-weight: 700;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  white-space: nowrap;
  line-height: 1.3;
}

.dash-acc-row__metric-value {
  font-size: 0.98rem;
  font-weight: 600;
  line-height: 1.25;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  font-family: var(--ui-num-font);
  color: var(--ui-text);
}

/* 총 자산 — 행에서 가장 중요한 숫자라 검정 텍스트 대신 그 계좌가 속한 분류색으로 강조 */
.dash-acc-row__metric-value--accent {
  color: var(--category-color);
}

.dash-acc-row__metric-value--pct {
  display: inline-flex;
  align-items: center;
  font-size: 1rem;
  font-weight: 700;
  padding: 0.1rem 0.55rem 0.1rem 0.7rem;
  clip-path: polygon(9px 0, 100% 0, 100% 100%, 9px 100%, 0 50%);
}

.dash-acc-row__metric-pct {
  display: inline-flex;
  align-items: center;
  font-size: 0.83rem;
  font-weight: 700;
  margin-left: 0.4rem;
  padding: 0.06rem 0.45rem 0.06rem 0.6rem;
  vertical-align: middle;
  clip-path: polygon(7px 0, 100% 0, 100% 100%, 7px 100%, 0 50%);
}

/* PC 화면: 계좌 상세정보 가독성 강화 — 여백을 넓히고 글자를 키운다 */
@media (min-width: 1200px) {
  .dash-acc-row {
    padding: 0.85rem 1.15rem;
  }

  .dash-acc-row__title {
    font-size: 1.08rem;
  }

  .dash-acc-row__tag,
  .dash-acc-row__time,
  .dash-acc-row__owner-tag {
    font-size: 0.9rem;
  }

  .dash-acc-row__metrics {
    gap: 1.6rem;
  }

  .dash-acc-row__metric:not(:first-child) {
    padding-left: 1.6rem;
  }

  .dash-acc-row__metric-label {
    font-size: 0.86rem;
  }

  .dash-acc-row__metric-value {
    font-size: 1.1rem;
  }

  .dash-acc-row__metric-value--pct {
    font-size: 1.2rem;
  }

  .dash-acc-row__metric-pct {
    font-size: 0.92rem;
  }

  /* 1200px 이상에서만 세로 나열 대신 6열 그리드로 압축 */
  .dash-acc-row__secondary {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 0.5rem 1.5rem;
    margin-top: 0.7rem;
    padding-top: 0.65rem;
  }

  .dash-acc-row__secondary-item {
    flex-direction: column;
    align-items: flex-start;
    justify-content: flex-start;
    gap: 0.1rem;
    padding-bottom: 0;
    border-bottom: none;
  }

  .dash-acc-row__secondary-item:not(:first-child) {
    padding-left: 1.6rem;
    border-left: 1px solid var(--ui-border);
  }

  .dash-acc-row__secondary-label {
    font-size: 0.88rem;
  }

  .dash-acc-row__secondary-value {
    font-size: 1.02rem;
    text-align: left;
  }
}

/* 모바일: 계좌명이 지표 열과 나란히 있으면 폭이 눌려 이름은 왼쪽에서 빈 듯 짜부라지고 지표만 오른쪽에 몰린다 — 계좌명을 윗줄로, 지표를 아랫줄로 분리. md(768px) 미만은 모두 모바일 레이아웃으로 취급 */
@media (max-width: 767.98px) {
  .dash-acc-row__top {
    flex-direction: column;
    align-items: stretch;
    min-height: 0;
    gap: 0.5rem;
  }

  .dash-acc-row__name {
    flex: none;
  }

  /* 지표 칸이 내용 폭만큼만 좌우 끝에 걸쳐 가운데가 비어 보이던 것을 — 각 지표가 폭을 균등하게 나눠 갖도록 변경 */
  .dash-acc-row__metrics {
    width: 100%;
    justify-content: flex-start;
  }

  .dash-acc-row__metric {
    flex: 1 1 0;
    align-items: flex-start;
    min-width: 0;
  }
}

.dashboard-group-charts {
  background: color-mix(in srgb, var(--ui-surface-soft) 60%, transparent);
}

:global([data-theme="dark"]) .dashboard-group-charts {
  background: rgba(255, 255, 255, 0.02);
}

.dashboard-chart-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--ui-text-muted);
  letter-spacing: 0.02em;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

/* 차트 영역도 카드 테마색과 이어지도록 라벨 앞에 작은 색 표식을 둔다 */
.dashboard-chart-label::before {
  content: '';
  width: 0.5rem;
  height: 0.5rem;
  flex-shrink: 0;
  border-radius: 1px;
  background: var(--category-color);
}

.dashboard-group-chart-wrap {
  position: relative;
  height: clamp(190px, 20vw, 240px);
  min-height: 170px;
  padding: 0.5rem 0.25rem; /* 차트 내부 마진 */
}

.dashboard-group-chart-wrap--bar {
  max-width: 100%;
  padding: 0.5rem 0.5rem 0.25rem;
}

/* ── 포트폴리오 ROI 히어로: 전체 폭 한 행 — 이 페이지에서 가장 먼저 봐야 할 숫자, 화사한 그라디언트로 강조 ── */
.dash-portfolio-hero {
  background: var(--dash-hero-grad) !important;
  border: none !important;
}

.dash-portfolio-hero-label,
.dash-portfolio-hero-number {
  color: #fff;
}

.dash-portfolio-hero-label {
  font-size: 0.95rem;
  opacity: 0.95;
}

.dash-portfolio-hero__headline {
  flex-shrink: 0;
}

.dash-portfolio-hero__headline .dashboard-index-price {
  font-size: clamp(2.6rem, 2rem + 4vw, 3.6rem);
}

/* 계좌 수 · 투자 원금 · 총 평가자산 3개뿐이라 항상 3열 균등 배치 — 큰 화면에서도 폭이 지나치게 벌어지지 않도록 max-width로 제한 */
.dash-portfolio-hero__stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.9rem 1.5rem;
  width: 100%;
}

@media (min-width: 1200px) {
  .dash-portfolio-hero__stats {
    max-width: 34rem;
  }
}

.dash-portfolio-hero__stat {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  min-width: 0;
}

.dash-portfolio-hero__stat-label {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #fff;
  opacity: 0.85;
}

/* 숫자 자체가 핵심 정보라 라벨보다 훨씬 크게 — 카드에 남던 여백을 타이포 크기로 채운다 */
.dash-portfolio-hero__stat-value {
  font-size: clamp(1.55rem, 1.25rem + 1.6vw, 1.95rem);
  font-weight: 800;
  line-height: 1.15;
  font-family: var(--ui-num-font);
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 시세 갱신 시각은 통계가 아니라 메타 정보 — 큰 숫자들과 같은 위계로 두지 않고 카드 하단에 작게 분리 */
.dash-portfolio-hero__meta {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.75rem;
  padding-top: 0.6rem;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  font-size: 0.78rem;
  font-weight: 500;
  color: #fff;
  opacity: 0.75;
}

@media (min-width: 1920px) {
  .dashboard-market-overview {
    max-width: 1880px;
    margin-left: auto;
    margin-right: auto;
  }

  .dashboard-main-content {
    max-width: 1880px;
    margin-left: auto;
    margin-right: auto;
  }
}

.dashboard-empty-accounts {
  max-width: 28rem;
}

.dashboard-acc-title {
  max-width: 100%;
}

@media (min-width: 576px) {
  .dashboard-acc-card-grid .dashboard-acc-title {
    max-width: min(100%, 22rem);
  }
}

.dashboard-acc-chart {
  height: clamp(118px, 12vw + 72px, 172px);
  min-height: 112px;
}

.dashboard-acc-metric-card {
  min-width: 0;
}

.dashboard-acc-metric-label-text {
  font-size: 0.8rem;
  font-weight: 500;
  color: #475569;
  letter-spacing: -0.01em;
  line-height: 1.2;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-acc-metric-number {
  font-size: 1.05rem;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dashboard-acc-metric-number--pct {
  font-size: 1.15rem;
}

@media (min-width: 1200px) {
  .dashboard-acc-metric-number {
    font-size: 1.1rem;
  }

  .dashboard-acc-metric-number--pct {
    font-size: 1.25rem;
  }
}

.dashboard-status-bar {
  padding: 0.48rem 0.6rem;
  border-radius: 12px;
  border: 1px solid var(--ui-border);
  background: var(--ui-surface-soft);
}

.dashboard-status-text {
  font-size: 0.85rem;
  font-weight: 500;
}

/* 카드 뷰 (KPI / 계좌 카드) */
.dash-kpi-card {
  background: var(--ui-surface);
  border-color: var(--ui-border) !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
.dash-kpi-card::after {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 3px;
  background: linear-gradient(90deg, var(--ui-primary), transparent);
  opacity: 0.35;
  pointer-events: none;
}
.dash-kpi-label {
  letter-spacing: 0.02em;
}

.dash-selection-chip {
  background: var(--ui-primary-soft);
  color: var(--ui-text);
}

.dash-group-heading {
  border-bottom: 1px solid var(--ui-border);
  padding-bottom: 0.35rem;
}
.dash-group-dot {
  width: 8px;
  height: 8px;
  background: var(--ui-primary);
  opacity: 0.85;
}
.dash-group-badge {
  background: var(--ui-surface-soft);
  color: var(--ui-text-muted);
  border: 1px solid var(--ui-border);
  font-weight: 600;
  font-size: 0.7rem;
}

.dash-acc-card {
  background: var(--ui-surface);
  transition: box-shadow 0.15s ease, transform 0.12s ease;
}
.dash-acc-card:hover {
  box-shadow: 0 0.5rem 1.25rem rgba(0, 0, 0, 0.08) !important;
}
.dash-acc-card--selected {
  outline: 2px solid var(--ui-primary);
  outline-offset: 2px;
  box-shadow: 0 0.35rem 1rem color-mix(in srgb, var(--ui-primary) 22%, transparent) !important;
}
.dash-shared-badge {
  font-size: 0.65rem;
  font-weight: 600;
  background: var(--ui-surface-soft);
  color: var(--ui-text-muted);
  border: 1px solid var(--ui-border);
}

.dash-acc-metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.65rem 1rem;
}
.dash-acc-metric {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}
.dash-acc-metric-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--ui-text-muted);
}
.dash-acc-metric-value {
  font-size: 0.95rem;
  line-height: 1.25;
  word-break: break-all;
}
.dash-acc-metric-sub {
  line-height: 1.2;
}

.dash-group-subtotal {
  background: var(--ui-surface-soft);
  border: 1px solid var(--ui-border) !important;
}

:global([data-theme="dark"]) .dash-group-subtotal {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.05) !important;
}

.drop-shadow-sm { filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.05)); }


.dashboard-refresh-toast {
  background: var(--ui-surface);
  border-color: var(--ui-border);
}

/* Financial Colors (Simple & Professional) */
.text-profit { color: var(--ui-up) !important; font-weight: 600; }
.text-loss { color: var(--ui-down) !important; font-weight: 600; }

/* Elegant Pastel Tints for Numbers */
.bg-pastel-profit { background-color: #fef2f2; color: #dc2626; border: 1px solid #fee2e2; }
.bg-pastel-loss { background-color: #eff6ff; color: #2563eb; border: 1px solid #dbeafe; }
:global([data-theme="dark"]) .bg-pastel-profit { background-color: rgba(251, 113, 133, 0.1); color: #fb7185; border-color: rgba(251, 113, 133, 0.2); }
:global([data-theme="dark"]) .bg-pastel-loss { background-color: rgba(96, 165, 250, 0.1); color: #60a5fa; border-color: rgba(96, 165, 250, 0.2); }

.bg-pastel-profit-soft { background-color: #fffafb; color: #b91c1c; border: 1px solid #fff1f2; }
.bg-pastel-loss-soft { background-color: #f8fbff; color: #1e40af; border: 1px solid #eff6ff; }
.border-subtle-red { border: 1px solid #fee2e2; }
.border-subtle-blue { border: 1px solid #dbeafe; }
:global([data-theme="dark"]) .border-subtle-red { border-color: rgba(251, 113, 133, 0.2); }
:global([data-theme="dark"]) .border-subtle-blue { border-color: rgba(96, 165, 250, 0.2); }

:global([data-theme="dark"]) .bg-pastel-profit-soft { background-color: rgba(251, 113, 133, 0.05); color: #fb7185; border-color: transparent; }
:global([data-theme="dark"]) .bg-pastel-loss-soft { background-color: rgba(96, 165, 250, 0.05); color: #60a5fa; border-color: transparent; }

.bg-pastel-gray { background-color: #f8fafc; color: #475569; }
.border-subtle-gray { border: 1px solid #f1f5f9; }
:global([data-theme="dark"]) .bg-pastel-gray { background-color: rgba(255, 255, 255, 0.05); color: #94a3b8; }
:global([data-theme="dark"]) .border-subtle-gray { border-color: rgba(255, 255, 255, 0.08); }

.bg-pastel-primary { background-color: #f0f7ff; color: #3b82f6; border: 1px solid #e0efff; }
:global([data-theme="dark"]) .bg-pastel-primary { background-color: rgba(59, 130, 246, 0.1); color: #60a5fa; border-color: rgba(59, 130, 246, 0.2); }

.dashboard-roi-mini {
  font-size: 0.72rem;
  letter-spacing: -0.01em;
}

.shadow-xs { box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); }
.shadow-sm-inset { box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.05); }




/* Mobile Professional Clean Styles */
@media (max-width: 767.98px) {
  .mobile-metric-row-clean {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.35rem 0;
    font-size: 0.8rem;
  }
  .mobile-metric-label-clean { color: var(--ui-text-muted); }
  .mobile-metric-value-clean { text-align: right; }
  .mobile-overview-card-professional {
    background-color: var(--ui-surface);
    transition: transform 0.1s ease;
  }
  .summary-mobile-card-premium {
    background: var(--ui-surface);
    border-left: 4px solid var(--ui-primary);
  }
}

/* Desktop Premium Table Styles */
.dashboard-table-premium {
  border-collapse: separate;
  border-spacing: 0;
}
.dashboard-table-premium thead th {
  border-bottom: 1px solid var(--ui-border);
  padding: 0.75rem 0.5rem;
}
.account-data-row-premium:hover {
  background-color: var(--ui-table-row-hover) !important;
}

/* Row Highlights (Subtle) */
.overall-summary-row-premium td {
  background-color: var(--ui-primary-soft) !important;
}
.table-group-header-premium td {
  background-color: var(--ui-surface-soft);
}
.category-summary-row-premium td {
  background-color: #f6f8ff !important; /* Distinct light indigo background */
}
:global([data-theme="dark"]) .category-summary-row-premium td {
  background-color: #1a253b !important;
}

/* Interactions */
.account-link-professional:hover {
  color: var(--ui-primary) !important;
  text-decoration: underline !important;
}

.btn-xs {
  padding: 0.15rem 0.4rem;
  font-size: 0.65rem;
}

/* 전일 대비 변동폭: 변동액(색 텍스트)과 등락률(플래그 배지)을 위아래로 분리해 서로 뭉쳐 보이지 않게 */
.dashboard-index-delta-amount {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 700;
  font-size: 0.98rem;
}

.dashboard-index-pct-flag {
  display: inline-flex;
  align-items: center;
  font-weight: 700;
  font-size: 0.86rem;
  padding: 0.1rem 0.55rem 0.1rem 0.7rem;
  clip-path: polygon(9px 0, 100% 0, 100% 100%, 9px 100%, 0 50%);
}

.naver-index-card-wrap:focus-visible {
  outline: 2px solid var(--ui-primary);
  outline-offset: 2px;
}

.index-card {
  position: relative;
  transition: background-color 0.15s ease, border-color 0.15s ease;
  background: var(--ui-surface);
  border: 1px solid var(--ui-border) !important;
}
.index-card:hover,
.naver-index-card-wrap:hover .index-card {
  border-color: var(--ui-border-strong) !important;
  background: var(--ui-surface-soft);
}
.index-card-line {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 4px;
  opacity: 0.8;
}

.bg-profit-soft { background-color: color-mix(in srgb, var(--ui-up) 14%, transparent); color: var(--ui-up); }
.bg-loss-soft { background-color: color-mix(in srgb, var(--ui-down) 14%, transparent); color: var(--ui-down); }
.bg-profit { background-color: var(--ui-up); }
.bg-loss { background-color: var(--ui-down); }
</style>
