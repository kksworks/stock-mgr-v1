from backend import config_loader, database

# 설정 및 DB 연결 초기화
config = config_loader.load_config()

ticker_collection = database.get_collection(config)
account_collection = database.get_account_collection(config)
transaction_collection = database.get_transaction_collection(config)
portfolio_collection = database.get_portfolio_collection(config)
balance_collection = database.get_balance_collection(config)
balance_history_collection = database.get_balance_history_collection(config)
account_monthly_trend_collection = database.get_account_monthly_trend_collection(config)
user_collection = database.get_user_collection(config)
log_collection = database.get_log_collection(config)
settings_collection = database.get_settings_collection(config)
user_preferences_collection = database.get_user_preferences_collection(config)
board_collection = database.get_board_collection(config)

# 편의를 위한 별칭 (app.py 등에서 사용)
app_config = config
