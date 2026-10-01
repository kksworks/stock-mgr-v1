"""
주기적 계좌 현재가 크롤링 및 balance_history 저장 스케줄러.
설정은 MongoDB app_settings 컬렉션의 balance_refresh 문서에서 읽음.
"""
import logging
import threading
import atexit

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor as APSchedulerThreadPoolExecutor
from backend import config_loader, runtime_state
from backend.time_utils import now_kst

# 앱 컨텍스트에서 실행하기 위해 Flask app 참조는 나중에 주입
_flask_app = None
_scheduler = None
_job_lock = threading.Lock()

JOB_BALANCE_REFRESH = "balance_refresh"
JOB_PORTFOLIO_REFRESH = "portfolio_ticker_refresh"

SETTINGS_BALANCE_REFRESH = "balance_refresh"
SETTINGS_PORTFOLIO_REFRESH = "portfolio_refresh"

DEFAULT_BALANCE_CRON = "0 9,15 * * 1-5"  # 평일 09:00, 15:00
DEFAULT_PORTFOLIO_INTERVAL = 10  # 10분

# 호완성을 위한 별칭
DEFAULT_CRON = DEFAULT_BALANCE_CRON
_config = config_loader.load_config()
_SCHEDULER_MAX_WORKERS = max(1, config_loader.get_int(_config, 'performance', 'scheduler_max_workers', 2))
_SCHEDULER_MAX_ACTIVE_REQUESTS = max(1, config_loader.get_int(_config, 'performance', 'scheduler_max_active_requests', 2))
_SCHEDULER_MISFIRE_GRACE_SEC = max(30, config_loader.get_int(_config, 'performance', 'scheduler_misfire_grace_sec', 120))
_SCHEDULER_JOB_MAX_INSTANCES = max(1, config_loader.get_int(_config, 'performance', 'scheduler_job_max_instances', 1))
_SCHEDULER_COALESCE = config_loader.get_bool(_config, 'performance', 'scheduler_coalesce', True)
_PORTFOLIO_REFRESH_MIN_INTERVAL = max(5, config_loader.get_int(_config, 'performance', 'portfolio_refresh_min_interval_minutes', 15))


def _run_balance_refresh_job():
    """스케줄 실행 시 호출: Flask 앱 컨텍스트 안에서 전체 계좌 갱신."""
    global _flask_app, _job_lock
    if not _flask_app:
        logging.warning("balance_refresh job: Flask app not set, skip.")
        return
    
    if runtime_state.get_active_requests() >= _SCHEDULER_MAX_ACTIVE_REQUESTS:
        logging.info(
            "balance_refresh job deferred: active requests=%d (limit=%d)",
            runtime_state.get_active_requests(),
            _SCHEDULER_MAX_ACTIVE_REQUESTS,
        )
        return

    if not _job_lock.acquire(blocking=False):
        logging.warning("balance_refresh job: Previous job still running, skipping this run.")
        return
    
    try:
        with _flask_app.app_context():
            try:
                from backend.routes.account_api import run_refresh_all_balances_admin
                updated = run_refresh_all_balances_admin()
                logging.info("balance_refresh job completed: %d accounts updated.", len(updated))
                _update_last_run(SETTINGS_BALANCE_REFRESH, now_kst())
            except Exception as e:
                logging.exception("balance_refresh job failed: %s", e)
    finally:
        _job_lock.release()


def _run_portfolio_refresh_job():
    """스케줄 실행 시 호출: 모든 포트폴리오의 티커 현재가 갱신."""
    global _flask_app
    if not _flask_app:
        return
    
    if runtime_state.get_active_requests() >= _SCHEDULER_MAX_ACTIVE_REQUESTS:
        logging.info(
            "portfolio_refresh job deferred: active requests=%d (limit=%d)",
            runtime_state.get_active_requests(),
            _SCHEDULER_MAX_ACTIVE_REQUESTS,
        )
        return

    try:
        with _flask_app.app_context():
            from backend.services import portfolio_collection, ticker_collection
            from backend import crawler
            
            # 1. 모든 포트폴리오에서 유니크 티커 추출
            ports = list(portfolio_collection.find({}))
            tickers = set()
            for p in ports:
                for item in p.get('items', []):
                    if item.get('ticker'):
                        tickers.add(item['ticker'])
            
            if not tickers:
                return
            
            # 2. 가격 갱신 ( 설정된 threshold 캐시 시간 존중 )
            logging.info(f"portfolio_refresh job: Refreshing {len(tickers)} unique tickers.")
            from backend.routes.account_api import _get_price_threshold
            threshold = _get_price_threshold()
            crawler.update_stale_prices(ticker_collection, list(tickers), threshold)
            _update_last_run(SETTINGS_PORTFOLIO_REFRESH, now_kst())
            logging.info("portfolio_refresh job completed.")
            
    except Exception as e:
        logging.exception("portfolio_refresh job failed: %s", e)


def _update_last_run(settings_id, now):
    try:
        from backend.services import settings_collection
        settings_collection.update_one(
            {"_id": settings_id},
            {"$set": {"last_run": now, "updated_at": now}},
            upsert=True,
        )
    except Exception as e:
        logging.warning("Could not update last_run: %s", e)


