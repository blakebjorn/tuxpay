import configparser
import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

from modules.helpers import read_json, random_alphanumeric_string
from modules.logging import logger


def get_app_secret():
    return os.environ['APP_SECRET']


def check_application_secret():
    application_secret = os.environ.get("APP_SECRET")
    if application_secret is None:
        os.environ['APP_SECRET'] = random_alphanumeric_string(32, subset='all', secure=True)
        with open('data/.env', 'a') as f:
            f.write(f"APP_SECRET={os.environ['APP_SECRET']}")
        logger.warn("APP_SECRET environment variable was not set."
                    " Application secret was set to {application_secret} and saved to `.env` in the data folder")


def get(key, default=None, namespace='global', coin=None, prefer_coin=None):
    if prefer_coin is not None:
        # If a coin-specific value exists, take it, otherwise fallback to global namespace or default
        return get(key, coin=prefer_coin) or get(key, default=default)

    if coin is not None:
        namespace = f"COIN_{coin}"
    if namespace not in _config:
        return default
    return _config[namespace].get(key, fallback=default)


def check(key, namespace='global', coin=None):
    return get(key, default="", coin=coin,
               namespace=namespace if coin is None else None).upper().strip() in ("1", "TRUE", "YES", "T")


def to_dict():
    output = {}
    for section in _config.sections():
        output[section] = {k: v for k, v in _config[section].items()}
    return output


data_path = (Path(__file__).parent / "..").resolve() / "data"
load_dotenv(dotenv_path=data_path / ".env")

if not (data_path / "config.ini").exists():
    logger.warn("config.ini does not exist, copying contents of config.default.ini")
    shutil.copy2(data_path / "config.default.ini", data_path / "config.ini")

_config = configparser.ConfigParser()
_config.read(data_path / "config.ini")

xpubs = read_json(data_path / ".xpubs.json", {})
check_application_secret()
