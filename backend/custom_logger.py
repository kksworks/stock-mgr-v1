import logging
from backend.time_utils import now_kst

class MongoDBHandler(logging.Handler):
    """MongoDB에 로그를 저장하는 핸들러"""
    def __init__(self, collection):
        super().__init__()
        self.collection = collection

    def emit(self, record):
        try:
            log_entry = {
                'level': record.levelname,
                'message': self.format(record),
                'timestamp': now_kst(),
                'module': record.module,
                'lineno': record.lineno
            }
            # 데이터베이스 핸들러이므로 네트워크 장애 등으로 인한 블로킹이 발생할 수 있음.
            # 타임아웃은 데이터베이스 연결 설정(_get_client)에서 5초로 관리함.
            self.collection.insert_one(log_entry)
        except Exception:
            self.handleError(record)