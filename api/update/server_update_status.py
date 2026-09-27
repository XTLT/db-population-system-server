import os
import subprocess
from flask import request, jsonify

from utils.security import require_auth
from . import bp, _DEPLOY_LOG


@bp.route('/server_status')
@require_auth
def server_update_status():
    """查询服务器当前git版本和最近更新日志"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403

    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = os.path.dirname(server_dir)

    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, cwd=project_dir, timeout=5
        )
        current_commit = result.stdout.strip()
    except Exception:
        current_commit = 'unknown'

    log_tail = ''
    if os.path.exists(_DEPLOY_LOG):
        try:
            with open(_DEPLOY_LOG, 'r') as f:
                lines = f.readlines()
                log_tail = ''.join(lines[-10:])
        except Exception:
            pass

    return jsonify({
        'current_commit': current_commit,
        'deploy_log': log_tail,
    })
