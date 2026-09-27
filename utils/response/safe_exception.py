import os
from flask import jsonify
from .log_error import log_error


def safe_exception(e: Exception, user_message: str = "服务器内部错误", status: int = 500):
    log_error(f"异常: {type(e).__name__}: {str(e)}", exc=e)

    if os.environ.get('FLASK_DEBUG') == '1':
        return jsonify({'error': str(e)}), status
    else:
        return jsonify({'error': user_message}), status
