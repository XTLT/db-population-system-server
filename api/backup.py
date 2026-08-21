import os
import secrets
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file

from database import add_operation_log
from utils.security import require_auth
from utils.response import safe_error, get_json_data
from config import BACKUP_DIR
from excel_importer import backup_database, get_backup_status, get_backup_list, restore_database


bp = Blueprint('backup', __name__)
_backup_download_times = {}


@bp.route('', methods=['POST'])
@require_auth
def api_backup():
    """创建备份（仅管理员）"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    result = backup_database(manual=True)
    add_operation_log(
        request.current_user['id'],
        request.current_user['username'],
        "数据备份",
        f"成功:{result.get('success', False)}",
        request.remote_addr,
        "Web"
    )
    return jsonify(result)


@bp.route('/download')
@require_auth
def api_backup_download():
    """下载备份（仅管理员）"""
    if request.current_user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    # 速率限制：同一用户60秒内只能下载1次
    user_id = request.current_user['id']
    now = datetime.now().timestamp()
    if user_id in _backup_download_times:
        elapsed = now - _backup_download_times[user_id]
        if elapsed < 60:
            return jsonify({'error': f'下载过于频繁，请{int(60 - elapsed)}秒后重试'}), 429
    _backup_download_times[user_id] = now
    
    status = get_backup_status()
    if not status.get('last_backup'):
        return jsonify({'error': '没有备份'}), 404
    
    backups = []
    for item in os.listdir(BACKUP_DIR):
        if item.startswith('backup_'):
            item_path = os.path.join(BACKUP_DIR, item)
            complete_file = os.path.join(item_path, 'backup_complete.txt')
            if os.path.exists(complete_file):
                backups.append({'path': item_path, 'time': os.path.getmtime(item_path)})
    
    if not backups:
        return jsonify({'error': '没有备份'}), 404
    
    latest = max(backups, key=lambda x: x['time'])
    db_path = os.path.join(latest['path'], 'population.db')
    
    if os.path.exists(db_path):
        # 生成随机文件名防止路径遍历
        safe_name = f'backup_{secrets.token_hex(8)}.db'
        add_operation_log(
            request.current_user['id'],
            request.current_user['username'],
            "下载备份",
            f"文件:{os.path.basename(latest['path'])}",
            request.remote_addr,
            "Web"
        )
        return send_file(db_path, as_attachment=True, download_name=safe_name)
    
    return jsonify({'error': '备份文件不存在'}), 404


@bp.route('s')  # /api/backups
@require_auth
def api_backup_list():
    """获取备份列表（仅管理员）"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    backups = get_backup_list()
    return jsonify({'backups': backups})


@bp.route('/restore', methods=['POST'])
@require_auth
def api_backup_restore():
    """恢复备份（仅管理员）"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    backup_name = data.get('name', '')  # 使用备份名称而不是路径
    password = data.get('password', '')
    
    if not backup_name:
        return jsonify({'error': '缺少备份名称'}), 400
    
    # 安全检查：防止路径遍历攻击
    if '..' in backup_name or '/' in backup_name or '\\' in backup_name:
        return jsonify({'error': '无效的备份名称'}), 400
    
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    # 验证备份目录存在
    if not os.path.exists(backup_path):
        return jsonify({'error': '备份不存在'}), 404
    
    result = restore_database(backup_path, password if password else None)
    
    if result.get('success'):
        add_operation_log(
            user['id'],
            user['username'],
            "恢复备份",
            result.get('timestamp', ''),
            request.remote_addr,
            "Web"
        )
        return jsonify(result)
    else:
        return jsonify(result), 400
