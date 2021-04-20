import logging.config
import os
from collections import namedtuple
from pathlib import Path

import toml
from dotenv import load_dotenv

__all__ = [
    "__version__",
    "CONFIG",
    "STATIC_DIR",
]

_VersionInfo = namedtuple("VersionInfo", ("major", "minor"))
_BOT_DIR = Path(__file__).parent

__version__ = _VersionInfo(2, 1)
# Global dict which contains bot config
CONFIG = toml.load(_BOT_DIR.parent / "bot-config.toml")
STATIC_DIR = _BOT_DIR / "static"


def setup():
    load_dotenv()  # Loads .env file by default
    log_config = toml.load(_BOT_DIR.parent / "log-config.toml")

    if os.getenv("ENVIRONMENT") == "development":
        # All logger are herited from the root logger
        log_config["root"] = log_config["loggers"]["development"]

    # Creates logs in current directory, does anything if it already exists
    os.makedirs("logs", exist_ok=True)
    logging.config.dictConfig(log_config)  # Loads config


setup()
