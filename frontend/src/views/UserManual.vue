<template>
  <section class="user-manual-page py-3 py-md-4">
    <div class="container-narrow">
      <div class="card border-0 shadow-sm mb-4">
        <div class="card-body p-4 p-md-5">
          <div class="d-flex align-items-center gap-3 mb-4">
            <div class="icon-box bg-primary-soft text-primary rounded-3 p-2">
              <MaterialIcon name="menu_book" size="2rem" />
            </div>
            <div>
              <h1 class="h3 mb-1 fw-bold">사용자 매뉴얼</h1>
              <p class="text-muted mb-0">주식 관리 시스템의 주요 기능과 사용 방법을 안내합니다.</p>
            </div>
          </div>

          <hr class="my-4 opacity-10">

          <!-- 1. 사이트 목적과 장점 -->
          <section class="manual-section mb-5">
            <h2 class="h4 mb-3 d-flex align-items-center gap-2">
              <span class="section-number">1</span>
              사이트의 목적과 장점
            </h2>
            <div class="manual-content">
              <p>본 시스템은 여러 증권사에 분산된 개인 투자자의 자산을 하나의 화면에서 통합 관리하고, 전략적인 자산 배분을 돕기 위해 설계되었습니다.</p>
              <div class="row g-3 mt-2">
                <div class="col-md-6">
                  <div class="advantage-card p-3 rounded-3 border h-100">
                    <h3 class="h6 fw-bold mb-2">통합 자산 관리</h3>
                    <p class="small text-muted mb-0">KOSPI/KOSDAQ 실시간 지수와 연동하여 모든 계좌의 손익 현황을 실시간으로 파악할 수 있습니다.</p>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="advantage-card p-3 rounded-3 border h-100">
                    <h3 class="h6 fw-bold mb-2">데이터 시각화</h3>
                    <p class="small text-muted mb-0">자산 구성비, 수익률 추이 등을 직관적인 차트로 제공하여 포트폴리오의 건강 상태를 한눈에 보여줍니다.</p>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="advantage-card p-3 rounded-3 border h-100">
                    <h3 class="h6 fw-bold mb-2">리밸런싱 지원</h3>
                    <p class="small text-muted mb-0">목표 포트폴리오 비중과 현재 보유 비중을 비교하여 최적의 매수/매도 수량을 자동으로 계산해줍니다.</p>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="advantage-card p-3 rounded-3 border h-100">
                    <h3 class="h6 fw-bold mb-2">개인화된 대시보드</h3>
                    <p class="small text-muted mb-0">사용자가 선호하는 뷰 모드(카드형, 리스트형)와 다크 모드 등을 지원하여 최적의 사용 경험을 제공합니다.</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <!-- 2. 주요 메뉴 설명 -->
          <section class="manual-section mb-5">
            <h2 class="h4 mb-4 d-flex align-items-center gap-2">
              <span class="section-number">2</span>
              주요 메뉴 설명 및 사용 가이드
            </h2>

            <!-- 대시보드 -->
            <div class="menu-guide mb-5 p-3 p-md-4 bg-light-soft rounded-4 border">
              <div class="d-flex align-items-center gap-3 mb-3">
                <div class="icon-circle bg-primary text-white shadow-sm">
                  <MaterialIcon name="dashboard" size="1.25rem" />
                </div>
                <h3 class="h5 mb-0 fw-bold">대시보드 (Dashboard)</h3>
              </div>
              <p class="text-secondary small">시스템 접속 시 첫 화면으로, 분산된 모든 자산의 지수, 합계, 비중을 통합하여 요약해 보여줍니다.</p>
              
              <div class="mockup-container my-4 rounded-4 overflow-hidden border shadow-sm">
                <img src="/img/manual/dashboard.png" alt="대시보드 화면" class="img-fluid">
                <div class="p-2 bg-dark text-white text-center small opacity-75">통합 자산 현황 대시보드</div>
              </div>

              <ul class="manual-list mt-3">
                <li><strong>시장 지수:</strong> 상단에서 KOSPI, KOSDAQ 실시간 지수와 등락을 즉시 확인합니다.</li>
                <li><strong>총 자산 요약:</strong> 모든 계좌를 합산한 평가 금액, 누적 수익금, 당일 수익을 파악합니다.</li>
                <li><strong>자산 배분 차트:</strong> 카네고리별 비중을 시각화하여 포트폴리오 밸런스를 점검하세요.</li>
              </ul>
            </div>

            <!-- 계좌 잔고 -->
            <div class="menu-guide mb-5 p-3 p-md-4 bg-light-soft rounded-4 border">
              <div class="d-flex align-items-center gap-3 mb-3">
                <div class="icon-circle bg-success text-white shadow-sm">
                  <MaterialIcon name="account_balance_wallet" size="1.25rem" />
                </div>
                <h3 class="h5 mb-0 fw-bold">계좌 잔고 (Balances)</h3>
              </div>
              <p class="text-secondary small">개별 계좌에 속한 종목들의 평단가, 수량, 현재가 및 평가 손익을 상세히 관리합니다.</p>

              <div class="mockup-container my-4 rounded-4 overflow-hidden border shadow-sm">
                <img src="/img/manual/balances.png" alt="계좌 잔고 상세 화면" class="img-fluid">
                <div class="p-2 bg-dark text-white text-center small opacity-75">개별 계좌 및 종목 상세 현황</div>
              </div>

              <ul class="manual-list mt-3">
                <li><strong>계좌별 요약:</strong> 각 계좌의 현재 자산 가치와 원금 대비 수익률을 확인합니다.</li>
                <li><strong>종목별 수익 분석:</strong> 계좌 내 개별 종목의 실시간 수익 현황을 직관적으로 확인하세요.</li>
                <li><strong>자산 추이 조회:</strong> '조회' 버튼을 통해 날짜별 자산 변화를 그래프로 추적할 수 있습니다.</li>
              </ul>
            </div>

            <!-- 포트폴리오 관리 -->
            <div class="menu-guide mb-5 p-3 p-md-4 bg-light-soft rounded-4 border">
              <div class="d-flex align-items-center gap-3 mb-3">
                <div class="icon-circle bg-info text-white shadow-sm">
                  <MaterialIcon name="pie_chart" size="1.25rem" />
                </div>
                <h3 class="h5 mb-0 fw-bold">포트폴리오 관리 (Portfolios)</h3>
              </div>
              <p class="text-secondary small">자산 배분 전략을 수립하고, 목표 비중과의 차이를 리밸런싱하는 전문 도구입니다.</p>

              <ul class="manual-list mt-3">
                <li><strong>목표 비중 설정:</strong> 본인의 성향에 맞게 주식, 채권, 현금 등의 비중을 % 단위로 설정합니다.</li>
                <li><strong>리밸런싱 계산:</strong> 현재 실제 보유 비중을 목표에 맞추기 위해 사고팔아야 할 수량을 자동 계산합니다.</li>
                <li><strong>매수/매도 수량 가이드:</strong> 계좌 상세에서 각 종목별로 '몇 주'를 더 사고팔아야 하는지 확인하세요.</li>
              </ul>
            </div>

            <!-- 설정 -->
            <div class="menu-guide p-3 p-md-4 bg-light-soft rounded-4 border">
              <div class="d-flex align-items-center gap-3 mb-3">
                <div class="icon-circle bg-dark text-white shadow-sm">
                  <MaterialIcon name="settings" size="1.25rem" />
                </div>
                <h3 class="h5 mb-0 fw-bold">계좌 관리 및 설정 (Settings)</h3>
              </div>
              <p class="text-secondary small">증권사 계좌를 등록하고 대시보드 노출 여부 등 환경을 설정합니다.</p>

              <div class="mockup-container my-4 rounded-4 overflow-hidden border shadow-sm">
                <img src="/img/manual/settings.png" alt="계좌 관리 화면" class="img-fluid">
                <div class="p-2 bg-dark text-white text-center small opacity-75">등록 계좌 편집 및 관리</div>
              </div>

              <ul class="manual-list mt-3">
                <li><strong>계좌 추가/삭제:</strong> 신규 계좌를 등록하거나 필요 없는 계좌를 제거합니다.</li>
                <li><strong>노출 설정:</strong> 토글 버튼으로 대시보드에 표시할 계좌를 직접 선택하세요.</li>
                <li><strong>그룹 테마:</strong> 계좌 그룹별로 고유 색상을 지정해 시각적 구분이 가능합니다.</li>
              </ul>
            </div>
          </section>

          <div class="alert alert-info border-0 rounded-4 d-flex gap-3 align-items-start p-3 p-md-4">
            <MaterialIcon name="tips_and_updates" size="1.5rem" />
            <div>
              <h4 class="h6 fw-bold mb-1">사용 팁!</h4>
              <p class="small mb-0 opacity-75">우측 상단의 <strong>테마 전환 버튼</strong>을 통해 눈이 편안한 다크 모드와 화사한 라이트 모드를 자유롭게 오갈 수 있습니다.</p>
            </div>
          </div>
        </div>
      </div>

      <div class="text-center">
        <router-link to="/site-guide" class="btn btn-outline-primary px-4 rounded-pill">
          <MaterialIcon name="arrow_back" size="1rem" class="me-1" />
          사이트 안내로 돌아가기
        </router-link>
      </div>
    </div>
  </section>
</template>

<script setup>
import MaterialIcon from '../components/MaterialIcon.vue'
</script>

<style scoped>
.user-manual-page {
  background: var(--ui-surface);
  min-height: 100vh;
}

.container-narrow {
  max-width: 800px;
  margin: 0 auto;
}

.section-number {
  background: var(--ui-primary);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  font-weight: 700;
}

.icon-circle {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.advantage-card {
  background: var(--ui-surface-soft);
  border-color: var(--ui-border) !important;
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.advantage-card:hover {
  transform: translateY(-2px);
  border-color: var(--ui-primary) !important;
}

.manual-list {
  padding-left: 1.25rem;
  margin-bottom: 0;
}

.manual-list li {
  margin-bottom: 0.5rem;
  font-size: 0.95rem;
  color: var(--ui-text-muted);
}

.manual-list li strong {
  color: var(--ui-text);
}

.bg-light-soft {
  background: var(--ui-surface-soft);
}

.mockup-container img {
  width: 100%;
  height: auto;
  display: block;
}

.icon-box {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
