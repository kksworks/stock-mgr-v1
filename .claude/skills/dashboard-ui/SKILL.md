# Skill: Stock Portfolio Dashboard UI

## 목적
주식 계좌 잔고 및 포트폴리오 관리 웹 서비스(stock-manage-flask)의 화면, 데이터 표현, 반응형 UI를 이 프로젝트의 기존 디자인 시스템(Bootstrap 5 + `frontend/src/style.css` CSS 변수)에 맞춰 안정적으로 설계·구현한다.

---

## 입력 목표
이 스킬은 다음 작업에 사용한다.
- 계좌 잔고 요약/상세 화면 설계 (`BalanceList`, `BalanceDetail`, `BalanceHistoryDetail`)
- 포트폴리오 구성 화면 설계 (`PortfolioManager`, `PortfolioDetail`)
- 종목별 평가손익 및 수익률 표현
- 금융 데이터 차트 구성
- 모바일/PC 반응형 화면 구현
- 한국어 UI 최적화
- 라이트/다크 테마 동시 지원
- Flask + MongoDB + Vue 3 + Bootstrap 5 기반 기능 설계

---

## 핵심 실행 원칙

### 1. 한국어 우선
- 모든 화면 문구는 한국어로 작성한다.
- 금융 용어는 프로젝트 루트 `AGENT.md`의 3.1 용어 기준을 따른다 (평가금액, 평가손익, 매수금액, 평균단가, 수익률 등).
- 텍스트 길이를 고려해 짧고 명확하게 표시한다.

### 2. 한글 줄바꿈 안정성
- 모든 텍스트 컨테이너에 한글 분리 방지 스타일을 적용한다.
- 필수 스타일:
  - `word-break: keep-all;`
  - `overflow-wrap: break-word;`
  - `line-break: strict;`
- 카드, 버튼, 탭, 테이블 헤더는 한글 길이를 고려한다.

### 3. 반응형 정보 전략
- 모바일:
  - 핵심 요약만 노출
  - 총자산, 평가손익, 수익률, Top 보유종목, 당일 변동
- PC:
  - 상세 차트, 섹터 분석, 종목별 테이블, 거래 내역, 기간별 추이
- 화면 크기에 따라 정보 우선순위를 조정한다.

### 4. 시각 디자인 — 기존 디자인 시스템을 따른다
- 새 색상/스타일을 즉흥적으로 정의하지 말고, 반드시 `frontend/src/style.css`의 `:root` CSS 변수를 재사용한다.
- 베이스는 Bootstrap 5 유틸리티 클래스이며, 그 위에 프로젝트 전용 플랫/매트 테마 변수가 얹혀 있다.
- 배경/서피스: `--ui-bg`, `--ui-surface`, `--ui-surface-soft`
- 브랜드 액센트는 **파인 그린**이다: `--ui-primary` (`#1f6f54`), 링크/포커스링도 이 색을 기준으로 파생한다 (`--ui-link`, `--ui-focus-ring`).
- 카드·섹션은 평면적이어야 한다. 과한 그림자(`--ui-shadow`는 이미 최소값으로 정의돼 있음), 장식적 그라데이션을 추가하지 않는다.
- **다크모드는 선택이 아니라 필수다.** 이 프로젝트는 `:root[data-theme="dark"]` 오버라이드로 다크모드를 지원한다(`style.css` 86번째 줄 이하 다수). 새 컴포넌트나 색상을 추가하면 반드시 동일한 셀렉터 패턴으로 다크 대응 값을 함께 정의한다. 색상을 하드코딩(`#fff`, `rgb(...)` 등)하지 말고 CSS 변수를 통해서만 참조한다.

### 5. 금융 표현 규칙
- 상승/이익 → 레드: `var(--ui-up)` (`#dc2626`)
- 하락/손실 → 블루: `var(--ui-down)` (`#2563eb`)
- 보합 → 그레이 계열 (`--ui-text-muted`)
- 금액은 천 단위 콤마 표기 (`1,250,000원`)
- 수익률은 부호와 소수점 둘째 자리까지 표기 (`+12.45%`, `-3.10%`)
- 숫자는 본문과 동일한 한글 폰트(`var(--ui-num-font)`, Noto Sans KR)를 쓰고 `font-variant-numeric: tabular-nums;`로 자릿수 정렬만 맞춘다. 코드용 모노스페이스 폰트(JetBrains Mono 등)는 한글 글리프가 없어 "억"/"만원" 같은 단위가 섞이면 다른 폰트로 깨져 보이므로 숫자·금액 표시에 쓰지 않는다. Chart.js/canvas 라벨처럼 `var()`를 못 쓰는 곳은 `"Noto Sans KR", sans-serif`를 직접 명시한다.

