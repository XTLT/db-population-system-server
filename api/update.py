import re
import json
import time
import urllib.request
from flask import Blueprint, jsonify, request

from utils.security import require_auth

bp = Blueprint('update', __name__)

# Gitee仓库配置
GITEE_OWNER = 'tension0712'
GITEE_REPO = 'population-system'
GITEE_API_URL = f'https://gitee.com/api/v5/repos/{GITEE_OWNER}/{GITEE_REPO}/releases'

# 缓存
_cache = {'data': None, 'timestamp': 0}
CACHE_TTL = 300


def _fetch_gitee_releases():
    """从Gitee获取发行版信息（带缓存）"""
    now = time.time()
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
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.apk'):
                return asset
    else:
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe'):
                return asset

    return None


def _parse_version(tag_name):
    """从tag解析版本号"""
    match = re.search(r'v?(\d+)\.(\d+)\.(\d+)', tag_name, re.IGNORECASE)
    if match:
        major, minor, patch = match.groups()
        code = int(major) * 10000 + int(minor) * 100 + int(patch)
        return code, f'{major}.{minor}.{patch}'
    return None, None


@bp.route('/check')
@require_auth
def check_update():
    app_type = request.args.get('type', 'mobile')
    current_code = request.args.get('version_code', 0, type=int)

    releases = _fetch_gitee_releases()
    if not releases:
        return jsonify({'error': '无法获取版本信息'}), 500

    # 找到最新有对应类型文件的发行版
    best_release = None
    best_code = 0
    best_version = '0.0.0'

    for release in releases:
        if release.get('prerelease', False):
            continue

        # 检查该发行版是否有对应类型的文件
        asset = _find_asset(release, app_type)
        if not asset:
            continue

        tag_name = release.get('tag_name', '')
        code, version = _parse_version(tag_name)

        if code is None:
            name = release.get('name', '')
            code, version = _parse_version(name)

        if code is None:
            code = release.get('id', 0)
            version = f'build.{code}'

        if code > best_code:
            best_code = code
            best_version = version
            best_release = release

    if not best_release:
        return jsonify({'has_update': False})

    has_update = best_code > current_code
    asset = _find_asset(best_release, app_type)

    result = {
        'has_update': has_update,
        'latest_version': best_version,
        'latest_code': best_code,
        'release_notes': best_release.get('body', best_release.get('name', '')),
    }

    if has_update and asset:
        result['download_url'] = asset.get('browser_download_url', '')
        result['is_external_url'] = True
        result['file_size'] = asset.get('size', 0)

    return jsonify(result)
