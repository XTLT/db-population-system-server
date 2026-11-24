"""宅基地建房申请：列表、详情、新建/更新/删除、身份证预填、Excel/PDF 导出。"""

import os
import shutil

from flask import after_this_request, jsonify, request, send_file

from database import (
    add_operation_log,
    create_house_build_app,
    delete_house_build_app,
    export_app_pdf,
    export_apps_pdf,
    export_app_xlsx,
    get_house_build_app,
    list_house_build_apps,
    prefill_by_id_card,
    update_house_build_app,
)
from utils.security import get_client_ip, require_auth


def _log(action, detail):
    user = getattr(request, 'current_user', None) or {}
    try:
        add_operation_log(
            user.get('id', ''),
            user.get('username', ''),
            action,
            detail,
            get_client_ip(),
            request.headers.get('X-Client-Type', 'Web'),
        )
    except Exception:
        pass


def _client_type():
    return request.headers.get('X-Client-Type', 'Web')


def _meeting_info(payload=None):
    """导出抬头与会议记录信息：乡镇/村 + 时间/地点/主持人/记录人，均可留空。"""
    payload = payload if isinstance(payload, dict) else {}
    result = {}
    for key in ('date', 'place', 'host', 'recorder', 'township', 'village'):
        value = payload.get(key)
        result[key] = str(value or '').strip()[:120]
    return result


@require_auth
def api_house_build_list():
    try:
        result = list_house_build_apps(
            keyword=request.args.get('keyword', ''),
            status=request.args.get('status', ''),
            year=request.args.get('year', ''),
            group_name=request.args.get('group_name', ''),
            page=request.args.get('page', 1),
            page_size=request.args.get('page_size', 20),
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': '查询建房申请失败：%s' % e}), 500


@require_auth
def api_house_build_detail(app_id):
    try:
        app_data = get_house_build_app(app_id)
    except Exception as e:
        return jsonify({'error': '读取建房申请失败：%s' % e}), 500
    if app_data is None:
        return jsonify({'error': '建房申请不存在'}), 404
    return jsonify(app_data)


@require_auth
def api_house_build_create():
    data = request.get_json(silent=True) or {}
    user = request.current_user
    try:
        result = create_house_build_app(data, operator=user.get('username', ''))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': '保存建房申请失败：%s' % e}), 500
    _log('新建建房申请', '%s %s' % (result.get('owner_name', ''), result.get('app_no', '')))
    return jsonify({'success': True, 'data': result}), 201


@require_auth
def api_house_build_update(app_id):
    data = request.get_json(silent=True) or {}
    user = request.current_user
    try:
        result = update_house_build_app(app_id, data, operator=user.get('username', ''))
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': '更新建房申请失败：%s' % e}), 500
    if result is None:
        return jsonify({'error': '建房申请不存在'}), 404
    _log('修改建房申请', '%s %s' % (result.get('owner_name', ''), result.get('app_no', '')))
    return jsonify({'success': True, 'data': result})


@require_auth
def api_house_build_delete(app_id):
    try:
        removed = delete_house_build_app(app_id)
    except Exception as e:
        return jsonify({'error': '删除建房申请失败：%s' % e}), 500
    if not removed:
        return jsonify({'error': '建房申请不存在'}), 404
    _log('删除建房申请', app_id)
    return jsonify({'success': True})


@require_auth
def api_house_build_prefill():
    id_card = (request.args.get('id_card') or '').strip()
    if not id_card:
        return jsonify({'error': '缺少 id_card'}), 400
    try:
        return jsonify(prefill_by_id_card(id_card))
    except Exception as e:
        return jsonify({'error': '预填失败：%s' % e}), 500


@require_auth
def api_house_build_export(app_id):
    fmt = (request.args.get('fmt') or 'xlsx').strip().lower()
    if fmt not in ('xlsx', 'pdf'):
        return jsonify({'error': '不支持的导出格式，仅支持 xlsx / pdf'}), 400

    app_data = get_house_build_app(app_id)
    if app_data is None:
        return jsonify({'error': '建房申请不存在'}), 404

    meeting_info = _meeting_info({
        'date': request.args.get('meeting_date'),
        'place': request.args.get('meeting_place'),
        'host': request.args.get('meeting_host'),
        'recorder': request.args.get('meeting_recorder'),
        'township': request.args.get('meeting_township'),
        'village': request.args.get('meeting_village'),
    }) if fmt == 'pdf' else None

    try:
        path = export_app_xlsx(app_data) if fmt == 'xlsx' else export_app_pdf(app_data, meeting_info)
    except Exception as e:
        return jsonify({'error': '生成导出文件失败：%s' % e}), 500

    tmp_dir = os.path.dirname(path)

    @after_this_request
    def _cleanup(response):
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return response

    _log('导出建房申请', '%s %s %s' % (app_data.get('owner_name', ''), app_data.get('app_no', ''), fmt))
    return send_file(
        path,
        as_attachment=True,
        download_name=os.path.basename(path),
        mimetype='application/pdf' if fmt == 'pdf' else
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )


@require_auth
def api_house_build_batch_export():
    """多户合并导出：每户 6 页，会议记录和公示共用；只支持 PDF。"""
    data = request.get_json(silent=True) or {}
    fmt = (data.get('fmt') or 'pdf').strip().lower()
    if fmt != 'pdf':
        return jsonify({'error': '批量导出仅支持 pdf'}), 400

    raw_ids = data.get('ids')
    if not isinstance(raw_ids, list):
        return jsonify({'error': '缺少 ids 列表'}), 400
    ids = []
    for value in raw_ids:
        text = str(value or '').strip()
        if text and text not in ids:
            ids.append(text)
    if not ids:
        return jsonify({'error': '请至少选择一户'}), 400
    if len(ids) > 50:
        return jsonify({'error': '一次最多导出 50 户'}), 400

    apps = []
    missing = []
    for app_id in ids:
        app_data = get_house_build_app(app_id)
        if app_data is None:
            missing.append(app_id)
        else:
            apps.append(app_data)
    if missing:
        return jsonify({'error': '以下建房申请不存在：%s' % '、'.join(missing)}), 404

    meeting_info = _meeting_info(data.get('meeting'))
    try:
        path = export_apps_pdf(apps, meeting_info)
    except Exception as e:
        return jsonify({'error': '生成批量导出文件失败：%s' % e}), 500

    tmp_dir = os.path.dirname(path)

    @after_this_request
    def _cleanup(response):
        shutil.rmtree(tmp_dir, ignore_errors=True)
        return response

    _log('批量导出建房申请', '%d户 %s' % (len(apps), fmt))
    return send_file(
        path,
        as_attachment=True,
        download_name=os.path.basename(path),
        mimetype='application/pdf',
    )