### 6. 분류(카테고리) 색상 팔레트
- 일반 UI(뱃지, 카드 테두리 등)에서 자산군/섹터를 구분할 때는 `frontend/src/style.css`의 `--color-category-1` ~ `--color-category-8` 톤온톤 팔레트를 순서대로 사용한다 (예: `#2f6f5e` Pine, `#a8763a` Brass, `#4a5d8a` Slate Indigo …). `BalanceList.vue`/`BalanceDetail.vue`가 이 팔레트를 쓴다.
- **예외 — 대시보드 차트**: `MainDashboard.vue`는 여러 분류를 동시에 비교하는 도넛/막대/라인 차트가 많아, 위 톤온톤 팔레트 대신 더 채도 높은 자체 팔레트(`--dash-cat-1` ~ `-8`, scoped style)를 의도적으로 사용한다 — 톤온톤 색은 차분하지만 여러 계열을 한 차트에서 구분하기 어렵기 때문이다. 이 팔레트는 카드 좌측 라인, 라인차트, 막대차트에서 항상 같은 순서로 매핑되어 그 안에서는 일관성을 유지한다. 새 화면을 만들 때 두 팔레트를 섞어 쓰지 말고, 어느 화면의 패턴을 따르는지 먼저 확인한다.
- 임의의 새 색상을 즉석에서 추가하지 말고, 팔레트가 부족하면 해당 화면이 따르는 팔레트의 톤(전자는 저채도 톤온톤, 후자는 고채도 구분색)에 맞춰 확장한다.

---

## 구현 체크리스트
- [ ] 모바일에서 핵심 정보만 보이는가
- [ ] PC에서 상세 정보가 확장되는가
- [ ] 한글이 줄바꿈 때문에 깨지지 않는가
- [ ] 표가 작은 화면에서 무너지지 않는가
- [ ] 차트가 금융 데이터에 적합한가
- [ ] 색상 규칙(상승=레드/하락=블루)이 일관적인가
- [ ] 숫자 표기(콤마, 소수점 둘째 자리, tabular-nums)가 표준화되어 있는가
- [ ] 새 색상을 하드코딩하지 않고 기존 `--ui-*` / `--color-category-*` 변수를 재사용했는가
- [ ] `:root[data-theme="dark"]` 오버라이드를 함께 작성했는가 (라이트에서만 확인하고 끝내지 않기)
- [ ] Bootstrap 5 유틸리티 클래스와 커스텀 변수가 충돌하지 않는가
- [ ] 전체 UI가 평면적이고 단순한가

---

## 실제 화면/컴포넌트 구조 (권장 사항이 아니라 기존 패턴)
이 프로젝트는 원자적 UI 컴포넌트 라이브러리가 아니라 **페이지 단위 View**로 구성되어 있다. 새 화면을 만들 때는 아래 기존 패턴을 따른다.

- `frontend/src/views/` — 라우트에 매핑되는 페이지 단위 컴포넌트
  - 잔고: `BalanceList`, `BalanceDetail`, `BalanceHistoryDetail`
  - 포트폴리오: `PortfolioManager`, `PortfolioDetail`
  - 계좌: `AccountManager`, `AccountDetail`, `MyAccount`
  - 대시보드/시세: `MainDashboard`, `StockDashboard`
  - 관리자 전용: `MemberManagement`, `ScheduleSettings`, `LogViewer`
  - 기타: `TransactionManager`, `BoardDetail`, `SiteGuide`, `UserManual`, `Login`, `Register`
- `frontend/src/components/` — 여러 View에서 재사용되는 작은 조각만 여기 둔다 (예: `MaterialIcon`, `PageLoadingPlaceholder`). 화면 하나에서만 쓰이는 요소를 굳이 이 폴더로 분리하지 않는다.
- 새 재사용 요소가 필요하면 이 폴더의 기존 이름 규칙(역할이 드러나는 PascalCase)을 따른다. "AccountSummary/ProfitBadge" 같은 이름을 임의로 새로 만들기 전에 비슷한 기존 컴포넌트가 있는지 먼저 확인한다.

## 권장 데이터 구조
- `backend/account.py`, `backend/stock.py`, `backend/account_monthly_trend.py`, `backend/services.py`에 이미 구현된 개념을 재사용한다: Account, Holding/Portfolio, Transaction(입출금), PriceHistory, PerformanceSnapshot(월별 추이), AssetAllocation.
- 새 컬렉션/필드를 추가하기 전에 `backend/database.py`와 `backend/routes/`의 기존 스키마를 먼저 확인한다.

---

## 금지 사항
- 과도한 그라데이션 사용 금지
- 과한 그림자 금지
- 한글 줄바꿈 방치 금지
- 모바일에서 과도한 정보 노출 금지
- 수익률 색상 혼용 금지 (상승=레드/하락=블루 고정)
- 숫자 포맷 혼용 금지
- 색상 하드코딩 금지 — 반드시 `--ui-*` / `--color-category-*` CSS 변수 사용
- 다크모드(`:root[data-theme="dark"]`) 대응 누락 금지
