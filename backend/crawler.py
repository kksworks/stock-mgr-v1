import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Any, Dict, Optional

import pandas as pd
from pykrx import stock
from pymongo import UpdateOne
import requests
import time
from urllib.parse import quote
from backend import config_loader
from backend.time_utils import now_kst, ensure_kst_from_utc_naive

# Pandas FutureWarning 해결: 다운캐스팅 동작 변경 승인
pd.set_option('future.no_silent_downcasting', True)

_config = config_loader.load_config()

def fetch_tickers(collection):
    """pykrx의 내부 Finder API를 사용하여 전종목 티커와 종목명을 효율적으로 조회."""
    logging.info("티커 크롤링 시작 (pykrx Finder API)")
    
    try:
        from pykrx.website.krx.market.core import 상장종목검색
        import pykrx.website.comm.webio as webio
        
        # KRX의 세션 및 User-Agent 체크를 우회하기 위한 로컬 패치
        _session = requests.Session()
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        
        def patched_post_read(self, **params):
            if not _session.cookies:
                try:
                    _session.get("https://data.krx.co.kr/contents/MDC/MDI/outerLoader/index.cmd", timeout=10)
                except Exception as ex:
                    logging.warning(f"쿠키 획득 실패 (무시하고 진행): {ex}")
            h = self.headers.copy()
            h.update({"User-Agent": ua, "X-Requested-With": "XMLHttpRequest"})
            return _session.post(self.url, headers=h, data=params, timeout=10)

        # 기존 Post.read 메서드를 백업하고 패치
        old_post_read = webio.Post.read
        webio.Post.read = patched_post_read
        
        try:
            finder = 상장종목검색()
            df = finder.fetch(mktsel="ALL")
        finally:
            # 다른 모듈에 영향을 주지 않도록 패치 원복
            webio.Post.read = old_post_read

        if df is None or df.empty:
            logging.error("티커 정보를 가져오지 못했습니다. (Empty DataFrame)")
            return 0
            
        now = now_kst()
        operations = []
        for _, row in df.iterrows():
            ticker = row.get('short_code')
            name = row.get('codeName')
            if ticker and name:
                operations.append(UpdateOne(
                    {"ticker": ticker},
                    {"$set": {
                        "name": name,
                        "last_updated": now
                    }},
                    upsert=True
                ))
        
        if operations:
            collection.bulk_write(operations)
            count = len(operations)
            logging.info(f"티커 크롤링 완료. 총 {count}개 종목 업데이트됨.")
            return count
            
    except Exception as e:
        logging.error(f"티커 크롤링 중 치명적 오류 발생: {e}")
        
    return 0


# 네이버 동시 요청 수/타임아웃/딜레이는 config.ini로 튜닝 가능
_FETCH_PRICE_MAX_WORKERS = max(1, config_loader.get_int(_config, 'performance', 'fetch_price_max_workers', 1))
_FETCH_PRICE_BATCH_TIMEOUT_SEC = max(5, config_loader.get_int(_config, 'performance', 'fetch_price_batch_timeout_sec', 30))
_FETCH_PRICE_TASK_TIMEOUT_SEC = max(1, config_loader.get_int(_config, 'performance', 'fetch_price_task_timeout_sec', 5))
_FETCH_PRICE_DELAY_SEC = max(0.0, config_loader.get_float(_config, 'performance', 'fetch_price_inter_task_delay_sec', 0.05))
_FETCH_PRICE_REQUEST_TIMEOUT_SEC = max(1, config_loader.get_int(_config, 'performance', 'fetch_price_request_timeout_sec', 3))
_FETCH_PRICE_INFLIGHT_TTL_SEC = max(1, config_loader.get_int(_config, 'performance', 'fetch_price_inflight_ttl_sec', 5))
_FETCH_PRICE_INFLIGHT_WAIT_SEC = max(1, config_loader.get_int(_config, 'performance', 'fetch_price_inflight_wait_sec', 8))
_FETCH_PRICE_MAX_BATCH_SIZE = max(10, config_loader.get_int(_config, 'performance', 'fetch_price_max_batch_size', 50))
_FETCH_PRICE_VERBOSE_LOGS = config_loader.get_bool(_config, 'performance', 'fetch_price_verbose_logs', False)

