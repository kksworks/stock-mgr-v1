<template>
  <div v-if="error" class="alert alert-danger">{{ error }}</div>
  <div v-else-if="detail">
    <div class="d-flex flex-column flex-sm-row justify-content-between align-items-stretch align-items-sm-center gap-2 mb-4 mt-1">
      <h1 class="mb-0 d-flex align-items-center gap-2 h4 fw-bold balance-page-title">
        <MaterialIcon name="monitoring" size="1.75rem" class="text-primary opacity-90" />
        계좌 상세
      </h1>
      <div class="btn-group-wrap top-action-buttons d-flex flex-wrap align-items-center gap-2">
        <button
          v-if="authStore.isAuthenticated"
          type="button"
          class="btn btn-sm btn-tonal-neutral d-inline-flex align-items-center gap-1"
          :disabled="priceRefreshing"
          @click="doPriceRefresh"
        >
          <MaterialIcon name="sync" size="1.1rem" :class="{ 'rotate-animation': priceRefreshing }" />
          <span class="d-none d-sm-inline">{{ priceRefreshing ? '갱신 중…' : '현재가 갱신' }}</span>
          <span class="d-sm-none">갱신</span>
        </button>
        <template v-if="detail.account.user_id === authStore.user?.id || authStore.isAdmin">
          <router-link :to="`/accounts/${detail.account.id}`" class="btn btn-sm btn-tonal-neutral d-inline-flex align-items-center gap-1">
            <MaterialIcon name="receipt_long" size="1.1rem" />
            <span class="d-none d-sm-inline">계좌 상세/내역</span>
            <span class="d-sm-none">내역</span>
          </router-link>
          <button type="button" class="btn btn-sm btn-tonal-neutral d-inline-flex align-items-center gap-1" data-bs-toggle="modal" data-bs-target="#withdrawalModal">
            <MaterialIcon name="calculate" size="1.1rem" />
            <span class="d-none d-sm-inline">시뮬레이션</span>
            <span class="d-sm-none">시뮬</span>
          </button>
        </template>
        <router-link class="btn btn-sm btn-tonal-neutral d-inline-flex align-items-center gap-1" to="/balances">
          <MaterialIcon name="arrow_back" size="1.1rem" />
          목록
        </router-link>
      </div>
    </div>

    <!-- 요약 카드: 대시보드 계좌 카드와 동일하게 왼쪽 액센트만, 배경은 깨끗한 서피스 -->
    <div class="row mb-4 g-3 g-xl-4 align-items-stretch">
      <!-- Left: Main Account Summary Card -->
      <div class="col-12 col-lg-7 col-xl-8">
        <div
          class="card border-0 shadow-sm rounded-4 h-100 overflow-hidden balance-detail-summary"
          :style="{ background: 'var(--ui-surface)', borderLeft: `6px solid ${themeColor}` }"
        >
          <div class="card-body p-4">
            <!-- 1. Account Identity -->
            <div class="d-flex align-items-center gap-3 mb-4">
              <div
                class="rounded-circle d-flex align-items-center justify-content-center balance-detail-icon-ring balance-detail-icon-ring--account"
                :style="{ background: 'var(--ui-surface)', color: themeColor, border: `2px solid ${themeColor}`, width: '48px', height: '48px', flexShrink: 0 }"
              >
                <MaterialIcon name="account_balance" size="1.75rem" />
              </div>
              <div class="d-flex flex-column overflow-hidden">
                <div class="d-flex align-items-center gap-2 mb-1 flex-wrap">
                   <router-link :to="`/accounts/${detail.account?.id}`" class="h5 fw-bold mb-0 text-truncate text-decoration-none hover-primary transition-colors d-inline-flex align-items-center gap-1" :style="{ color: 'var(--ui-text)' }">
                     {{ detail.account?.account_name }}
                     <MaterialIcon name="open_in_new" size="1.05rem" class="opacity-50" />
                   </router-link>
                   <span v-if="detail.account?.owner" class="text-muted fw-medium" style="font-size: 0.85rem;">· {{ detail.account.owner }}</span>
                   <div class="d-flex align-items-center gap-1">
                     <span v-for="tag in (detail.account?.tags || [])" :key="tag" 
                           class="badge rounded-pill" 
                           :style="{ background: 'transparent', border: `1px solid ${getThemeColorByTag(tag)}`, color: getThemeColorByTag(tag), fontSize: '0.65rem', padding: '0.15rem 0.45rem', fontWeight: '600' }">
                       {{ tag }}
                     </span>
                   </div>
                </div>
                <div class="d-flex align-items-center gap-2">
                  <span class="text-muted fw-medium small">{{ detail.account?.account_number }}</span>
                  <span class="text-muted opacity-50">·</span>
                  <span class="badge bg-light text-muted border px-2 py-0.5" style="font-size: 0.7rem;">{{ accountCategory?.name || '미분류' }}</span>
                </div>
              </div>
            </div>

            <!-- 2. Principal Evaluation Section (Highlighted) -->
            <div class="p-3 px-sm-4 mb-4 rounded-4" style="background: rgba(128,128,128,0.05); border: 1px solid var(--ui-border);">
              <div class="row align-items-center g-3">
                <div class="col-12 col-md-auto flex-grow-1">
                  <span class="text-muted fw-bold text-uppercase" style="letter-spacing: 0.05em; font-size: 0.75rem;">현재 평가 자산</span>
                  <div class="h2 fw-bold mb-0 tabular-nums text-success mt-1">₩{{ Math.round(totalAssetValue).toLocaleString() }}</div>
                </div>
                <div v-if="detail.prev_day_asset_change != null" class="col-12 col-md-auto text-md-end ps-md-4 balance-prevday-col">
                  <span class="text-muted fw-bold text-uppercase" style="letter-spacing: 0.05em; font-size: 0.75rem;">전일 대비</span>
                  <div class="d-flex align-items-center justify-content-md-end gap-2 fw-bold mt-1" :class="prevDayChangeClass(detail.prev_day_asset_change)">
                    <div class="d-flex align-items-center gap-0" style="font-size: 1.35rem;">
                      <MaterialIcon :name="detail.prev_day_asset_change >= 0 ? 'arrow_drop_up' : 'arrow_drop_down'" size="1.6rem" />
                      <span class="tabular-nums">{{ formatPrevDayMoney(detail.prev_day_asset_change) }}</span>
                    </div>
                    <span class="opacity-75 pt-1" style="font-size: 0.95rem; font-weight: 500;">({{ formatPrevDayPercent(detail.prev_day_return_vs_principal_pct) }})</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 3. Stats Grid -->
            <div class="row g-4 stats-flat-grid">
              <!-- Col 1 -->
              <div class="col-12 col-md-6 col-xl-4">
                 <div class="d-flex flex-column gap-3">
                   <div class="d-flex justify-content-between align-items-center border-bottom pb-2" :style="{ borderColor: 'var(--ui-border) !important' }">
                     <span class="text-muted small fw-bold">투자 원금</span>
                     <span class="fw-bold tabular-nums" :style="{ color: 'var(--ui-text)' }">₩{{ Number(detail.principal).toLocaleString() }}</span>
                   </div>
                   <div class="d-flex justify-content-between align-items-center border-bottom pb-2" :style="{ borderColor: 'var(--ui-border) !important' }">
                     <span class="text-muted small fw-bold">현금 잔액</span>
                     <span class="fw-bold tabular-nums" :style="{ color: 'var(--ui-text)' }">₩{{ Number(localCash).toLocaleString() }}</span>
                   </div>
                 </div>
              </div>
              <!-- Col 2 -->
              <div class="col-12 col-md-6 col-xl-4">
                 <div class="d-flex flex-column gap-3">
                   <div class="d-flex justify-content-between align-items-center border-bottom pb-2" :style="{ borderColor: 'var(--ui-border) !important' }">
                     <span class="text-muted small fw-bold">평가 손익</span>
                     <span class="fw-bold tabular-nums" :class="investmentReturn >= 0 ? 'text-profit' : 'text-loss'">
                       {{ investmentReturn >= 0 ? '+' : '' }}₩{{ Number(Math.abs(investmentReturn)).toLocaleString() }}
                     </span>
                   </div>
                   <div class="d-flex justify-content-between align-items-center border-bottom pb-2" :style="{ borderColor: 'var(--ui-border) !important' }">
                     <span class="text-muted small fw-bold">수익률 (ROI)</span>
                     <span class="fw-bold tabular-nums" :class="overallReturnRate >= 0 ? 'text-profit' : 'text-loss'">
                       {{ overallReturnRate >= 0 ? '+' : '' }}{{ overallReturnRate.toFixed(2) }}%
                     </span>
                   </div>
                 </div>
              </div>
              <!-- Col 3 -->
              <div class="col-12 col-xl-4">
                 <div class="d-flex flex-column gap-3">
                   <div class="d-flex justify-content-between align-items-center border-bottom pb-2" :style="{ borderColor: 'var(--ui-border) !important' }">
                     <span class="text-muted small fw-bold">최종 리밸런싱</span>
                     <span class="fw-bold" :style="{ color: 'var(--ui-text)' }">{{ detail.last_rebalanced_date || '-' }} <span class="text-muted small ms-1 fw-medium" v-if="daysSinceLastRebalanced">({{ daysSinceLastRebalanced }})</span></span>
                   </div>
                   <div class="d-flex justify-content-between align-items-center border-bottom pb-2" :style="{ borderColor: 'var(--ui-border) !important' }">
                     <span class="text-muted small fw-bold">데이터 업데이트</span>
                     <span class="text-muted small fw-medium">{{ oldestPriceAgeText || '-' }}</span>
                   </div>
                 </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Asset Allocation Card -->
      <div class="col-12 col-lg-5 col-xl-4">
        <div class="card border-0 shadow-sm rounded-4 h-100 overflow-hidden" :style="{ background: 'var(--ui-surface)', borderTop: `6px solid ${themeColor}` }">
          <div class="card-body p-4 d-flex flex-column align-items-center justify-content-center">
             <div class="balance-asset-pie-wrap w-100" style="height: 240px; position: relative;">
               <Doughnut
                  v-if="detailedHoldingsPieData.data.length"
                  :data="doughnutChartConfig"
                  :options="doughnutOptions"
                  :plugins="[ChartDataLabels, balanceCenterTextPlugin]"
               />
               <div v-else class="h-100 d-flex align-items-center justify-content-center text-muted small">
                  보유 자산 없음
               </div>
             </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Chart -->
    <div class="row mb-4">
      <div class="col-12">
          <div class="card shadow-sm border-0 rounded-4 overflow-hidden chart-card" :style="{ background: 'var(--ui-surface)' }">
          <div class="card-header border-bottom py-3 chart-header" :style="{ borderColor: 'var(--ui-border) !important' }">
            <div class="d-flex justify-content-between align-items-center">
              <h5 class="mb-0 fw-bold" :style="{ color: 'var(--ui-text)' }">자산 추이</h5>
              <router-link :to="`/balances/history/${detail.account.id}`" target="_blank" class="btn btn-sm btn-link text-decoration-none d-flex align-items-center gap-1">
                자세히 보기
                <MaterialIcon name="open_in_new" size="1.1rem" />
              </router-link>
            </div>
            <div class="d-flex flex-wrap gap-2 mt-2 align-items-center">
              <button @click="setPeriod(1)" type="button" :class="['btn btn-sm period-btn', periodPreset === 1 ? 'btn-primary' : 'btn-outline-secondary']">1개월</button>
              <button @click="setPeriod(3)" type="button" :class="['btn btn-sm period-btn', periodPreset === 3 ? 'btn-primary' : 'btn-outline-secondary']">3개월</button>
              <button @click="setPeriod(6)" type="button" :class="['btn btn-sm period-btn', periodPreset === 6 ? 'btn-primary' : 'btn-outline-secondary']">6개월</button>
              <button @click="setPeriod(12)" type="button" :class="['btn btn-sm period-btn', periodPreset === 12 ? 'btn-primary' : 'btn-outline-secondary']">1년</button>
              <button @click="setPeriod(24)" type="button" :class="['btn btn-sm period-btn', periodPreset === 24 ? 'btn-primary' : 'btn-outline-secondary']">2년</button>
              <button @click="setPeriod(36)" type="button" :class="['btn btn-sm period-btn', periodPreset === 36 ? 'btn-primary' : 'btn-outline-secondary']">3년</button>
              <input type="date" v-model="startDate" @change="periodPreset = 0" class="form-control form-control-sm" style="width: 130px;">
              <span class="text-muted align-self-center">~</span>
              <input type="date" v-model="endDate" @change="periodPreset = 0" class="form-control form-control-sm" style="width: 130px;">
              <button @click="loadHistory" type="button" class="btn btn-sm btn-primary">조회</button>
            </div>
          </div>
          <div class="card-body chart-body">
            <div class="chart-canvas-wrap">
              <Line v-if="historyData.length > 0" :data="chartData" :options="chartOptions" />
              <div v-else class="chart-empty-state text-center text-muted">
                {{ historyLoading ? '데이터를 불러오는 중...' : '해당 기간의 데이터가 없습니다.' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <form @submit.prevent="save">
      <input type="hidden" name="account_id" :value="detail.account.id">

      <!-- Management Settings -->
      <div class="row mb-4 g-3 align-items-center">
        <!-- Portfolio Section -->
        <div class="col-12 col-md-6 col-lg-5">
          <div class="portfolio-section h-100 px-3 py-2 border rounded-3 bg-light d-flex align-items-center" :style="{ background: 'var(--ui-surface-input) !important', borderColor: 'var(--ui-border) !important' }">
            <label class="form-label fw-bold portfolio-text mb-0 me-3" style="white-space: nowrap;" :style="{ color: 'var(--ui-text)' }">포트폴리오 연결</label>
            <div v-if="isEditing" class="flex-grow-1">
              <select v-model="localLinkedPortfolio" class="form-select form-select-sm border-primary" name="linked_portfolio" :style="{ background: 'var(--ui-surface)', color: 'var(--ui-text)' }">
                <option value="">선택 안함</option>
                <option v-for="pf in detail.portfolios" :key="pf.id" :value="pf.id">
                  {{ pf.name }} ({{ pf.is_public ? `공용 Lv${pf.level}` : '개인' }})
                </option>
              </select>
            </div>
            <div v-else class="d-flex align-items-center flex-grow-1">
              <router-link v-if="localLinkedPortfolio" :to="`/portfolios/${localLinkedPortfolio}`" 
                           class="portfolio-link-text mt-0 fw-bold text-decoration-none d-flex align-items-center gap-2" 
                           title="포트폴리오 상세 보기" :style="{ color: 'var(--ui-text)' }">
                <span>{{ connectedPortfolio?.name || '연결됨' }}</span>
                <span v-if="connectedPortfolio" 
                      class="badge rounded-pill fw-medium border shadow-none" 
                      :style="connectedPortfolio.is_public ? 
                              { background: 'transparent', color: 'var(--bs-primary)', borderColor: 'var(--bs-primary) !important', fontSize: '0.65rem' } : 
                              { background: 'transparent', color: 'gray', borderColor: 'gray !important', fontSize: '0.65rem' }">
                  {{ connectedPortfolio.is_public ? '공용' : '개인' }}
                  {{ connectedPortfolio.is_public ? ' Lv' + connectedPortfolio.level : '' }}
                </span>
                <MaterialIcon name="open_in_new" size="1.05rem" class="opacity-50" />
              </router-link>
              <span v-else class="text-muted small">연결된 포트폴리오 없음</span>
            </div>
          </div>
        </div>

        <!-- Cash Section -->
        <div class="col-12 col-md-6 col-lg-3">
          <div class="cash-edit-section h-100 px-3 py-2 border rounded-3 bg-light d-flex align-items-center" :style="{ background: 'var(--ui-surface-input) !important', borderColor: 'var(--ui-border) !important' }">
            <label class="form-label fw-bold text-primary mb-0 me-3" style="white-space: nowrap;">현금 잔액</label>
            <div v-if="isEditing" class="input-group input-group-sm flex-grow-1">
              <span class="input-group-text bg-white" :style="{ background: 'var(--ui-surface)', borderColor: 'var(--ui-border)', color: 'var(--ui-text)' }">₩</span>
              <input
                v-model.number="localCash"
                type="number"
                class="form-control text-end"
                @input="cashManualOverride = true"
                :style="{ background: 'var(--ui-surface)', borderColor: 'var(--ui-border)', color: 'var(--ui-text)' }"
              >
              <button
                type="button"
                class="btn btn-outline-secondary"
                title="자동 계산으로 되돌리기"
                @click="resetCashAuto"
                :style="{ borderColor: 'var(--ui-border)', color: 'var(--ui-text)' }"
              >
                자동
              </button>
            </div>
            <div v-else class="fw-bold fs-5 mb-0" :style="{ color: 'var(--ui-text)' }">
              <span class="fs-6 fw-normal me-1 text-muted">₩</span>{{ Number(localCash).toLocaleString() }}
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="col-12 col-lg-4 d-flex flex-wrap align-items-center gap-2 justify-content-lg-end">
          <template v-if="detail.account.user_id === authStore.user?.id || authStore.isAdmin">
            <template v-if="!isEditing">
              <button type="button" class="btn btn-primary px-4" @click="startEdit">편집 시작</button>
            </template>
            <template v-else>
              <button type="submit" class="btn btn-success px-4 fw-bold">저장하기</button>
              <button type="button" class="btn btn-outline-secondary" @click="cancelEdit">취소</button>
              <button type="button" class="btn btn-outline-secondary btn-sm" data-bs-toggle="modal" data-bs-target="#addTickerModal">종목 추가</button>
            </template>
          </template>
          <div v-else class="text-muted small italic bg-light p-2 rounded border" :style="{ background: 'var(--ui-surface-input) !important', borderColor: 'var(--ui-border) !important', color: 'var(--ui-text) !important' }">
            <MaterialIcon name="lock" size="1rem" class="me-1" />
            공유된 계좌 (읽기 전용)
          </div>
        </div>
      </div>

      <!-- Holdings Table -->
      <div class="card shadow-sm border-0 rounded-4 overflow-hidden" :style="{ background: 'var(--ui-surface)' }">
        <div class="card-header border-bottom py-3 d-flex flex-column flex-sm-row align-items-start align-items-sm-center justify-content-between gap-2" :style="{ background: 'var(--ui-surface-soft)', borderColor: 'var(--ui-border) !important' }">
          <div class="d-flex align-items-center gap-2 flex-wrap">
            <h5 class="mb-0 fw-bold" :style="{ color: 'var(--ui-text)' }">보유 종목 및 리밸런싱 계획</h5>
            <div class="ms-1 ms-md-2 ps-2 border-start d-flex align-items-center gap-2" :style="{ borderColor: 'var(--ui-border) !important' }">
              <span class="text-muted small">
                최종 리밸런싱:
                <span class="fw-bold" :style="{ color: 'var(--ui-text)' }">{{ detail.last_rebalanced_date || '없음' }}</span>
                <span v-if="daysSinceLastRebalanced" class="ms-1 fw-bold text-primary">({{ daysSinceLastRebalanced }})</span>
              </span>
              <router-link
                :to="`/balances/history/${detail.account.id}?rebalanced_only=true`"
                target="_blank"
                class="text-decoration-none small text-info hover-underline d-flex align-items-center gap-1 fw-semibold"
                style="font-size: 0.72rem;"
              >
                자세히보기
                <MaterialIcon name="chevron_right" size="1rem" />
              </router-link>
            </div>
          </div>
          <small v-if="oldestPriceAgeText" class="text-muted">
            업데이트 {{ oldestPriceUpdatedAtLabel }} · {{ oldestPriceAgeText }}
          </small>
        </div>
        <div class="card-body p-0">
          <!-- Desktop Table -->
          <div class="d-none d-lg-block table-responsive">
            <table class="table table-striped table-hover align-middle mb-0" style="white-space: nowrap; min-width: 1120px;">
              <thead class="text-center">
                <tr>
                  <th rowspan="2" style="vertical-align: middle;" class="header-divider sorting_disabled">종목</th>
                  <th rowspan="2" style="vertical-align: middle;" class="header-divider sorting_disabled">현재가</th>
                  <th rowspan="2" style="vertical-align: middle;" class="header-divider sorting_disabled small">전일대비</th>
                  <th colspan="3" class="table-section-holdings header-divider">보유 현황</th>
                  <th colspan="1" class="table-section-profit header-divider">수익</th>
                  <th colspan="2" class="table-section-rebalancing header-divider">리밸런싱</th>
                  <th rowspan="2" style="vertical-align: middle;">관리</th>
                </tr>
                <tr class="table-light" :style="{ background: 'var(--ui-surface-input) !important' }">
                  <th>수량</th>
                  <th>매수평균가</th>
                  <th class="header-divider">평가금액</th>
                  <th class="header-divider">평가손익 (수익률)</th>
                  <th>비중(현재/목표)</th>
                  <th class="header-divider">매매 필요</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in processedHoldings" :key="item.ticker" :style="{ background: 'var(--ui-surface)' }">
                  <td class="section-divider">
                    <div class="d-flex align-items-center gap-1">
                      <a :href="`https://finance.naver.com/item/main.naver?code=${item.ticker}`" target="_blank" class="text-decoration-none text-primary hover-primary transition-colors d-inline-flex align-items-center gap-1" title="네이버 증권 열기">
                        <span class="fw-bold">{{ item.name }}</span>
                        <MaterialIcon name="open_in_new" size="0.9rem" />
                      </a>
                    </div>
                    <small class="text-muted d-block text-start">{{ item.ticker }}</small>
                    <span
                      class="rounded-pill px-2 py-0 mt-1 d-inline-block text-nowrap balance-asset-class-tag"
                      :style="assetClassBadgeStyle(item.asset_class)"
                    >{{ assetClassLabel(item.asset_class) }}</span>
                  </td>
                  <td class="text-end num-cell section-divider">
                    <span class="text-muted small me-1">₩</span>{{ Number(item.price).toLocaleString() }}
                  </td>
                  <td class="text-end num-cell section-divider small">
                    <span
                      v-if="formatTickerPrevDay(item.prev_day_change, item.prev_day_change_pct)"
                      :class="tickerPrevDayClass(item.prev_day_change)"
                    >
                      {{ formatTickerPrevDay(item.prev_day_change, item.prev_day_change_pct) }}
                    </span>
                    <span v-else class="text-muted">—</span>
                  </td>
                  <td>
                    <div v-if="isEditing">
                      <input v-model.number="localHoldings[idx].quantity" type="number" class="form-control form-control-sm text-end" min="0" style="width: 80px;" :style="{ background: 'var(--ui-surface)', borderColor: 'var(--ui-border)', color: 'var(--ui-text)' }">
                    </div>
                    <div v-else class="text-end num-cell">
                      {{ Number(item.quantity).toLocaleString() }}
                    </div>
                  </td>
                  <td>
                    <div v-if="isEditing">
                      <input v-model.number="localHoldings[idx].avg_purchase_price" type="number" class="form-control form-control-sm text-end" min="0" style="width: 100px;" :style="{ background: 'var(--ui-surface)', borderColor: 'var(--ui-border)', color: 'var(--ui-text)' }">
                    </div>
                    <div v-else class="text-end num-cell">
                      <span class="text-muted small me-1">₩</span>{{ Number(item.avg_purchase_price).toLocaleString() }}
                    </div>
                  </td>
                  <td class="text-end num-cell section-divider">
                    <span class="text-muted small me-1">₩</span>{{ Number(item.value).toLocaleString() }}
                  </td>
                  <td class="text-end num-cell section-divider" :class="item.profit_loss > 0 ? 'text-danger' : item.profit_loss < 0 ? 'text-primary' : ''">
                    <div class="fw-bold">{{ item.profit_loss >= 0 ? '+' : '' }}₩{{ Number(item.profit_loss).toLocaleString() }}</div>
                    <small>({{ Number(item.return_rate).toFixed(2) }}%)</small>
                  </td>
                  <td class="text-center num-cell small">
                    <div class="fw-bold">{{ (item.current_ratio * 100).toFixed(1) }}% <span class="text-muted fw-normal">/ {{ (item.target_ratio * 100).toFixed(1) }}%</span></div>
                    <span :class="(item.current_ratio - item.target_ratio) > 0.0001 ? 'text-danger' : (item.current_ratio - item.target_ratio) < -0.0001 ? 'text-primary' : 'text-muted'" style="font-size: 0.75rem;">
                      ({{ (item.current_ratio - item.target_ratio) > 0.0001 ? '+' : '' }}{{ ((item.current_ratio - item.target_ratio) * 100).toFixed(1) }}pp)
                    </span>
                    <div v-if="relativeDeviationPct(item) != null" class="balance-relative-deviation" :class="relativeDeviationClass(item)">
                      이격도 {{ relativeDeviationPct(item).toFixed(0) }}%
                    </div>
                  </td>
                  <td class="text-center num-cell section-divider">
                    <div class="d-flex flex-column align-items-center gap-1">
                      <span v-if="item.action === 'buy'" class="badge bg-danger rounded-pill px-3">매수</span>
                      <span v-else-if="item.action === 'sell'" class="badge bg-primary rounded-pill px-3">매도</span>
                      <span v-else-if="item.action === 'hold'" class="badge bg-secondary rounded-pill px-3">유지</span>
                      <span v-else class="badge bg-secondary rounded-pill px-3">-</span>
                      
                      <div v-if="item.action !== 'hold' && item.action !== '-'" class="small mt-1" :class="item.action === 'buy' ? 'text-danger' : 'text-primary'">
                         <span class="fw-bold">{{ item.diff_qty }}주</span>
                         <div class="text-muted" style="font-size: 0.7rem;">(₩{{ Number(item.diff_amount).toLocaleString() }})</div>
                      </div>
                    </div>
                  </td>
                  <td class="text-center">
                    <div v-if="isEditing" class="d-inline-flex align-items-center gap-1">
                      <button
                        type="button"
                        class="btn btn-outline-secondary btn-sm p-1 leading-none shadow-none border-0"
                        :disabled="idx === 0"
                        title="위로 이동"
                        @click="moveHolding(idx, -1)"
                      >
                        <MaterialIcon name="arrow_upward" size="1.0rem" />
                      </button>
                      <button
                        type="button"
                        class="btn btn-outline-secondary btn-sm p-1 leading-none shadow-none border-0"
                        :disabled="idx === localHoldings.length - 1"
                        title="아래로 이동"
                        @click="moveHolding(idx, 1)"
                      >
                        <MaterialIcon name="arrow_downward" size="1.0rem" />
                      </button>
                      <button
                        @click="removeHolding(idx)"
                        type="button"
                        class="btn btn-outline-danger btn-sm p-1 leading-none shadow-none border-0 hover-danger"
                        title="삭제"
                      >
                        <MaterialIcon name="delete" size="1.1rem" />
                      </button>
                    </div>
                    <span v-else class="text-muted small">-</span>
                  </td>
                </tr>
                <tr v-if="localHoldings.length === 0">
                  <td colspan="11" class="text-center py-5 text-muted">
                    <MaterialIcon name="inventory_2" size="2.5rem" class="mb-2 d-block mx-auto opacity-25" />
                    보유 중인 종목이 없습니다. 편집 모드에서 종목을 추가하세요.
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mobile List -->
          <div class="d-lg-none d-flex flex-column gap-2 p-3 bg-light">
            <div v-for="(item, idx) in processedHoldings" :key="item.ticker" class="card shadow-sm border-0 border-start border-4 mb-1" :class="item.profit_loss > 0 ? 'border-danger' : item.profit_loss < 0 ? 'border-primary' : 'border-secondary'">
              <div class="card-body p-3">
                <div class="d-flex justify-content-between align-items-start mb-2">
                  <div>
                    <div class="d-flex align-items-center gap-1">
                      <a :href="`https://finance.naver.com/item/main.naver?code=${item.ticker}`" target="_blank" class="text-decoration-none text-primary fw-bold">
                        {{ item.name }}
                      </a>
                      <span class="text-muted tiny">{{ item.ticker }}</span>
                    </div>
                    <span
                      class="rounded-pill px-2 py-0 mt-1 d-inline-block text-nowrap balance-asset-class-tag"
                      :style="assetClassBadgeStyle(item.asset_class)"
                    >{{ assetClassLabel(item.asset_class) }}</span>
                    <div class="text-muted small mt-1">현재가: ₩{{ Number(item.price).toLocaleString() }}</div>
                    <div
                      v-if="formatTickerPrevDay(item.prev_day_change, item.prev_day_change_pct)"
                      class="small"
                      :class="tickerPrevDayClass(item.prev_day_change)"
                    >
                      전일대비 {{ formatTickerPrevDay(item.prev_day_change, item.prev_day_change_pct) }}
                    </div>
                  </div>
                  <div class="text-end">
                    <div class="fw-bold">₩{{ Number(item.value).toLocaleString() }}</div>
                    <div class="small" :class="item.profit_loss > 0 ? 'text-danger' : item.profit_loss < 0 ? 'text-primary' : ''">
                      {{ item.profit_loss >= 0 ? '+' : '' }}₩{{ Number(item.profit_loss).toLocaleString() }}
                      <span class="tiny">({{ Number(item.return_rate).toFixed(2) }}%)</span>
                    </div>
                  </div>
                </div>

                <div v-if="isEditing" class="p-2 bg-light rounded mb-2 border">
                  <div class="row g-2">
                    <div class="col-6">
                      <label class="tiny text-muted d-block">수량</label>
                      <input v-model.number="localHoldings[idx].quantity" type="number" class="form-control form-control-sm text-end">
                    </div>
                    <div class="col-6">
                      <label class="tiny text-muted d-block">매수평가</label>
                      <input v-model.number="localHoldings[idx].avg_purchase_price" type="number" class="form-control form-control-sm text-end">
                    </div>
                  </div>
                </div>
                <div v-else class="row g-1 mb-2">
                  <div class="col-6 text-muted tiny">보유: {{ Number(item.quantity).toLocaleString() }}주</div>
                  <div class="col-6 text-muted tiny text-end">평단: ₩{{ Number(item.avg_purchase_price).toLocaleString() }}</div>
                </div>

                <div class="d-flex justify-content-between align-items-center pt-2 border-top">
                  <div class="d-flex align-items-center gap-2">
                    <span v-if="item.action === 'buy'" class="badge bg-danger tiny">매수 필요: {{ item.diff_qty }}주</span>
                    <span v-else-if="item.action === 'sell'" class="badge bg-primary tiny">매도 필요: {{ item.diff_qty }}주</span>
                    <span v-else class="badge bg-secondary tiny">{{ item.action === 'hold' ? '유지' : '-' }}</span>
                    <span class="tiny text-muted">{{ (item.current_ratio * 100).toFixed(1) }}% / {{ (item.target_ratio * 100).toFixed(1) }}%</span>
                    <span v-if="relativeDeviationPct(item) != null" class="tiny balance-relative-deviation" :class="relativeDeviationClass(item)">
                      이격도 {{ relativeDeviationPct(item).toFixed(0) }}%
                    </span>
                  </div>
                  <div v-if="isEditing" class="d-flex gap-1">
                     <button type="button" class="btn btn-sm btn-outline-secondary p-1 border-0" :disabled="idx === 0" @click="moveHolding(idx, -1)"><MaterialIcon name="arrow_upward" size="0.9rem" /></button>
                     <button type="button" class="btn btn-sm btn-outline-secondary p-1 border-0" :disabled="idx === localHoldings.length - 1" @click="moveHolding(idx, 1)"><MaterialIcon name="arrow_downward" size="0.9rem" /></button>
                     <button type="button" class="btn btn-sm btn-outline-danger p-1 border-0" @click="removeHolding(idx)"><MaterialIcon name="delete" size="0.9rem" /></button>
                  </div>
                </div>
              </div>
            </div>
            <div v-if="localHoldings.length === 0" class="text-center py-4 text-muted bg-white rounded shadow-sm">
               종목이 없습니다.
            </div>
          </div>
        </div>
      </div>
    </form>

    <!-- Modals (Add Ticker, Withdrawal Simulation) -->
    <div class="modal fade" id="addTickerModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content shadow border-0">
          <div class="modal-header border-bottom-0 pb-0">
            <h5 class="modal-title fw-bold">종목 추가</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div class="input-group mb-3">
              <input v-model="tickerSearchQuery" type="text" class="form-control" placeholder="종목명 또는 티커 검색" @keypress.enter.prevent="doTickerSearch">
              <button type="button" class="btn btn-primary px-3" @click="doTickerSearch">검색</button>
            </div>
            <div class="list-group list-group-flush border rounded-3 overflow-hidden" style="max-height: 300px; overflow-y: auto;">
              <button
                v-for="item in tickerSearchResults"
                :key="item.ticker"
                type="button"
                class="list-group-item list-group-item-action d-flex justify-content-between align-items-center py-3"
                @click="addHoldingFromSearch(item)"
              >
                <div>
                  <div class="fw-bold">{{ item.name }}</div>
                  <small class="text-muted">{{ item.ticker }}</small>
                </div>
                <MaterialIcon name="add_circle" class="text-primary" />
              </button>
              <div v-if="tickerSearchResults.length === 0 && tickerSearchQuery" class="text-center py-4 text-muted small">
                검색 결과가 없습니다.
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="modal fade" id="withdrawalModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content shadow border-0">
          <div class="modal-header bg-warning border-0">
            <h5 class="modal-title fw-bold d-flex align-items-center gap-2">
              <MaterialIcon name="savings" size="1.35rem" />
              출금 시뮬레이션
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body p-4">
            <div class="mb-4">
              <label class="form-label fw-bold">출금하고자 하는 금액</label>
              <div class="input-group input-group-lg">
                <span class="input-group-text bg-white border-end-0 text-muted">₩</span>
                <input v-model.number="withdrawalAmount" type="number" class="form-control border-start-0" placeholder="0" @keypress.enter.prevent>
              </div>
              <div class="form-text mt-2 text-muted">
                <MaterialIcon name="info" size="0.9rem" class="align-middle me-1" />
                입력하신 금액을 인출하기 위해 어떤 종목을 얼마나 팔아야 하는지 비중을 유지하며 계산합니다.
              </div>
            </div>

            <div v-if="withdrawalSimulation" class="simulation-results">
              <div class="card mb-4 border-0 bg-light p-3">
                <div class="row text-center">
                  <div class="col-6 border-end">
                    <div class="text-muted small mb-1">수익금(Profit) 기반</div>
                    <div class="fw-bold text-danger h5 mb-0">₩{{ Number(withdrawalSimulation.profitSource).toLocaleString() }}</div>
                  </div>
                  <div class="col-6">
                    <div class="text-muted small mb-1">투자 원찰(Principal) 기반</div>
                    <div class="fw-bold h5 mb-0" :class="withdrawalSimulation.principalSource > 0 ? 'text-primary' : 'text-muted'">
                      ₩{{ Number(withdrawalSimulation.principalSource).toLocaleString() }}
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="!localLinkedPortfolio" class="alert alert-warning small py-2 mb-3">
                <MaterialIcon name="warning" size="0.9rem" class="me-1 align-middle" /> 
                포트폴리오가 연결되어 있지 않아 기존 보유 비중에 따라 균등 매도를 제안합니다.
              </div>

              <h6 class="fw-bold mb-3 mt-4 text-dark fst-italic border-bottom pb-2">추천 매매 내역 (리밸런싱 포함)</h6>
              <div class="table-responsive">
                <table class="table table-sm table-hover align-middle">
                  <thead class="table-light text-center small">
                    <tr>
                      <th class="py-2">종목명</th>
                      <th class="py-2">구분</th>
                      <th class="py-2">수량</th>
                      <th class="py-2">매매금액</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="t in withdrawalSimulation.tradeList" :key="t.ticker">
                      <td class="py-2">
                        <div class="fw-bold">{{ t.name }}</div>
                        <small class="text-muted text-xs">{{ t.ticker }}</small>
                      </td>
                      <td class="text-center py-2">
                        <span class="badge rounded-pill" :class="t.action === 'sell' ? 'bg-primary-subtle text-primary border border-primary' : 'bg-danger-subtle text-danger border border-danger'">
                          {{ t.action === 'sell' ? '매도' : '매수' }}
                        </span>
                      </td>
                      <td class="text-center py-2 fw-bold">{{ t.quantity.toLocaleString() }}주</td>
                      <td class="text-end py-2 num-cell">₩{{ t.amount.toLocaleString() }}</td>
                    </tr>
                    <tr v-if="withdrawalSimulation.tradeList.length === 0">
                      <td colspan="4" class="text-center py-4 text-muted small">매매할 항목이 없습니다.</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              
              <div v-if="Math.abs(withdrawalSimulation.netCashOut - withdrawalSimulation.requestedAmount) > 1000" class="alert alert-info small py-2 mt-3">
                <MaterialIcon name="info" size="1rem" class="me-1 align-middle" /> 
                요청 금액과 결과 금액이 일부 차이날 수 있습니다. (사유: 단주 매매 제약 등)
              </div>
            </div>
          </div>
          <div class="modal-footer border-0">
            <button type="button" class="btn btn-secondary px-4 rounded-pill" data-bs-dismiss="modal">닫기</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="loading" class="text-center py-5 my-5">
    <div class="spinner-border text-primary mb-3" role="status"></div>
    <div class="text-muted">데이터를 구성하는 중...</div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { accountApi, portfolioApi, stockApi, userApi, getApiErrorMessage } from '../api'
import { pollUntilBalanceDetailFresh } from '../composables/useBalanceRefreshPolling'
import { authStore } from '../stores/auth'
import { getKstTodayDateInput, toKstDateInput } from '../utils/dateTime'
import {
  formatPrevDayMoney,
  formatPrevDayPercent,
  prevDayChangeClass,
} from '../utils/prevDayAsset'

// --- Chart.js ---
import { Line, Doughnut } from 'vue-chartjs'
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
  ArcElement,
  LineController,
  DoughnutController,
  BarElement,
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
  ArcElement,
  LineController,
  DoughnutController,
  BarElement,
  BarController
)
// ----------------

const emit = defineEmits(['flash'])
const route = useRoute()
const accountId = computed(() => route.params.accountId ? decodeURIComponent(route.params.accountId) : '')
const detail = ref(null)
const error = ref('')
const loading = ref(true)
const priceRefreshing = ref(false)
const isEditing = ref(false)
const editingFixedTotalAsset = ref(null)
const savingEdit = ref(false)
const cashManualOverride = ref(false)

const daysSinceLastRebalanced = computed(() => {
  if (!detail.value?.last_rebalanced_date) return ''
  try {
    const last = new Date(detail.value.last_rebalanced_date)
    last.setHours(0, 0, 0, 0)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    const diffTime = today - last
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
    if (diffDays === 0) return '오늘'
    return `${diffDays}일 전`
  } catch (e) {
    return ''
  }
})

const localLinkedPortfolio = ref('')
const localHoldings = ref([])
const tickerSearchQuery = ref('')
const tickerSearchResults = ref([])
const withdrawalAmount = ref(0)
const localCash = ref(0)
const categories = ref([])
const accountCategoryMap = ref({})

const accountCategory = computed(() => {
  if (!detail.value || !categories.value || categories.value.length === 0) return null;
  const catId = accountCategoryMap.value[detail.value.account.id];
  return categories.value.find(c => c.id === catId) || null;
});

const connectedPortfolio = computed(() => {
  if (!detail.value?.portfolios || !localLinkedPortfolio.value) return null;
  return detail.value.portfolios.find(p => p.id === localLinkedPortfolio.value);
});

const getThemeColorByTag = (tag) => {
  if (!tag) return 'var(--color-category-1)';
  // Simple stable hash based on name (consistent with BalanceList)
  let hash = 0;
  for (let i = 0; i < tag.length; i++) {
    hash = tag.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % 8 + 1;
  return `var(--color-category-${index})`;
}

const themeColor = computed(() => {
  const tag = accountCategory.value?.name || detail.value?.account?.account_name;
  return getThemeColorByTag(tag);
});

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

let detailAbortController = null
let historyAbortController = null
let priceAbortController = null
let tickerSearchAbortController = null
let detailReqId = 0
let historyReqId = 0
let priceReqId = 0
let tickerSearchReqId = 0

// --- History & Chart ---
const historyData = ref([])
const historyLoading = ref(false)

const savedStartDate = ref('')
const savedEndDate = ref('')
const periodPreset = ref(1)

const startDate = ref('')
const endDate = ref('')

const chartThemeVersion = ref(0)
let chartThemeObserver = null

// Load from localStorage based on user ID
watch(() => authStore.user?.id, (userId) => {
  if (userId) {
    const keyPrefix = `balanceDetail_${userId}_`
    savedStartDate.value = localStorage.getItem(`${keyPrefix}startDate`)
    savedEndDate.value = localStorage.getItem(`${keyPrefix}endDate`)
    const savedPreset = localStorage.getItem(`${keyPrefix}periodPreset`)
    
    periodPreset.value = savedPreset !== null ? parseInt(savedPreset, 10) : 1
    startDate.value = savedStartDate.value || toKstDateInput(Date.now() - 30 * 24 * 60 * 60 * 1000)
    endDate.value = savedEndDate.value || getKstTodayDateInput()
  }
}, { immediate: true })

watch([startDate, endDate, periodPreset], ([newStart, newEnd, newPreset]) => {
  const userId = authStore.user?.id
  if (userId) {
    const keyPrefix = `balanceDetail_${userId}_`
    localStorage.setItem(`${keyPrefix}startDate`, newStart)
    localStorage.setItem(`${keyPrefix}endDate`, newEnd)
    localStorage.setItem(`${keyPrefix}periodPreset`, String(newPreset))
  }
})

const chartData = computed(() => {
  chartThemeVersion.value
  const rootStyle = getComputedStyle(document.documentElement)
  const palette = {
    asset: rootStyle.getPropertyValue('--ui-primary').trim() || '#2563eb',
    principal: rootStyle.getPropertyValue('--ui-text-muted').trim() || '#64748b',
    profit: rootStyle.getPropertyValue('--ui-up').trim() || '#dc2626',
    // ROI는 다른 금액 라인과 겹치지 않도록 별도 색상군 사용
    roi: rootStyle.getPropertyValue('--ui-alert-info-text').trim() || '#14b8a6',
  }
  const datasets = [
    {
      label: '총 자산',
      data: historyData.value.map(d => d.total_asset_value),
      borderColor: palette.asset,
      backgroundColor: palette.asset,
      yAxisID: 'y',
      tension: 0.26,
      borderWidth: 2,
      pointRadius: 0,
      pointHoverRadius: 4,
    },
    {
      label: '원금',
      data: historyData.value.map(d => d.principal),
      borderColor: palette.principal,
      backgroundColor: palette.principal,
      yAxisID: 'y',
      tension: 0.24,
      borderWidth: 1.6,
      pointRadius: 0,
      pointHoverRadius: 3,
    }
  ]

  datasets.push({
    label: '수익금',
    data: historyData.value.map(d => d.investment_return),
    borderColor: palette.profit,
    backgroundColor: palette.profit,
    yAxisID: 'y',
    tension: 0.26,
    borderWidth: 1.8,
    pointRadius: 0,
    pointHoverRadius: 4,
  })

  datasets.push({
    type: 'line',
    label: '수익률 (%)',
    data: historyData.value.map(d => d.return_rate),
    borderColor: palette.roi,
    backgroundColor: (context) => {
      const chart = context.chart
      const { ctx, chartArea } = chart
      if (!chartArea) return toAlphaColor(palette.roi, 0.16)
      const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom)
      gradient.addColorStop(0, toAlphaColor(palette.roi, 0.24))
      gradient.addColorStop(0.55, toAlphaColor(palette.roi, 0.12))
      gradient.addColorStop(1, toAlphaColor(palette.roi, 0.03))
      return gradient
    },
    yAxisID: 'y1',
    fill: 'origin',
    tension: 0.25,
    borderWidth: 1.6,
    pointRadius: 0,
    pointHoverRadius: 3,
    order: 0,
  })

  return {
    labels: historyData.value.map(d => d.date),
    datasets
  }
})

function formatCompactKrw(value) {
  const n = Number(value || 0)
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : ''

  if (abs >= 100000000) {
    const v = abs / 100000000
    return `${sign}${v >= 10 ? v.toFixed(0) : v.toFixed(1)}억`
  }
  if (abs >= 10000) {
    const v = abs / 10000
    return `${sign}${v >= 100 ? v.toFixed(0) : v.toFixed(1)}만`
  }
  if (abs >= 1000) {
    const v = abs / 1000
    return `${sign}${v >= 100 ? v.toFixed(0) : v.toFixed(1)}K`
  }
  return `${sign}${abs.toFixed(0)}`
}

function toAlphaColor(color, alpha) {
  const normalizedAlpha = Math.max(0, Math.min(1, Number(alpha)))
  const c = String(color || '').trim()

  if (c.startsWith('#')) {
    const hex = c.slice(1)
    const full = hex.length === 3 ? hex.split('').map((ch) => ch + ch).join('') : hex
    if (/^[0-9a-fA-F]{6}$/.test(full)) {
      const r = parseInt(full.slice(0, 2), 16)
      const g = parseInt(full.slice(2, 4), 16)
      const b = parseInt(full.slice(4, 6), 16)
      return `rgba(${r}, ${g}, ${b}, ${normalizedAlpha})`
    }
  }

  const rgbMatch = c.match(/^rgb\(([^)]+)\)$/i)
  if (rgbMatch) return `rgba(${rgbMatch[1]}, ${normalizedAlpha})`

  const rgbaMatch = c.match(/^rgba\(([^)]+)\)$/i)
  if (rgbaMatch) {
    const parts = rgbaMatch[1].split(',').map((part) => part.trim())
    if (parts.length >= 3) {
      return `rgba(${parts[0]}, ${parts[1]}, ${parts[2]}, ${normalizedAlpha})`
    }
  }

  return c || `rgba(96, 165, 250, ${normalizedAlpha})`
}

