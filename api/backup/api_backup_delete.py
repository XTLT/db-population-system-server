import os
import shutil
from flask import request, jsonify

from database import add_operation_log
from utils.security import require_auth
from config import BACKUP_DIR
from . import bp


@bp.route('/delete', methods=['POST'])
@require_auth
def api_backup_delete():
    """删除备份（仅管理员）"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403

    data = request.get_json()
    backup_name = data.get('name', '')

    if not backup_name:
        return jsonify({'error': '缺少备份名称'}), 400

    # 安全检查：防止路径遍历攻击
    if '..' in backup_name or '/' in backup_name or '\\' in backup_name:
        return jsonify({'error': '无效的备份名称'}), 400

    backup_path = os.path.join(BACKUP_DIR, backup_name)

    if not os.path.exists(backup_path) or not os.path.isdir(backup_path):
        return jsonify({'error': '备份不存在'}), 404

    try:
        shutil.rmtree(backup_path)
        add_operation_log(
            user['id'],
            user['username'],
            "删除备份",
            backup_name,
            request.remote_addr,
            "APP"
        )
        return jsonify({'success': True, 'message': f'已删除备份: {backup_name}'})
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500
