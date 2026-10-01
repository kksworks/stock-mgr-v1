from datetime import timezone
from pymongo import MongoClient
from bson.objectid import ObjectId
from backend import config_loader
from backend.time_utils import now_kst

_mongo_client = None

def _get_client(config):
    global _mongo_client
    if _mongo_client is None:
        mongo_url = config['mongodb']['access_url']
        # 서버 리소스/네트워크 상황에 맞게 config.ini에서 풀/타임아웃 튜닝 가능.
        server_selection_timeout_ms = config_loader.get_int(config, 'performance', 'mongodb_server_selection_timeout_ms', 5000)
        connect_timeout_ms = config_loader.get_int(config, 'performance', 'mongodb_connect_timeout_ms', 5000)
        socket_timeout_ms = config_loader.get_int(config, 'performance', 'mongodb_socket_timeout_ms', 5000)
        max_pool_size = config_loader.get_int(config, 'performance', 'mongodb_max_pool_size', 5)
        max_idle_time_ms = config_loader.get_int(config, 'performance', 'mongodb_max_idle_time_ms', 60000)

        _mongo_client = MongoClient(
            mongo_url,
            serverSelectionTimeoutMS=server_selection_timeout_ms,
            connectTimeoutMS=connect_timeout_ms,
            socketTimeoutMS=socket_timeout_ms,
            maxPoolSize=max_pool_size,
            maxIdleTimeMS=max_idle_time_ms,
            # MongoDB datetime 조회를 UTC-aware로 일관되게 받아 TZ 오해석(예: 9시간 오차) 방지
            tz_aware=True,
            tzinfo=timezone.utc,
        )
    return _mongo_client

def get_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection']['ticker']
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_account_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection']['account']
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_portfolio_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection']['portfolio']
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_log_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('log', 'log_datas')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_balance_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('balance', 'balance_datas')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_balance_history_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('balance_history', 'balance_history_datas')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_account_monthly_trend_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('account_monthly_trend', 'account_monthly_trend_datas')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_transaction_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection']['transaction']
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_user_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('user', 'user_datas')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_settings_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('settings', 'app_settings')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_user_preferences_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('user_preferences', 'user_preferences')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]

def get_board_collection(config):
    db_name = config['mongodb']['database']
    col_name = config['collection'].get('board', 'board_posts')
    client = _get_client(config)
    db = client[db_name]
    return db[col_name]


def update_custom_field(collection, ticker, field_name, field_value):
    """특정 티커에 커스텀 필드를 추가하거나 업데이트합니다."""
    return collection.update_one(
        {'ticker': ticker},
        {'$set': {field_name: field_value}}
    )

def upsert_account(collection, account_data):
    """계좌 정보를 업데이트하거나 새로 생성합니다 (계좌번호 기준)."""
    return collection.update_one(
        {'account_number': account_data['account_number']},
        {'$set': account_data},
        upsert=True
    )

def upsert_portfolio(collection, portfolio_data, portfolio_id=None):
    """포트폴리오 정보를 업데이트하거나 새로 생성합니다."""
    if portfolio_id:
        return collection.update_one(
            {'_id': ObjectId(portfolio_id)},
            {'$set': portfolio_data},
            upsert=False
        )
    return collection.insert_one(portfolio_data)

def add_transaction(collection, data):
    """새로운 거래 내역을 추가합니다."""
    return collection.insert_one(data)

def update_transaction(collection, transaction_id, data):
    """기존 거래 내역을 수정합니다."""
    return collection.update_one(
        {'_id': ObjectId(transaction_id)},
        {'$set': data}
    )

def delete_transaction(collection, transaction_id):
    """거래 내역을 삭제합니다."""
    return collection.delete_one({'_id': ObjectId(transaction_id)})

def delete_portfolio(collection, portfolio_id):
    """포트폴리오를 삭제합니다."""
    return collection.delete_one({'_id': ObjectId(portfolio_id)})

