import os
import subprocess
from flask import request, jsonify

from utils.security import require_auth
from . import bp, _DEPLOY_LOG


@bp.route('/server', methods=['POST'])
@require_auth
def update_server():
    """触发服务器代码更新：git pull + 清理pyc + 重启gunicorn"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '需要管理员权限'}), 403

    server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    project_dir = server_dir  # git 仓库即代码部署目录（拆分后仓库根=代码根）

    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--short', 'HEAD'],
            capture_output=True, text=True, cwd=project_dir, timeout=5
        )
        old_commit = result.stdout.strip()
    except Exception:
        old_commit = 'unknown'

    # 分离子进程：等待HTTP响应完成后再执行git pull + 重启
    # start_new_session=True 确保子进程在 gunicorn 重启后存活
    deploy_script = f'''#!/bin/bash
export TZ=Asia/Shanghai
sleep 2
echo "=== $(date) 开始更新 ===" > {_DEPLOY_LOG}
cd {project_dir}
# 拉取重试：官方直连不稳时自动切 ghproxy 镜像兜底（镜像域名如失效可更换）
pull_with_retry() {{
  for i in 1 2; do
    git pull origin master && return 0
    sleep 3
    git pull https://gh-proxy.com/https://github.com/XTLT/db-population-system-server.git master && return 0
    sleep 3
  done
  return 1
}}
pull_with_retry >> {_DEPLOY_LOG} 2>&1
git rev-parse --short HEAD >> {_DEPLOY_LOG} 2>&1
find . -name "*.pyc" -delete >> {_DEPLOY_LOG} 2>&1
find . -name "__pycache__" -type d -exec rm -rf {{}} + 2>/dev/null
systemctl restart population-server >> {_DEPLOY_LOG} 2>&1
echo "=== $(date) 更新完成 ===" >> {_DEPLOY_LOG}
'''

    subprocess.Popen(
        ['bash', '-c', deploy_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )

    return jsonify({
        'status': 'deploying',
        'old_commit': old_commit,
        'message': '服务器正在更新中，预计10-20秒后重启完成'
    })
