import os
from flask import request

from database import get_report_file
from . import bp
from ._auth_from_query import _auth_from_query
from ._render_editor_html import _render_editor_html


@bp.route('/<report_id>/edit')
def api_edit_report(report_id):
    """在线编辑报表页面（浏览器打开）"""
    user = _auth_from_query()
    if not user:
        return '<html><body><h2>登录已过期，请重新登录后重试</h2></body></html>', 401

    report = get_report_file(report_id)
    if not report:
        return '<html><body><h2>报表不存在</h2></body></html>', 404

    if not os.path.exists(report['file_path']):
        return '<html><body><h2>报表文件不存在</h2></body></html>', 404

    token = request.args.get('token', '')
    return _render_editor_html(report_id, report['name'], token)
