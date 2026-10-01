import copy
import threading
import time


class _Entry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value, expires_at):
        self.value = value
        self.expires_at = expires_at


class QueryCache:
    """
    Thread-safe in-memory TTL cache with single-flight loading.
    - Cache miss 동시 요청은 1개만 loader 실행
    - 나머지는 동일 key 결과를 기다렸다가 재사용
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._entries = {}
        self._inflight = {}

    def get_or_load(self, key, ttl_seconds, loader, wait_timeout=5.0):
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry and entry.expires_at > now:
                return copy.deepcopy(entry.value)

            wait_event = self._inflight.get(key)
            if wait_event is None:
                wait_event = threading.Event()
                self._inflight[key] = wait_event
                should_load = True
            else:
                should_load = False

        if should_load:
            try:
                value = loader()
                expires_at = time.monotonic() + max(0.0, float(ttl_seconds))
                with self._lock:
                    self._entries[key] = _Entry(value=value, expires_at=expires_at)
                return copy.deepcopy(value)
            finally:
                with self._lock:
                    event = self._inflight.pop(key, None)
                    if event:
                        event.set()

        # 다른 스레드가 로드 중이면 잠시 대기 후 캐시 재확인
        wait_event.wait(timeout=max(0.0, float(wait_timeout)))
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry and entry.expires_at > now:
                return copy.deepcopy(entry.value)

        # 대기 타임아웃 또는 로드 실패 시 직접 재시도
        value = loader()
        expires_at = time.monotonic() + max(0.0, float(ttl_seconds))
        with self._lock:
            self._entries[key] = _Entry(value=value, expires_at=expires_at)
        return copy.deepcopy(value)

    def invalidate(self, key):
        with self._lock:
            self._entries.pop(key, None)

    def clear(self):
        with self._lock:
            self._entries.clear()


query_cache = QueryCache()
