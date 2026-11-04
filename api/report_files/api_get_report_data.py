import os
from flask import jsonify, request

from database import get_report_file
from . import bp
from ._auth_from_query import _auth_from_query


@bp.route('/<report_id>/data')
def api_get_report_data(report_id):
    """获取报表数据（JSON 格式，供在线编辑器使用）"""
    user = _auth_from_query()
    if not user:
        return jsonify({'error': '未授权'}), 401

    report = get_report_file(report_id)
    if not report:
        return jsonify({'error': '报表不存在'}), 404

    if not os.path.exists(report['file_path']):
        return jsonify({'error': '文件不存在'}), 404

    try:
        import openpyxl
        from io import BytesIO
        try:
            wb = openpyxl.load_workbook(report['file_path'], data_only=True)
        except Exception:
            # 兼容旧报表：落盘文件名可能无 .xlsx 后缀（secure_filename 丢扩展名），按字节流打开
            with open(report['file_path'], 'rb') as _f:
                wb = openpyxl.load_workbook(BytesIO(_f.read()), data_only=True)
        sheets = wb.sheetnames
        sheet_name = request.args.get('sheet', '')
        if sheet_name and sheet_name in sheets:
            ws = wb[sheet_name]
        else:
            ws = wb.active
            sheet_name = ws.title
    except Exception as e:
        return jsonify({'error': f'读取失败: {e}'}), 500

    headers = []
    rows = []
    for row_idx, row in enumerate(ws.iter_rows(values_only=True), 1):
        if row_idx == 1:
            headers = [str(cell or '') for cell in row]
        else:
            if all(cell is None for cell in row):
                continue
            rows.append([str(cell) if cell is not None else '' for cell in row])

    return jsonify({
        'sheet_name': sheet_name,
        'sheets': sheets,
        'headers': headers,
        'rows': rows,
    })
