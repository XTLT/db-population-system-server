# -*- coding: utf-8 -*-
"""服务器本地更新包下载接口。

客户端从服务器直接下载 exe/apk（mTLS 双向证书已在 stunnel 层校验）。
"""
import os

from flask import request, send_file, jsonify

from . import bp
from ._check_local_package import get_local_package_meta


@bp.route('/download')
def download_update_package():
    app_type = request.args.get('type', 'mobile')
    meta = get_local_package_meta(app_type)
    if not meta:
        return jsonify({'error': '服务器上暂无该端的更新包'}), 404
    fname = meta.get('file', '')
    full = meta.get('_full_path', '')
    if not full or not os.path.exists(full):
        return jsonify({'error': '更新包文件不存在'}), 404
    return send_file(
        full,
        as_attachment=True,
        download_name=fname,
        conditional=True,
        max_age=0,
    )
