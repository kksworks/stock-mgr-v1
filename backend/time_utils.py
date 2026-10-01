from datetime import datetime, timezone
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def now_kst():
    return datetime.now(KST)


def ensure_kst(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=KST)
    return dt.astimezone(KST)


def ensure_kst_from_utc_naive(dt):
    """MongoDB에서 tz 없는 UTC datetime으로 반환되는 값을 KST로 정규화."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(KST)
    return dt.astimezone(KST)

