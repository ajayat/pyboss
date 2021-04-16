import logging.config
import os
from pathlib import Path

import toml
from dotenv import load_dotenv

load_dotenv()  # load .env file by default

ROOT_DIR = Path(__file__).parent.parent
os.chdir(ROOT_DIR)  # make sure that the bot runs under ROOT_DIR

STATIC_DIR = ROOT_DIR / "bot/static"
BOT_CONFIG = toml.load("bot-config.toml")
_log_config = toml.load("bot/logging-config.toml")  # Loads logging config

if os.getenv("ENVIRONMENT") == "development":
    # All logged are herited from the root logger
    _log_config["root"] = _log_config["loggers"]["development"]

os.makedirs("bot/logs", exist_ok=True)  # Does anything if it already exists
logging.config.dictConfig(_log_config)  # Loads config
