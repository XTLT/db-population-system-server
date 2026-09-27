from flask import request, jsonify


def get_json_data():
    data = request.json
    if data is None:
        return None, (jsonify({'error': '请求数据格式错误'}), 400)
    return data, None