function buildChartTickIndexSet(totalLabels) {
  if (totalLabels <= 0) return new Set()
  // Always show first/last, and fill middle points evenly.
  const targetTicks = totalLabels <= 8 ? totalLabels : 8
  const indices = new Set([0, totalLabels - 1])
  if (totalLabels <= targetTicks) {
    for (let i = 0; i < totalLabels; i += 1) indices.add(i)
    return indices
  }
  const innerTickCount = Math.max(0, targetTicks - 2)
  for (let i = 1; i <= innerTickCount; i += 1) {
    const idx = Math.round((i * (totalLabels - 1)) / (innerTickCount + 1))
    indices.add(Math.min(totalLabels - 2, Math.max(1, idx)))
  }
  return indices
}

const chartOptions = computed(() => {
  chartThemeVersion.value
  const rootStyle = getComputedStyle(document.documentElement)
  const colorText = rootStyle.getPropertyValue('--ui-text-subtle').trim() || '#334155'
  const colorMuted = rootStyle.getPropertyValue('--ui-text-muted').trim() || '#64748b'
  const colorGrid = rootStyle.getPropertyValue('--ui-border').trim() || '#e5e7ee'

  const labels = historyData.value.map((d) => d.date)
  const visibleTickIndices = buildChartTickIndexSet(labels.length)

  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    animation: false,
    scales: {
      x: {
        offset: true,
        ticks: {
          color: colorMuted,
          autoSkip: false,
          maxRotation: 0,
          minRotation: 0,
          callback: (_val, idx) => {
            if (!labels[idx]) return ''
            if (!visibleTickIndices.has(idx)) return ''
            const parts = String(labels[idx]).split('-')
            return parts.length === 3 ? `${Number(parts[1])}/${Number(parts[2])}` : labels[idx]
          },
        },
        grid: {
          display: false,
        },
      },
      y: {
        type: 'linear',
        display: true,
        position: 'left',
        title: { display: true, text: '금액 (₩)', color: colorMuted },
        ticks: {
          color: colorMuted,
          callback: (val) => '₩' + formatCompactKrw(val),
        },
        grid: {
          color: `${colorGrid}aa`,
        },
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        title: { display: true, text: '수익률 (%)', color: colorMuted },
        grid: { drawOnChartArea: false },
        ticks: {
          color: colorMuted,
          callback: (val) => `${val}%`,
        },
      },
    },
    plugins: {
      legend: {
        labels: {
          color: colorText,
          boxWidth: 14,
          usePointStyle: true,
          pointStyle: 'line',
        },
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            let label = context.dataset.label || ''
            if (label) label += ': '
            const isRoi = context.dataset.yAxisID === 'y1'
            return isRoi ? `${label}${context.parsed.y}%` : `${label}₩${formatCompactKrw(context.parsed.y)}`
          },
        },
      },
    },
  }
})

