import threading

_lock = threading.Lock()
_active_requests = 0


def increment_active_requests():
    global _active_requests
    with _lock:
        _active_requests += 1
        return _active_requests


def decrement_active_requests():
    global _active_requests
    with _lock:
        _active_requests = max(0, _active_requests - 1)
        return _active_requests


def get_active_requests():
    with _lock:
        return _active_requests

