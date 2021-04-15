import logging

from dotenv import load_dotenv

logging.basicConfig(
    format="%(levelname)s: %(name)s | %(asctime)s -> %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

if not load_dotenv():
    logger.warning("You must setup your environment variables to benefit all features")