/** 대시보드와 동일한 스타일의 팔레트 */
const CHART_COLORS = [
  '#6366f1', '#8b5cf6', '#06b6d4', '#10b981',
  '#f59e0b', '#ec4899', '#3b82f6', '#14b8a6',
  '#a855f7', '#64748b',
]

const balanceCenterTextPlugin = {
  id: 'balanceCenterText',
  beforeDraw(chart) {
    if (!chart.chartArea) return
    const { ctx, chartArea: { width, height, top } } = chart
    ctx.save()
    const centerX = width / 2
    const centerY = top + height / 2
    ctx.font = 'bold 9px "JetBrains Mono", "IBM Plex Mono", monospace'
    ctx.fillStyle = '#8b9bb4'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText('ASSET MIX', centerX, centerY)
    ctx.restore()
  },
}

const detailedHoldingsPieData = computed(() => {
  if (!detail.value) return { labels: [], data: [] }
  const map = new Map()
  
  // 보유 종목 (CASH 제외는 이미 필터링되어 있음)
  processedHoldings.value.forEach(h => {
    const ac = assetClassLabel(h.asset_class)
    const val = Number(h.value || 0)
    if (val > 0) {
      map.set(ac, (map.get(ac) || 0) + val)
    }
  })
  
  // 현금
  const cashVal = Number(localCash.value || 0)
  if (cashVal > 0) {
    map.set('현금', (map.get('현금') || 0) + cashVal)
  }
  
  const entries = [...map.entries()].sort((a, b) => b[1] - a[1])
  if (entries.length === 0) return { labels: [], data: [] }
  
  const top = 6
  const head = entries.slice(0, top)
  const rest = entries.slice(top).reduce((s, [, v]) => s + v, 0)
  const labels = head.map(([k]) => k)
  const data = head.map(([, v]) => v)
  if (rest > 0) {
    labels.push('기타')
    data.push(rest)
  }
  return { labels, data }
})

