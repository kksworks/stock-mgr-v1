import configparser
import os


def load_config():
    # 현재 파일 위치: .../web-test/backend/config_loader.py
    # config.ini 위치: .../web-test/config.ini
    basedir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.dirname(basedir) # 상위 폴더로 이동
    config_path = os.path.join(project_root, 'config.ini')
    config = configparser.ConfigParser()
    config.read(config_path)
    return config


def get_int(config, section, key, default):
    try:
        return config.getint(section, key)
    except Exception:
        return int(default)


def get_float(config, section, key, default):
    try:
        return config.getfloat(section, key)
    except Exception:
        return float(default)


def get_bool(config, section, key, default):
    try:
        return config.getboolean(section, key)
    except Exception:
        return bool(default)


def get_str(config, section, key, default):
    try:
        value = config.get(section, key)
        return value if value is not None and str(value).strip() != "" else default
    except Exception:
        return default