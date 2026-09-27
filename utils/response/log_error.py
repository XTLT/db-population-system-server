import os
import traceback
from ._base import logger


def log_error(message: str, exc: Exception = None):
    logger.error(message)
    if exc and os.environ.get('FLASK_DEBUG') == '1':
        logger.debug(traceback.format_exc())