const doughnutChartConfig = computed(() => {
  const { labels, data } = detailedHoldingsPieData.value
  const bg = labels.map((_, i) => CHART_COLORS[i % CHART_COLORS.length])
  return {
    labels,
    datasets: [
      {
        data,
        backgroundColor: bg,
        borderWidth: 2,
        borderColor: '#ffffff',
      },
    ],
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '68%',
  animation: false,
  plugins: {
    legend: { display: false },
    datalabels: {
      color: '#ffffff',
      anchor: 'center',
      align: 'center',
      font: { weight: '700', size: 10, family: 'Inter, sans-serif' },
      formatter: (value, ctx) => {
        const v = Number(value)
        if (!Number.isFinite(v) || v <= 0) return null
        const arr = ctx.chart?.data?.datasets?.[0]?.data || []
        const total = arr.reduce((a, b) => a + Number(b || 0), 0) || 1
        const pct = (v / total) * 100
        if (pct < 10) return null
        const label = ctx.chart.data.labels[ctx.dataIndex]
        return `${label}\n${pct.toFixed(0)}%`
      },
      textAlign: 'center',
      textStrokeColor: 'rgba(0,0,0,0.7)',
      textStrokeWidth: 2,
    },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const v = Number(ctx.raw ?? ctx.parsed ?? 0)
          const arr = ctx.dataset?.data || []
          const total = arr.reduce((a, b) => a + Number(b || 0), 0) || 1
          const pct = ((v / total) * 100).toFixed(1)
          return `${ctx.label}: ₩${v.toLocaleString()} (${pct}%)`
        },
      },
    },
  },
}