_THREAD_LOCAL = threading.local()
_INFLIGHT_LOCK = threading.Lock()
_INFLIGHT_EVENTS: Dict[str, threading.Event] = {}
_RECENT_FETCH_CACHE: Dict[str, tuple] = {}


def _empty_quote() -> Dict[str, Any]:
    return {'price': 0, 'prev_day_change': None, 'prev_day_change_pct': None}


def _doc_to_quote(doc: Optional[dict]) -> Dict[str, Any]:
    if not doc:
        return _empty_quote()
    price_val = doc.get('current_price') or 0
    return {
        'price': float(price_val) if isinstance(price_val, float) else int(price_val),
        'prev_day_change': doc.get('prev_day_change'),
        'prev_day_change_pct': doc.get('prev_day_change_pct'),
    }


_NAVER_STOCK_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
)


def _naver_api_headers(referer: str, *, origin: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "User-Agent": _NAVER_STOCK_UA,
        "Accept": "*/*",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Referer": referer,
    }
    if origin:
        headers["Origin"] = origin
    return headers


def _parse_naver_number(value: Any) -> Optional[float]:
    """'6,649.28', '-35.09', 26186.41 등 Naver API 숫자 필드를 float으로 변환."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "").replace("%", "")
    if not text or text in ("-", "—"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _quote_from_price_change(price: Optional[float], change: Optional[float], pct: Optional[float], *, as_int: bool = False) -> Dict[str, Any]:
    if price is None or price <= 0:
        return _empty_quote()
    out_price: Any = int(round(price)) if as_int else float(price)
    out_change: Any = None
    if change is not None:
        out_change = int(round(change)) if as_int else float(change)
    return {
        "price": out_price,
        "prev_day_change": out_change,
        "prev_day_change_pct": float(pct) if pct is not None else None,
    }


def _get_http_session():
    # 스레드별 Session 재사용으로 TCP/TLS 재협상 비용을 줄여 CPU/지연을 절감.
    session = getattr(_THREAD_LOCAL, "session", None)
    if session is None:
        session = requests.Session()
        _THREAD_LOCAL.session = session
    return session


def _naver_get_json(url: str, headers: Dict[str, str]) -> Optional[dict]:
    session = _get_http_session()
    response = session.get(url, headers=headers, timeout=_FETCH_PRICE_REQUEST_TIMEOUT_SEC)
    response.raise_for_status()
    data = response.json()
    return data if isinstance(data, dict) else None


def _get_recent_quote(ticker):
    now = time.time()
    with _INFLIGHT_LOCK:
        row = _RECENT_FETCH_CACHE.get(ticker)
        if not row:
            return None
        quote, ts = row
        if (now - ts) > _FETCH_PRICE_INFLIGHT_TTL_SEC:
            _RECENT_FETCH_CACHE.pop(ticker, None)
            return None
        return quote


def _set_recent_quote(ticker, quote: Dict[str, Any]):
    with _INFLIGHT_LOCK:
        _RECENT_FETCH_CACHE[ticker] = (quote, time.time())


def _chunked(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def update_stale_prices(collection, tickers, threshold_minutes=10):
    """
    지정된 종목들 중 가격이 threshold_minutes보다 오래된 것만 크롤링하여 DB를 업데이트합니다.
    벌크 쓰기 및 인플라이트(중복 요청 방지) 보호 적용.
    """
    tickers = list(set(tickers))
    if not tickers:
        return {}

    now = now_kst()
    threshold = pd.Timedelta(minutes=threshold_minutes)
    results: Dict[str, Dict[str, Any]] = {}

    # 1. DB에서 현재 상태 벌크 조회
    cursor = collection.find(
        {"ticker": {"$in": tickers}},
        {"ticker": 1, "current_price": 1, "price_updated_at": 1, "prev_day_change": 1, "prev_day_change_pct": 1},
    )
    db_data = {doc["ticker"]: doc for doc in cursor}

    stale_tickers = []
    for t in tickers:
        doc = db_data.get(t)
        is_stale = True
        if doc and "price_updated_at" in doc and doc["price_updated_at"]:
            if (now - ensure_kst_from_utc_naive(doc["price_updated_at"])) < threshold:
                is_stale = False
        
        if is_stale:
            stale_tickers.append(t)
        elif doc:
            results[t] = _doc_to_quote(doc)
        else:
            # DB에도 없고 정체도 모르는 경우 일단 크롤링 대상
            stale_tickers.append(t)

    if not stale_tickers:
        return results

    # 2. 크롤링 수행 (중복 방지 로직 포함)
    to_fetch = []
    to_wait = []
    for t in stale_tickers:
        recent = _get_recent_quote(t)
        if recent is not None:
            results[t] = recent
            continue
            
        with _INFLIGHT_LOCK:
            ev = _INFLIGHT_EVENTS.get(t)
            if ev is None:
                ev = threading.Event()
                _INFLIGHT_EVENTS[t] = ev
                to_fetch.append(t)
            else:
                to_wait.append((t, ev))

    try:
        fetched = {}
        if to_fetch:
            logging.info(f"Crawling {len(to_fetch)} stale tickers (BatchSize={_FETCH_PRICE_MAX_BATCH_SIZE})")
            for chunk in _chunked(to_fetch, _FETCH_PRICE_MAX_BATCH_SIZE):
                fetched.update(fetch_stock_prices_parallel(chunk))

        # 3. DB 벌크 업데이트
        operations = []
        for t, q in fetched.items():
            price = q.get("price", 0)
            if price > 0:
                set_doc = {
                    "current_price": price,
                    "price_updated_at": now,
                    "prev_day_change": q.get("prev_day_change"),
                    "prev_day_change_pct": q.get("prev_day_change_pct"),
                }
                operations.append(UpdateOne({"ticker": t}, {"$set": set_doc}, upsert=True))
                results[t] = q
                _set_recent_quote(t, q)
            else:
                # 실패 시 DB 값으로 폴백
                results[t] = _doc_to_quote(db_data.get(t))

        if operations:
            collection.bulk_write(operations, ordered=False)

        # 4. 다른 스레드에서 대기 중인 항목 처리
        for t, ev in to_wait:
            if ev.wait(timeout=_FETCH_PRICE_INFLIGHT_WAIT_SEC):
                results[t] = _get_recent_quote(t) or _doc_to_quote(db_data.get(t))
            else:
                results[t] = _doc_to_quote(db_data.get(t))
    finally:
        with _INFLIGHT_LOCK:
            for t in to_fetch:
                ev = _INFLIGHT_EVENTS.pop(t, None)
                if ev: ev.set()

    return results


def fetch_hot_tickers(account_collection, balance_collection, ticker_collection, threshold_minutes=15):
    """
    최근 활동(예: 15분 내 조회)이 있는 계좌의 보유 종목들만 우선적으로 갱신합니다.
    (스케줄러나 대량 갱신 시 리소스 절약용)
    """
    now = now_kst()
    active_threshold = now - pd.Timedelta(minutes=30) # 최근 30분 내 갱신 시도된 계좌 대상
    
    # 최근 갱신된(또는 조회된) 계좌들 추출
    active_balances = balance_collection.find(
        {"last_calculated_at": {"$gte": active_threshold}},
        {"latest.holdings.ticker": 1}
    )
    
    hot_tickers = set()
    for b in active_balances:
        holdings = b.get('latest', {}).get('holdings', [])
        for h in holdings:
            t = h.get('ticker')
            if t and t != 'CASH':
                hot_tickers.add(t)
                
    if not hot_tickers:
        return 0
        
    res = update_stale_prices(ticker_collection, list(hot_tickers), threshold_minutes=threshold_minutes)
    return len(res)


def fetch_stock_prices_parallel(tickers, max_workers=None):
    """여러 종목 현재가·전일대비를 병렬(스레드)로 크롤링합니다. ticker -> quote dict."""
    tickers = list(tickers)
    if not tickers:
        return {}
    n = len(tickers)
    workers = min(max_workers or _FETCH_PRICE_MAX_WORKERS, n)
    logging.info(f"Starting parallel crawl for {n} tickers with {workers} workers.")

    out = {}
    consecutive_errors = 0
    max_consecutive_errors = max(2, workers)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(fetch_stock_quote, t): t for t in tickers}
        try:
            for fut in as_completed(future_map, timeout=_FETCH_PRICE_BATCH_TIMEOUT_SEC):
                if _FETCH_PRICE_DELAY_SEC > 0:
                    time.sleep(_FETCH_PRICE_DELAY_SEC)
                t = future_map[fut]
                try:
                    q = fut.result(timeout=_FETCH_PRICE_TASK_TIMEOUT_SEC)
                    out[t] = q if isinstance(q, dict) else _empty_quote()
                    if out[t].get("price", 0) > 0:
                        consecutive_errors = 0
                    else:
                        consecutive_errors += 1
                except Exception as e:
                    logging.warning("fetch_stock_quote 병렬 실패 ticker=%s: %s", t, e)
                    out[t] = _empty_quote()
                    consecutive_errors += 1

                if consecutive_errors >= max_consecutive_errors and n > workers:
                    logging.error(
                        f"Too many consecutive errors ({consecutive_errors}). Possible network issue. Stopping batch early."
                    )
                    for rem_fut in future_map:
                        rem_t = future_map[rem_fut]
                        if rem_t not in out:
                            out[rem_t] = _empty_quote()
                    break
        except Exception as e:
            logging.error(f"fetch_stock_prices_parallel 전체 타임아웃/오류: {e}")
            for t in tickers:
                if t not in out:
                    out[t] = _empty_quote()
    return out


# 해외지수: api.stock.naver.com/index/{symbol}/basic
_NAVER_WORLD_INDEX_SYMBOL_BY_TICKER = {
    "NASDAQ": ".IXIC",
    "SP500": ".INX",
}

# 환율: api.stock.naver.com/marketindex/exchange/{code}
_NAVER_EXCHANGE_MARKETINDEX_BY_TICKER = {
    "USDKRW": "FX_USDKRW",
}


def _quote_from_naver_basic_payload(data: dict, *, as_int: bool = False) -> Dict[str, Any]:
    """closePrice / compareToPreviousClosePrice / fluctuationsRatio 공통 파싱."""
    price = _parse_naver_number(data.get("closePriceRaw", data.get("closePrice")))
    change = _parse_naver_number(
        data.get("compareToPreviousClosePriceRaw", data.get("compareToPreviousClosePrice"))
    )
    pct = _parse_naver_number(data.get("fluctuationsRatioRaw", data.get("fluctuationsRatio")))
    return _quote_from_price_change(price, change, pct, as_int=as_int)


def fetch_world_sise_quote(symbol: str):
    """네이버 stock API 해외지수 시세 (api.stock.naver.com/index/{symbol}/basic)."""
    url = f"https://api.stock.naver.com/index/{quote(symbol, safe='.@')}/basic"
    try:
        data = _naver_get_json(
            url,
            _naver_api_headers(
                f"https://stock.naver.com/worldstock/index/{quote(symbol, safe='.@')}",
                origin="https://stock.naver.com",
            ),
        )
        if not data:
            logging.warning("[world_index %s] 빈 응답", symbol)
            return _empty_quote()
        quote_data = _quote_from_naver_basic_payload(data)
        if quote_data.get("price", 0) <= 0:
            logging.warning("[world_index %s] 지수 값을 파싱하지 못했습니다.", symbol)
            return _empty_quote()
        return quote_data
    except Exception as e:
        logging.error("[world_index %s] 크롤링 오류: %s", symbol, e)
        return _empty_quote()


def fetch_exchange_detail_quote(marketindex_cd: str):
    """네이버 stock API 환율 (api.stock.naver.com/marketindex/exchange/{code})."""
    url = f"https://api.stock.naver.com/marketindex/exchange/{quote(marketindex_cd, safe='_')}"
    try:
        data = _naver_get_json(
            url,
            _naver_api_headers(
                "https://stock.naver.com/marketindex",
                origin="https://stock.naver.com",
            ),
        )
        info = (data or {}).get("exchangeInfo") or {}
        price = _parse_naver_number(info.get("calcPrice", info.get("closePrice")))
        change = _parse_naver_number(info.get("fluctuations"))
        pct = _parse_naver_number(info.get("fluctuationsRatio"))
        quote_data = _quote_from_price_change(price, change, pct)
        if quote_data.get("price", 0) <= 0:
            logging.warning("[exchange %s] 환율 값을 파싱하지 못했습니다.", marketindex_cd)
            return _empty_quote()
        return quote_data
    except Exception as e:
        logging.error("[exchange %s] 크롤링 오류: %s", marketindex_cd, e)
        return _empty_quote()


def fetch_domestic_stock_quote(ticker: str):
    """국내 종목 현재가: api.stock.naver.com 5분봉 차트 API."""
    code = str(ticker).strip()
    url = f"https://api.stock.naver.com/chart/domestic/item/{quote(code, safe='')}/minute5?wrapper=true"
    start_time = time.time()
    if _FETCH_PRICE_VERBOSE_LOGS:
        logging.info("[%s] 현재가 크롤링 시작 (chart minute5)...", code)
    try:
        data = _naver_get_json(
            url,
            _naver_api_headers(
                f"https://stock.naver.com/domestic/stock/{quote(code, safe='')}/price",
                origin="https://stock.naver.com",
            ),
        )
        if not data:
            logging.warning("[%s] 빈 응답", code)
            return _empty_quote()

        infos = data.get("priceInfos") or []
        if not infos:
            logging.warning("[%s] priceInfos 없음", code)
            return _empty_quote()

        latest = infos[-1] if isinstance(infos[-1], dict) else {}
        price = _parse_naver_number(latest.get("currentPrice"))
        last_close = _parse_naver_number(data.get("lastClosePrice"))
        change = None
        pct = None
        if price is not None and last_close is not None and last_close != 0:
            change = price - last_close
            pct = (change / last_close) * 100.0

        quote_data = _quote_from_price_change(price, change, pct, as_int=True)
        elapsed = time.time() - start_time
        if quote_data.get("price", 0) <= 0:
            logging.warning("[%s] 현재가 정보를 찾을 수 없습니다. (소요시간: %.2f초)", code, elapsed)
            return _empty_quote()
        if _FETCH_PRICE_VERBOSE_LOGS:
            logging.info("[%s] 크롤링 완료: %s원 (소요시간: %.2f초)", code, quote_data["price"], elapsed)
        return quote_data
    except requests.exceptions.ConnectionError as e:
        elapsed = time.time() - start_time
        logging.error("[%s] Fatal connection error: %s (소요시간: %.2f초)", code, e, elapsed)
        raise
    except (requests.exceptions.RequestException, ValueError, TypeError, KeyError) as e:
        elapsed = time.time() - start_time
        logging.error("[%s] 현재가 크롤링 중 오류 발생: %s (소요시간: %.2f초)", code, e, elapsed)
        return _empty_quote()


def fetch_stock_quote(ticker):
    """네이버 stock API에서 현재가·전일대비·등락률(%) 조회."""
    up_ticker = str(ticker).upper()
    ex_cd = _NAVER_EXCHANGE_MARKETINDEX_BY_TICKER.get(up_ticker)
    if ex_cd:
        return fetch_exchange_detail_quote(ex_cd)
    world_sym = _NAVER_WORLD_INDEX_SYMBOL_BY_TICKER.get(up_ticker)
    if world_sym:
        return fetch_world_sise_quote(world_sym)
    if up_ticker in ("KOSPI", "KOSDAQ"):
        return fetch_index_price(up_ticker)
    return fetch_domestic_stock_quote(ticker)


def fetch_stock_price(ticker):
    """하위 호환: 현재가만 반환."""
    return int(fetch_stock_quote(ticker).get("price") or 0)


def fetch_index_price(code: str):
    """국내 지수(KOSPI, KOSDAQ): stock.naver.com securityFe basic API."""
    code = str(code).upper()
    url = f"https://stock.naver.com/api/securityFe/api/index/{quote(code, safe='')}/basic"
    try:
        data = _naver_get_json(
            url,
            _naver_api_headers(f"https://stock.naver.com/domestic/index/{quote(code, safe='')}/price"),
        )
        if not data:
            logging.warning("[%s] 빈 응답", code)
            return _empty_quote()
        quote_data = _quote_from_naver_basic_payload(data)
        if quote_data.get("price", 0) <= 0:
            logging.warning("[%s] 현재가 요소를 찾을 수 없습니다.", code)
            return _empty_quote()
        return quote_data
    except Exception as e:
        logging.error("[%s] 지수 크롤링 중 오류 발생: %s", code, e)
        return _empty_quote()


def fetch_kospi_price():
    return fetch_index_price("KOSPI")
