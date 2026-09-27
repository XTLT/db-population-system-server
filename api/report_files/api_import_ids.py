import os
from flask import request, jsonify

from database import get_report_file, add_report_log
from utils.security import require_auth
from . import bp


@bp.route('/<report_id>/import_ids', methods=['POST'])
@require_auth
def api_import_ids(report_id):
    """批量导入证件号码到报表"""
    user = request.current_user
    report = get_report_file(report_id)
    if not report:
        return jsonify({'error': '报表不存在'}), 404

    if not os.path.exists(report['file_path']):
        return jsonify({'error': '文件不存在'}), 404

    data = request.get_json(silent=True) or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'error': '没有可导入的数据'}), 400

    id_map = {}
    for item in ids:
        id_card = str(item.get('id_card', '')).strip()
        if id_card:
            id_map[id_card] = item

    try:
        import openpyxl
        wb = openpyxl.load_workbook(report['file_path'])
        ws = wb.active
    except Exception as e:
        return jsonify({'error': f'读取报表失败: {e}'}), 500

    id_col_idx = None
    phone_col_idx = None
    social_cols = {}

    for col_idx, cell in enumerate(ws[1], 1):
        val = str(cell.value or '').strip()
        if val in ('身份证号', '证件号码', '身份证', '身份证号码', 'ID'):
            id_col_idx = col_idx
        elif val in ('电话', '手机号', '手机', '联系电话', '联系方式'):
            phone_col_idx = col_idx
        elif val in ('社保卡1', '社保卡号1', '社会保障卡1'):
            social_cols[1] = col_idx
        elif val in ('社保卡2', '社保卡号2', '社会保障卡2'):
            social_cols[2] = col_idx
        elif val in ('社保卡3', '社保卡号3', '社会保障卡3'):
            social_cols[3] = col_idx

    if id_col_idx is None:
        return jsonify({'error': '报表中未找到身份证号列'}), 400

    updated = 0
    not_found = 0

    for row in ws.iter_rows(min_row=2, min_col=1, max_col=ws.max_column):
        id_cell = row[id_col_idx - 1]
        id_val = str(id_cell.value or '').strip()
        if not id_val:
            continue

        if id_val in id_map:
            item = id_map[id_val]
            if phone_col_idx and item.get('phone'):
                ws.cell(row=id_cell.row, column=phone_col_idx, value=item['phone'])
            for key, col_idx in social_cols.items():
                field = f'social{key}'
                if item.get(field):
                    ws.cell(row=id_cell.row, column=col_idx, value=item[field])
            updated += 1
        else:
            not_found += 1

    wb.save(report['file_path'])

    add_report_log(
        report_id=report_id,
        user_id=user['id'],
        username=user['username'],
        operation_type='批量导入证件号码',
        operation_detail=f'更新:{updated}, 未匹配:{not_found}',
        ip_address=request.remote_addr,
        client_type='Desktop',
    )

    return jsonify({'success': True, 'updated': updated, 'not_found': not_found})