async function loadHistory() {
  if (!accountId.value) return
  if (historyAbortController) {
    historyAbortController.abort()
  }
  historyAbortController = new AbortController()
  const reqId = ++historyReqId
  historyLoading.value = true
  try {
    const { data } = await accountApi.fetchBalanceHistory(
      accountId.value,
      startDate.value,
      endDate.value,
      false, // rebalancedOnly
      { signal: historyAbortController.signal }
    )
    if (reqId !== historyReqId) return
    historyData.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    if (reqId !== historyReqId) return
    emit('flash', getApiErrorMessage(e, '히스토리 조회 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    if (reqId !== historyReqId) return
    historyLoading.value = false
  }
}

function setPeriod(months) {
  periodPreset.value = months
  const end = new Date()
  const start = new Date()
  start.setMonth(end.getMonth() - months)
  
  startDate.value = toKstDateInput(start)
  endDate.value = toKstDateInput(end)
  loadHistory()
}
// -----------------------

const stockValueLive = computed(() => (
  localHoldings.value.reduce((sum, h) => sum + (Number(h.quantity || 0) * Number(h.price || 0)), 0)
))

const totalAssetValue = computed(() => {
  if (isEditing.value && Number.isFinite(Number(editingFixedTotalAsset.value))) {
    return Number(editingFixedTotalAsset.value)
  }
  return stockValueLive.value + Number(localCash.value || 0)
})

const processedHoldings = computed(() => {
  const total = totalAssetValue.value
  return localHoldings.value.map(h => {
    const qty = Number(h.quantity || 0)
    const prc = Number(h.price || 0)
    const avg = Number(h.avg_purchase_price || 0)
    const targetRatio = Number(h.target_ratio || 0)
    
    const value = qty * prc
    const cost = qty * avg
    const profit_loss = value - cost
    const return_rate = cost > 0 ? (profit_loss / cost) * 100 : 0
    const current_ratio = total > 0 ? value / total : 0
    
    const targetValue = total * targetRatio
    const diff_amount = targetValue - value
    let diff_qty = prc > 0 ? Math.round(diff_amount / prc) : 0
    
    // Action logic
    let action = 'hold'
    if (diff_qty > 0) action = 'buy'
    else if (diff_qty < 0) action = 'sell'
    
    return {
      ...h,
      value,
      profit_loss,
      return_rate,
      current_ratio,
      target_ratio: targetRatio,
      diff_amount: Math.round(Math.abs(diff_amount)),
      diff_qty: Math.abs(diff_qty),
      action
    }
  })
})

const investmentReturn = computed(() => {
  if (!detail.value) return 0
  return totalAssetValue.value - Number(detail.value.principal || 0)
})

const overallReturnRate = computed(() => {
  const p = Number(detail.value?.principal || 0)
  if (p === 0) return 0
  return (investmentReturn.value / p) * 100
})

const oldestPriceUpdatedAtLabel = computed(() => {
  const raw = detail.value?.oldest_price_updated_at
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

const oldestPriceAgeText = computed(() => {
  const minutes = Number(detail.value?.oldest_price_age_minutes)
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
})

/** 티커 시세 전일대비(원·%) — 네이버 크롤 메타 */
function formatTickerPrevDay(won, pct) {
  if ((won == null || won === '') && (pct == null || pct === '')) return ''
  const parts = []
  if (won != null && won !== '' && Number.isFinite(Number(won))) {
    const v = Number(won)
    const arrow = v > 0 ? '▲' : v < 0 ? '▼' : ''
    parts.push(`${arrow} ${Math.abs(v).toLocaleString()}원`)
  }
  if (pct != null && pct !== '' && Number.isFinite(Number(pct))) {
    const p = Number(pct)
    parts.push(`(${p >= 0 ? '+' : ''}${p.toFixed(2)}%)`)
  }
  return parts.join(' ')
}

function tickerPrevDayClass(won) {
  if (won == null || won === '' || !Number.isFinite(Number(won))) return ''
  const v = Number(won)
  if (v > 0) return 'text-danger'
  if (v < 0) return 'text-primary'
  return 'text-muted'
}

/**
 * 목표 비중 대비 "상대" 이격도(%) — 대시보드의 accountMaxDeviationPct와 동일한 공식.
 * 절대 이격도(현재-목표, pp)와 달리 목표 크기에 비례해 심각도를 따진다:
 * 목표 10%에서 1%p 벗어난 것(상대 10%)이 목표 20%에서 1%p 벗어난 것(상대 5%)보다 더 크게 나온다.
 * 목표 비중이 0(포트폴리오 미편입 보유분)이면 "목표 대비 비율"이 정의되지 않아 null.
 */
function relativeDeviationPct(item) {
  const current = Number(item?.current_ratio)
  const target = Number(item?.target_ratio)
  if (!Number.isFinite(current) || !Number.isFinite(target) || target <= 0) return null
  return Math.abs(current - target) / target * 100
}

/** 이격도가 클수록(리밸런싱 필요도가 높을수록) 경고색 — "5/25 규칙"의 상대 기준(25%)을 따름 */
function relativeDeviationClass(item) {
  const pct = relativeDeviationPct(item)
  if (pct == null) return ''
  return pct >= 25 ? 'balance-relative-deviation--warn' : ''
}

/** PortfolioDetail / 대시보드 자산분류 도넛과 맞춘 팔레트 — 분류명마다 고정 색 */
const ASSET_CLASS_TAG_COLORS = [
  '#2a69d4', '#e84c3d', '#27ae60', '#f1c40f', '#9b59b6',
  '#1abc9c', '#e67e22', '#34495e', '#7f8c8d', '#d35400',
]

function assetClassLabel(ac) {
  if (ac == null || String(ac).trim() === '') return '미분류'
  return String(ac).trim()
}

function assetClassColorIndex(ac) {
  const s = assetClassLabel(ac)
  let h = 0
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0
  return h % ASSET_CLASS_TAG_COLORS.length
}

function assetClassBadgeStyle(ac) {
  const hex = ASSET_CLASS_TAG_COLORS[assetClassColorIndex(ac)]
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return {
    backgroundColor: `rgba(${r},${g},${b},0.14)`,
    color: hex,
    border: `1px solid rgba(${r},${g},${b},0.42)`,
    fontSize: '0.7rem',
    fontWeight: '600',
  }
}

function syncFromDetail() {
  if (!detail.value) return
  editingFixedTotalAsset.value = null
  cashManualOverride.value = false
  localLinkedPortfolio.value = detail.value.linked_portfolio || ''
  localCash.value = detail.value.cash_balance || 0
  localHoldings.value = detail.value.holdings.filter(h => h.ticker !== 'CASH').map((h) => ({ ...h }))
}

function startEdit() {
  editingFixedTotalAsset.value = Number(totalAssetValue.value || 0)
  cashManualOverride.value = false
  isEditing.value = true
}

function resetCashAuto() {
  if (!Number.isFinite(Number(editingFixedTotalAsset.value))) return
  cashManualOverride.value = false
  localCash.value = Number(editingFixedTotalAsset.value) - Number(stockValueLive.value || 0)
}

async function load() {
  if (!accountId.value) return
  if (detailAbortController) {
    detailAbortController.abort()
  }
  detailAbortController = new AbortController()
  const reqId = ++detailReqId
  loading.value = true
  error.value = ''
  try {
    const { data } = await accountApi.getBalanceDetail(accountId.value, { signal: detailAbortController.signal })
    if (reqId !== detailReqId) return
    detail.value = data
    syncFromDetail()
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    if (reqId !== detailReqId) return
    error.value = getApiErrorMessage(e, '계좌 정보를 불러오지 못했습니다.')
  } finally {
    if (reqId !== detailReqId) return
    loading.value = false
  }
}

async function doPriceRefresh() {
  if (!accountId.value || !authStore.isAuthenticated || priceRefreshing.value) return
  priceRefreshing.value = true
  try {
    let refreshQueued = true
    try {
      const { data } = await accountApi.refreshBalances({ account_id: accountId.value })
      if (data?.queued === false) {
        refreshQueued = false
        emit('flash', data.message || '갱신 요청을 처리하지 못했습니다.', 'alert-warning')
      }
    } catch (e) {
      emit('flash', getApiErrorMessage(e, '현재가 갱신 요청에 실패했습니다.'), 'alert-danger')
      await load()
      return
    }
    await load()
    if (refreshQueued && detail.value?.is_stale) {
      const ok = await pollUntilBalanceDetailFresh({
        load,
        isStale: () => !!detail.value?.is_stale,
      })
      if (!ok) {
        emit('flash', '갱신이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.', 'alert-warning')
      }
    }
  } finally {
    priceRefreshing.value = false
  }
}

onMounted(() => {
  loadDashboardPrefs()
  loadHistory()
  chartThemeObserver = new MutationObserver(() => {
    chartThemeVersion.value += 1
  })
  chartThemeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme'],
  })
})

watch(accountId, load, { immediate: true })

watch(localLinkedPortfolio, async (newVal) => {
  if (!isEditing.value) return
  await syncPortfolioRatios()
})

watch(
  localHoldings,
  () => {
    if (!isEditing.value) return
    if (!Number.isFinite(Number(editingFixedTotalAsset.value))) return
    if (cashManualOverride.value) return
    localCash.value = Number(editingFixedTotalAsset.value) - Number(stockValueLive.value || 0)
  },
  { deep: true }
)

onBeforeUnmount(() => {
  detailAbortController?.abort()
  historyAbortController?.abort()
  priceAbortController?.abort()
  tickerSearchAbortController?.abort()
  chartThemeObserver?.disconnect()
})

async function syncPortfolioRatios() {
  if (!detail.value) return
  
  const pf = localLinkedPortfolio.value 
    ? detail.value.portfolios.find(p => p.id === localLinkedPortfolio.value)
    : null

  // Fetch latest prices for portfolio tickers if any
  let priceMap = {}
  if (pf && pf.items.length > 0) {
    if (priceAbortController) {
      priceAbortController.abort()
    }
    priceAbortController = new AbortController()
    const reqId = ++priceReqId
    try {
      const tickers = pf.items.map(i => i.ticker)
      const { data } = await stockApi.getTickerPrices(tickers, { signal: priceAbortController.signal })
      if (reqId !== priceReqId) return
      priceMap = data
    } catch (e) {
      if (e?.code === 'ERR_CANCELED') return
      console.warn('Failed to fetch prices for portfolio tickers:', e)
    }
  }

  // Create a new array based on current localHoldings to ensure reactivity
  const nextHoldings = localHoldings.value.map(h => {
    const pfItem = pf ? pf.items.find(i => i.ticker === h.ticker) : null
    const priceInfo = priceMap[h.ticker]
    return {
      ...h,
      target_ratio: pfItem ? (Number(pfItem.ratio) / 100) : 0,
      // Update price and name if we got fresh data
      price: priceInfo ? priceInfo.price : h.price,
      name: priceInfo ? priceInfo.name : h.name,
      prev_day_change: priceInfo ? priceInfo.prev_day_change : h.prev_day_change,
      prev_day_change_pct: priceInfo ? priceInfo.prev_day_change_pct : h.prev_day_change_pct,
    }
  })

  // Add missing tickers from portfolio
  if (pf) {
    pf.items.forEach(item => {
      if (!nextHoldings.find(h => h.ticker === item.ticker)) {
        const priceInfo = priceMap[item.ticker]
        nextHoldings.push({
          ticker: item.ticker,
          name: priceInfo ? priceInfo.name : (item.name || item.ticker),
          quantity: 0,
          price: priceInfo ? priceInfo.price : 0,
          prev_day_change: priceInfo ? priceInfo.prev_day_change : null,
          prev_day_change_pct: priceInfo ? priceInfo.prev_day_change_pct : null,
          value: 0,
          avg_purchase_price: 0,
          profit_loss: 0,
          return_rate: 0,
          target_ratio: Number(item.ratio) / 100.0,
          target_qty: 0,
          action: 'buy',
          diff_qty: 0,
          diff_amount: 0,
        })
      }
    })
  }

  localHoldings.value = nextHoldings
}


async function save() {
  if (!detail.value || savingEdit.value) return
  savingEdit.value = true
  const cashToSave = Math.max(0, Math.round(Number(localCash.value || 0)))
  // 저장 클릭 직후 UI도 서버 저장값(0 이상)과 즉시 동기화해
  // 응답 대기 중 음수 현금이 잠깐 보이는 현상을 방지한다.
  localCash.value = cashToSave
  const payload = {
    account_id: detail.value.account.id,
    linked_portfolio: localLinkedPortfolio.value || undefined,
    cash: cashToSave,
    tickers: localHoldings.value.map((h) => h.ticker),
    quantities: localHoldings.value.map((h) => String(h.quantity ?? 0)),
    avg_purchase_prices: localHoldings.value.map((h) => String(h.avg_purchase_price ?? 0)),
  }
  try {
    // 저장 중 계산 기준이 바뀌지 않도록 편집 모드를 먼저 종료한다.
    isEditing.value = false
    editingFixedTotalAsset.value = null
    cashManualOverride.value = false
    await accountApi.updateBalance(payload)
    emit('flash', '잔고 및 포트폴리오 설정이 저장되었습니다.', 'alert-success')
    await load()
    // 저장 시점에 balance_history(오늘)가 갱신되므로 차트도 즉시 재조회한다.
    await loadHistory()
  } catch (e) {
    // 실패 시 서버 원본으로 동기화
    await load()
    emit('flash', getApiErrorMessage(e, '저장 중 오류가 발생했습니다.'), 'alert-danger')
  } finally {
    savingEdit.value = false
  }
}

function cancelEdit() {
  isEditing.value = false
  editingFixedTotalAsset.value = null
  cashManualOverride.value = false
  syncFromDetail()
}

function removeHolding(idx) {
  if (!confirm('이 종목을 목록에서 제거하시겠습니까? (저장 시 반영됩니다)')) return
  localHoldings.value.splice(idx, 1)
}

function moveHolding(idx, delta) {
  const nextIdx = idx + delta
  if (idx < 0 || nextIdx < 0 || idx >= localHoldings.value.length || nextIdx >= localHoldings.value.length) return
  const next = [...localHoldings.value]
  const [item] = next.splice(idx, 1)
  next.splice(nextIdx, 0, item)
  localHoldings.value = next
}

async function doTickerSearch() {
  const q = tickerSearchQuery.value.trim()
  if (!q) return
  if (tickerSearchAbortController) {
    tickerSearchAbortController.abort()
  }
  tickerSearchAbortController = new AbortController()
  const reqId = ++tickerSearchReqId
  try {
    const { data } = await portfolioApi.searchTicker(q, { signal: tickerSearchAbortController.signal })
    if (reqId !== tickerSearchReqId) return
    tickerSearchResults.value = data
  } catch (e) {
    if (e?.code === 'ERR_CANCELED') return
    emit('flash', getApiErrorMessage(e, '종목 검색 중 오류가 발생했습니다.'), 'alert-danger')
  }
}

function addHoldingFromSearch(item) {
  if (localHoldings.value.some((h) => h.ticker === item.ticker)) {
    emit('flash', '이미 목록에 있는 종목입니다.', 'alert-warning')
    return
  }
  localHoldings.value.push({
    ticker: item.ticker,
    name: item.name,
    quantity: 0,
    price: item.current_price || 0,
    value: 0,
    avg_purchase_price: 0,
    profit_loss: 0,
    return_rate: 0,
    target_ratio: 0,
    target_qty: 0,
    action: 'buy',
    diff_qty: 0,
    diff_amount: 0,
  })
  tickerSearchResults.value = []
  tickerSearchQuery.value = ''
  const modalEl = document.getElementById('addTickerModal')
  if (modalEl) {
    const modal = window.bootstrap?.Modal?.getInstance(modalEl)
    if (modal) modal.hide()
  }
}

const withdrawalSimulation = computed(() => {
  if (!detail.value || withdrawalAmount.value <= 0) return null

  const W = Number(withdrawalAmount.value)
  
  // 1. Current Total Asset (Reactive calculation based on UI inputs)
  const currentTotalAsset = totalAssetValue.value
  const targetTotalAsset = currentTotalAsset - W
  
  if (targetTotalAsset < 0) return null

  // 2. Resolve Active Portfolio Ratios (Reactive to selection)
  const activePortfolio = detail.value.portfolios.find(p => p.id === localLinkedPortfolio.value)
  const portfolioRatios = {}
  if (activePortfolio) {
    activePortfolio.items.forEach(item => {
      portfolioRatios[item.ticker] = Number(item.ratio) / 100
    })
  }

  // 3. Source Breakdown (Using principal as baseline)
  const principal = Number(detail.value.principal || 0)
  const currentInvestmentReturn = currentTotalAsset - principal
  const profit = Math.max(0, currentInvestmentReturn)
  const profitSource = Math.min(W, profit)
  const principalSource = W - profitSource

  // 4. Calculate Trades (Full Rebalancing)
  const tradeList = localHoldings.value.map((h) => {
    const targetRatio = portfolioRatios[h.ticker] || 0
    const targetValue = targetTotalAsset * targetRatio
    const currentValue = Number(h.quantity || 0) * Number(h.price || 0)
    const requiredChangeAmount = currentValue - targetValue
    const suggestedQty = h.price > 0 ? Math.round(requiredChangeAmount / h.price) : 0
    
    return {
      ticker: h.ticker,
      name: h.name,
      price: h.price,
      quantity: Math.abs(suggestedQty),
      amount: Math.abs(suggestedQty) * h.price,
      action: suggestedQty > 0 ? 'sell' : suggestedQty < 0 ? 'buy' : 'hold'
    }
  }).filter((t) => t.action !== 'hold')

  return {
    profitSource,
    principalSource,
    tradeList,
    netCashOut: tradeList.reduce((sum, t) => sum + (t.action === 'sell' ? t.amount : -t.amount), 0),
    requestedAmount: W
  }
})
</script>

<style scoped>
.balance-page-title {
  color: var(--ui-text);
}
.balance-detail-summary {
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
}
/* md 미만(모바일)은 위아래로 쌓이므로 구분선이 필요 없다 — 좌우로 나란히 서는 md 이상에서만 표시 */
@media (min-width: 768px) {
  .balance-prevday-col {
    border-left: 1px solid var(--ui-border);
  }
}
.balance-detail-pill {
  font-size: 0.65rem;
  font-weight: 800;
  letter-spacing: 0.05em;
}
/* 목표 비중 대비 상대 이격도 — 평소엔 은은하게, 리밸런싱이 필요할 만큼 벌어지면 경고색으로 */
.balance-relative-deviation {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--ui-text-muted);
}
.balance-relative-deviation--warn {
  color: var(--ui-alert-warning-text);
}
.balance-detail-icon-ring {
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}
.balance-detail-icon-ring--account {
  width: 3.25rem;
  height: 3.25rem;
  flex-shrink: 0;
}

.text-profit { color: var(--ui-up) !important; font-weight: 600; }
.text-loss { color: var(--ui-down) !important; font-weight: 600; }
:global([data-theme="dark"]) .text-profit { color: #fb7185 !important; }
:global([data-theme="dark"]) .text-loss { color: #60a5fa !important; }

.text-danger.fw-bold { color: var(--ui-up) !important; }
.text-primary.fw-bold { color: var(--ui-down) !important; }
.hover-danger:hover { color: var(--ui-up) !important; }
.text-xs { font-size: 0.7rem; }

.chart-header {
  background: var(--ui-surface-soft) !important;
}

.chart-body {
  background: var(--ui-surface) !important;
  display: flex;
  flex-direction: column;
}

.chart-canvas-wrap {
  position: relative;
  height: 340px;
  min-height: 340px;
}

.chart-empty-state {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.period-btn {
  min-width: 56px;
}

.chart-toggle-group {
  gap: 0.4rem;
}

.chart-toggle-btn {
  min-height: var(--ui-btn-height-sm);
  padding: 0.25rem 0.65rem;
  font-weight: 600;
  border-radius: var(--ui-btn-radius);
  border: 1px solid var(--ui-border-strong);
  background: var(--ui-surface);
  color: var(--ui-text-subtle);
  box-shadow: none;
}

.chart-toggle-btn:hover {
  background: var(--ui-surface-soft);
  border-color: var(--ui-border-strong);
  color: var(--ui-text);
}

.chart-toggle-btn.is-active.active-profit {
  background: var(--ui-alert-danger-bg);
  border-color: var(--ui-alert-danger-border);
  color: var(--ui-alert-danger-text);
}

.chart-toggle-btn.is-active.active-roi {
  background: var(--ui-alert-info-bg);
  border-color: var(--ui-alert-info-border);
  color: var(--ui-alert-info-text);
}

.top-action-buttons {
  gap: 0.5rem;
}

@media (max-width: 767.98px) {
  .chart-canvas-wrap {
    height: 300px;
    min-height: 300px;
  }

  .top-action-buttons {
    width: 100%;
  }

  .top-action-buttons .btn {
    flex: 1 1 calc(50% - 0.5rem);
    justify-content: center;
  }
}
.border-soft { border-color: rgba(0,0,0,0.06) !important; }
:global([data-theme="dark"]) .border-soft { border-color: rgba(255,255,255,0.08) !important; }
</style>
