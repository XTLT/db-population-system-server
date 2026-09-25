import logging
import traceback
import os
from flask import jsonify, request

logger = logging.getLogger('population_system')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_error(message: str, exc: Exception = None):
    logger.error(message)
    if exc and os.environ.get('FLASK_DEBUG') == '1':
        logger.debug(traceback.format_exc())


def safe_error(message: str, status: int = 400, log_details: bool = True):
    if log_details:
        log_error(message)
        if os.environ.get('FLASK_DEBUG') == '1':
            traceback.print_exc()
    
    return jsonify({'error': message}), status


def safe_exception(e: Exception, user_message: str = "服务器内部错误", status: int = 500):
    log_error(f"异常: {type(e).__name__}: {str(e)}", exc=e)
    
    if os.environ.get('FLASK_DEBUG') == '1':
        return jsonify({'error': str(e)}), status
    else:
        return jsonify({'error': user_message}), status


def get_json_data():
    data = request.json
    if data is None:
        return None, (jsonify({'error': '请求数据格式错误'}), 400)
    return data, None
