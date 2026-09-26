import os
import json
import shutil
import secrets
import subprocess
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file

from database import add_operation_log
from utils.security import require_auth
from config import BACKUP_DIR, DB_PATH, PHOTOS_DIR, LOG_DIR
from excel_importer import backup_database, get_backup_status, get_backup_list, _decrypt_backup


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


@bp.route('/list')  # /api/backup/list
@require_auth
def api_backup_list():
    """获取备份列表（仅管理员）"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    backups = get_backup_list()
    return jsonify({'backups': backups})


@bp.route('/status')
@require_auth
def api_backup_status():
    """获取备份状态"""
    status = get_backup_status()
    return jsonify(status)


@bp.route('/restore', methods=['POST'])
@require_auth
def api_backup_restore():
    """恢复备份（仅管理员）— 分离子进程停止服务器后再复制DB，避免在线覆盖导致损坏"""
    user = request.current_user
    if user.get('role') != 'admin':
        return jsonify({'error': '权限不足'}), 403
    
    data = request.get_json()
    backup_name = data.get('name', '')
    password = data.get('password', '')
    
    if not backup_name:
        return jsonify({'error': '缺少备份名称'}), 400
    
    if '..' in backup_name or '/' in backup_name or '\\' in backup_name:
        return jsonify({'error': '无效的备份名称'}), 400
    
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    if not os.path.exists(backup_path):
        return jsonify({'error': '备份不存在'}), 404
    
    complete_file = os.path.join(backup_path, "backup_complete.txt")
    if not os.path.exists(complete_file):
        return jsonify({'error': '备份不完整'}), 400
    
    try:
        with open(complete_file, "r") as f:
            manifest = json.load(f)
    except Exception as e:
        return jsonify({'error': f'读取备份清单失败: {str(e)}'}), 500
    
    # 加密备份：在服务器停止前解密（需要Python cryptography库，stop后无法调用）
    encrypted = manifest.get("encrypted", False)
    if encrypted:
        if not password:
            return jsonify({'error': '需要解密密码'}), 400
        try:
            _decrypt_backup(backup_path, password)
        except Exception as e:
            return jsonify({'error': f'解密失败: {str(e)}'}), 400
    
    db_backup = os.path.join(backup_path, "population.db")
    if not os.path.exists(db_backup):
        return jsonify({'error': '数据库备份文件不存在'}), 400
    
    photos_backup = os.path.join(backup_path, "photos.tar.gz")
    
    add_operation_log(
        user['id'],
        user['username'],
        "恢复备份",
        manifest.get("timestamp", ""),
        request.remote_addr,
        "Web"
    )
    
    # 分离子进程：sleep 2让HTTP响应先返回 → 停止服务器 → 恢复DB → 重启
    # start_new_session=True 确保子进程在 gunicorn 停止/重启后存活
    restore_log = os.path.join(LOG_DIR, 'backup_restore.log')
    encrypted_flag = '1' if encrypted else '0'
    
    restore_script = f'''#!/bin/bash
export TZ=Asia/Shanghai
sleep 2
echo "=== $(date) 开始恢复备份: {backup_name} ===" > "{restore_log}"

systemctl stop population-server >> "{restore_log}" 2>&1
echo "服务器已停止" >> "{restore_log}"

if [ -f "{DB_PATH}" ]; then
    cp "{DB_PATH}" "{DB_PATH}.before_restore"
    echo "已备份当前数据库到 .before_restore" >> "{restore_log}"
fi

cp "{db_backup}" "{DB_PATH}"
echo "数据库已恢复" >> "{restore_log}"

if [ -f "{photos_backup}" ]; then
    rm -rf "{PHOTOS_DIR}"
    mkdir -p "{PHOTOS_DIR}"
    tar -xzf "{photos_backup}" -C "{PHOTOS_DIR}" --no-same-owner >> "{restore_log}" 2>&1
    echo "照片已恢复" >> "{restore_log}"
fi

if [ "{encrypted_flag}" = "1" ]; then
    rm -f "{backup_path}/population.db" "{backup_path}/photos.tar.gz"
    echo "已清理解密临时文件" >> "{restore_log}"
fi

systemctl start population-server >> "{restore_log}" 2>&1
echo "服务器已重启" >> "{restore_log}"
echo "=== $(date) 恢复完成 ===" >> "{restore_log}"
'''
    
    subprocess.Popen(
        ['bash', '-c', restore_script],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    
    return jsonify({
        'success': True,
        'message': '备份恢复中，服务器将自动重启',
        'timestamp': manifest.get('timestamp'),
        'restored_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })


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
