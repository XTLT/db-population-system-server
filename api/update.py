import os
import re
import json
import hashlib
import urllib.request
from flask import Blueprint, jsonify, request, send_file

from utils.security import require_auth

bp = Blueprint('update', __name__)

UPDATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'updates')

# Gitee仓库配置
GITEE_OWNER = 'tension0712'
GITEE_REPO = 'population-system'
GITEE_API_URL = f'https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/releases'

# 缓存配置
_cache = {'data': None, 'timestamp': 0}
CACHE_TTL = 300  # 5分钟缓存


def _parse_version_from_tag(tag_name):
    """从tag名称解析版本号，支持格式: v0.0.5, 0.0.5, V0.0.5"""
    match = re.search(r'v?(\d+)\.(\d+)\.(\d+)', tag_name, re.IGNORECASE)
    if match:
        major, minor, patch = match.groups()
        version_code = int(major) * 10000 + int(minor) * 100 + int(patch)
        version_str = f'{major}.{minor}.{patch}'
        return version_code, version_str
    return None, None


def _fetch_gitee_releases():
    """从Gitee获取发行版信息（带缓存）"""
    import time
    now = time.time()
    
    # 检查缓存
    if _cache['data'] and (now - _cache['timestamp']) < CACHE_TTL:
        return _cache['data']
    
    try:
        req = urllib.request.Request(
            GITEE_API_URL,
            headers={'User-Agent': 'PopulationSystem/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            _cache['data'] = data
            _cache['timestamp'] = now
            return data
    except Exception as e:
        print(f'获取Gitee发行版失败: {e}')
        return _cache['data'] or []


def _find_asset(release, app_type):
    """从发行版中查找对应的下载文件"""
    assets = release.get('assets', [])
    
    if app_type == 'mobile':
        # 优先查找 app-release.apk 或包含 apk 的文件
        for asset in assets:
            name = asset.get('name', '').lower()
            if 'app-release.apk' in name or (name.endswith('.apk') and 'population' in name):
                return asset
        # 降级查找任何apk文件
        for asset in assets:
            if asset.get('name', '').lower().endswith('.apk'):
                return asset
    else:
        # 桌面端查找exe
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe') and ('人口' in name or 'population' in name):
                return asset
        for asset in assets:
            if asset.get('name', '').lower().endswith('.exe'):
                return asset
    
    return None


@bp.route('/check')
@require_auth
def check_update():
    app_type = request.args.get('type', 'mobile')
    current_code = request.args.get('version_code', 0, type=int)

    # 从Gitee获取发行版
    releases = _fetch_gitee_releases()
    if not releases:
        return jsonify({'error': '无法获取版本信息'}), 500

    # 查找最新版本
    latest_release = None
    latest_code = 0
    latest_version = '0.0.0'
    use_release_id = False  # 是否使用发行版ID作为版本比较

    for release in releases:
        # 跳过预发布版本
        if release.get('prerelease', False):
            continue
        
        tag_name = release.get('tag_name', '')
        code, version = _parse_version_from_tag(tag_name)
        
        # 如果tag没有版本号，尝试从发行版名称解析
        if code is None:
            name = release.get('name', '')
            code, version = _parse_version_from_tag(name)
        
        # 如果还是没有，从body中查找版本信息
        if code is None:
            body = release.get('body', '')
            code, version = _parse_version_from_tag(body)
        
        # 如果仍然没有版本号，使用发行版ID
        if code is None:
            release_id = release.get('id', 0)
            if release_id > latest_code:
                latest_code = release_id
                latest_version = f'build.{release_id}'
                latest_release = release
                use_release_id = True
        else:
            if code > latest_code:
                latest_code = code
                latest_version = version
                latest_release = release
                use_release_id = False

    if not latest_release:
        return jsonify({'error': '未找到有效发行版'}), 404

    has_update = latest_code > current_code

    result = {
        'has_update': has_update,
        'latest_version': latest_version,
        'latest_code': latest_code,
        'release_notes': latest_release.get('body', latest_release.get('name', '')),
    }

    if has_update:
        # 查找下载文件
        asset = _find_asset(latest_release, app_type)
        if asset:
            result['download_url'] = asset.get('browser_download_url', '')
            result['is_external_url'] = True  # 标记为外部URL
            # Gitee API不直接提供文件大小，设为0让客户端不显示
            result['file_size'] = 0

    return jsonify(result)


@bp.route('/download')
@require_auth
def download_update():
    """本地下载（保留兼容性）"""
    app_type = request.args.get('type', 'mobile')

    if app_type == 'mobile':
        filepath = os.path.join(UPDATES_DIR, 'population-query.apk')
        download_name = 'population-query.apk'
    else:
        filepath = os.path.join(UPDATES_DIR, 'population-query.exe')
        download_name = 'population-query.exe'

    if not os.path.exists(filepath):
        return jsonify({'error': '更新文件不存在，请从Gitee下载'}), 404

    from database import add_operation_log
    user = request.current_user
    add_operation_log(
        user['id'], user['username'],
        "下载更新", f"类型:{app_type}",
        request.remote_addr, "App"
    )

    return send_file(filepath, as_attachment=True, download_name=download_name)