def get_transactions_by_account(collection, account_number):
    """특정 계좌의 거래 내역을 날짜 내림차순으로 조회합니다."""
    return list(collection.find({'account_number': account_number}).sort('date', -1))

def get_transaction_by_id(collection, transaction_id):
    """ID로 단일 거래 내역을 조회합니다."""
    return collection.find_one({'_id': ObjectId(transaction_id)})

def search_tickers(collection, query):
    """티커 또는 종목명으로 검색합니다."""
    return list(collection.find({
        '$or': [
            {'ticker': {'$regex': query, '$options': 'i'}},
            {'name': {'$regex': query, '$options': 'i'}}
        ]
    }, {'_id': 0, 'ticker': 1, 'name': 1}).limit(20))

def ensure_indexes(config):
    """주요 컬렉션에 대해 필수 인덱스를 생성하여 성능을 최적화합니다."""
    db_name = config['mongodb']['database']
    client = _get_client(config)
    db = client[db_name]

    # 계좌 컬렉션 (uuid 기준 조회 빈번, 권한 체크용 인덱스 추가)
    acc_col = db[config['collection']['account']]
    acc_col.create_index("uuid", unique=True)
    acc_col.create_index("user_id")
    acc_col.create_index("is_public")
    acc_col.create_index("shared_user_ids")
    # 검색 최적화: 계좌명/계좌번호
    acc_col.create_index("account_name")
    acc_col.create_index("account_number")

    # 잔고/평가 컬렉션 (account_id 기준 조회 빈번)
    bal_col = db[config['collection'].get('balance', 'balance_datas')]
    bal_col.create_index("account_id", unique=True)

    # 거래 내역 컬렉션 (account_id 기준 조회 및 날짜 정렬 빈번)
    tx_col = db[config['collection']['transaction']]
    tx_col.create_index([("account_id", 1), ("date", -1)])
    tx_col.create_index("date") # 날짜만으로도 정렬/필터링 가능하게
    
    # 종목 정보 컬렉션 (ticker 검색 빈번)
    ticker_col = db[config['collection']['ticker']]
    ticker_col.create_index("ticker", unique=True)
    ticker_col.create_index("name")
    # 자산분류별 검색/집계용
    ticker_col.create_index("asset_class")

    # 잔고 이력 컬렉션 (그래프용 조회 빈번)
    hist_col = db[config['collection'].get('balance_history', 'balance_history_datas')]
    hist_col.create_index([("account_id", 1), ("date", 1)])

    # 대시보드 월별 트렌드 (계좌당 월 최대 1문서)
    trend_col = db[config['collection'].get('account_monthly_trend', 'account_monthly_trend_datas')]
    trend_col.create_index([('account_id', 1), ('month', 1)], unique=True)

    # 게시판 컬렉션 (작성일 기준 정렬, 상단고정 기준 정렬)
    board_col = db[config['collection'].get('board', 'board_posts')]
    board_col.create_index([("created_at", -1)])
    board_col.create_index([("pinned", -1), ("created_at", -1)])


def ensure_default_settings(config):
    """기동 시 필요한 기본 설정(스케줄러 등)을 DB에 삽입합니다."""
    db_name = config['mongodb']['database']
    client = _get_client(config)
    db = client[db_name]
    settings_col = db[config['collection'].get('settings', 'app_settings')]

    now = now_kst()

    # 1. Balance Refresh (계좌 갱신) 기본 설정
    if not settings_col.find_one({"_id": "balance_refresh"}):
        settings_col.insert_one({
            "_id": "balance_refresh",
            "enabled": True,
            "cron": "0 9,15 * * 1-5",  # 평일 09, 15시
            "updated_at": now
        })

    # 2. Portfolio Refresh (포트폴리오 티커 갱신) 기본 설정
    if not settings_col.find_one({"_id": "portfolio_refresh"}):
        settings_col.insert_one({
            "_id": "portfolio_refresh",
            # 저사양 서버 기본값: 비활성 + 여유있는 간격
            "enabled": False,
            "interval": 30,  # 30분
            "updated_at": now
        })