def get_schedule_doc(settings_id=SETTINGS_BALANCE_REFRESH):
    """DB에서 스케줄 설정 조회. 없으면 기본값."""
    from backend.services import settings_collection
    doc = settings_collection.find_one({"_id": settings_id})
    if not doc:
        if settings_id == SETTINGS_BALANCE_REFRESH:
            return {"enabled": False, "cron": DEFAULT_BALANCE_CRON, "last_run": None}
        else:
            return {"enabled": True, "interval": DEFAULT_PORTFOLIO_INTERVAL, "last_run": None}
    
    if settings_id == SETTINGS_BALANCE_REFRESH:
        return {
            "enabled": doc.get("enabled", False),
            "cron": doc.get("cron", DEFAULT_BALANCE_CRON),
            "last_run": doc.get("last_run"),
        }
    else:
        return {
            "enabled": doc.get("enabled", True),
            "interval": doc.get("interval", DEFAULT_PORTFOLIO_INTERVAL),
            "last_run": doc.get("last_run"),
        }


def set_schedule_doc(enabled, cron_or_interval, settings_id=SETTINGS_BALANCE_REFRESH):
    """스케줄 설정 저장 후 스케줄러 반영."""
    from backend.services import settings_collection
    now = now_kst()
    field = "cron" if settings_id == SETTINGS_BALANCE_REFRESH else "interval"
    settings_collection.update_one(
        {"_id": settings_id},
        {"$set": {"enabled": enabled, field: cron_or_interval, "updated_at": now}},
        upsert=True,
    )
    reschedule_job()


def _parse_cron(cron_str):
    """'0 9,15 * * 1-5' -> (분, 시, 일, 월, 요일) 또는 CronTrigger."""
    s = (cron_str or DEFAULT_BALANCE_CRON).strip()
    parts = s.split()
    if len(parts) != 5:
        return None
    try:
        return CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
        )
    except Exception:
        return None


def reschedule_job():
    """DB 설정에 따라 모든 job 예약/해제."""
    global _scheduler
    if not _scheduler:
        return

    # 1. Balance Refresh (Cron)
    if _scheduler.get_job(JOB_BALANCE_REFRESH) is not None:
        _scheduler.remove_job(JOB_BALANCE_REFRESH)
    
    doc_b = get_schedule_doc(SETTINGS_BALANCE_REFRESH)
    if doc_b.get("enabled"):
        trigger = _parse_cron(doc_b.get("cron"))
        if not trigger:
            trigger = _parse_cron(DEFAULT_BALANCE_CRON)
        _scheduler.add_job(_run_balance_refresh_job, trigger, id=JOB_BALANCE_REFRESH, replace_existing=True)
        logging.info("balance_refresh scheduled: cron=%s", doc_b.get("cron") or DEFAULT_BALANCE_CRON)

    # 2. Portfolio Refresh (Interval)
    if _scheduler.get_job(JOB_PORTFOLIO_REFRESH) is not None:
        _scheduler.remove_job(JOB_PORTFOLIO_REFRESH)
    
    doc_p = get_schedule_doc(SETTINGS_PORTFOLIO_REFRESH)
    if doc_p.get("enabled"):
        interval = max(_PORTFOLIO_REFRESH_MIN_INTERVAL, int(doc_p.get("interval", DEFAULT_PORTFOLIO_INTERVAL)))
        _scheduler.add_job(
            _run_portfolio_refresh_job,
            'interval',
            minutes=interval,
            id=JOB_PORTFOLIO_REFRESH,
            replace_existing=True
        )
        logging.info("portfolio_refresh scheduled: interval=%d min", interval)


def get_next_run_time(job_id=None):
    """지정한 job_id(기본: balance_refresh)의 다음 실행 예정 시각."""
    global _scheduler
    if not _scheduler:
        return None
    jid = job_id or JOB_BALANCE_REFRESH
    job = _scheduler.get_job(jid)
    if not job:
        return None
    return job.next_run_time


def init_scheduler(flask_app):
    """Flask 앱 기동 시 스케줄러 초기화."""
    global _flask_app, _scheduler
    _flask_app = flask_app
    # 스케줄러 내부 실행 풀을 config.ini로 제어해 서버 스펙에 맞춰 부하를 조절.
    _scheduler = BackgroundScheduler(
        executors={'default': APSchedulerThreadPoolExecutor(max_workers=_SCHEDULER_MAX_WORKERS)},
        job_defaults={
            'coalesce': _SCHEDULER_COALESCE,
            'max_instances': _SCHEDULER_JOB_MAX_INSTANCES,
            'misfire_grace_time': _SCHEDULER_MISFIRE_GRACE_SEC,
        }
    )
    reschedule_job()
    _scheduler.start()
    logging.info("Scheduler initialized with multijob support.")

    # 프로세스 종료 시 스케줄러를 함께 종료하도록 등록
    atexit.register(lambda: _scheduler.shutdown() if _scheduler else None)
