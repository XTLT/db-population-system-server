import os
import traceback
from flask import jsonify
from .log_error import log_error


def safe_error(message: str, status: int = 400, log_details: bool = True):
    if log_details:
        log_error(message)
        if os.environ.get('FLASK_DEBUG') == '1':
            traceback.print_exc()

    return jsonify({'error': message}), status
