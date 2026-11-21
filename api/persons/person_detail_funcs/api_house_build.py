"""宅基地建房申请：列表、详情、新建/更新/删除、身份证预填、Excel/PDF 导出。"""

import os
import shutil

from flask import after_this_request, jsonify, request, send_file

from database import (
    add_operation_log,
    create_house_build_app,
    delete_house_build_app,
    export_app_pdf,
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

    try:
        path = export_app_xlsx(app_data) if fmt == 'xlsx' else export_app_pdf(app_data)
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
