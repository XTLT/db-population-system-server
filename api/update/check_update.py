from flask import request, jsonify

from . import bp, RELEASE_REPOS, DEFAULT_RELEASE_TYPE
from ._check_local_package import get_local_package_meta
from ._fetch_releases import _fetch_releases
from ._find_asset import _find_asset, _asset_size
from ._parse_version import _parse_version

# 客户端从哪个版本起支持"服务器直连下载（mTLS）"：
# 更早的版本下载请求不带客户端证书，会被 stunnel 拒绝，必须走 Gitee 免证书外部 URL。
SERVER_DIRECT_MIN_CODE = {'mobile': 24, 'desktop': 28}


def _gitee_fallback(app_type, current_code, legacy_desktop=False):
    """备用源：Gitee releases。返回 jsonify 结果；找不到则返回 None。"""
    repo = RELEASE_REPOS.get(app_type, RELEASE_REPOS[DEFAULT_RELEASE_TYPE])
    releases = _fetch_releases(repo)
    if not releases:
        return None

    best_release = None
    best_code = 0
    best_version = '0.0.0'

    for release in releases:
        if release.get('prerelease', False):
            continue
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
    # 旧版桌面客户端（<13）仅支持 zip 解压更新；新版优先 .exe 安装包静默安装
    asset = _find_asset(best_release, app_type, legacy_desktop=legacy_desktop)

    result = {
        'has_update': has_update,
        'latest_version': best_version,
        'latest_code': best_code,
        'release_notes': best_release.get('body', best_release.get('name', '')),
    }

    if has_update and asset:
        result['download_url'] = asset.get('browser_download_url', '')
        result['is_external_url'] = True
        size = asset.get('size', 0) or 0
        if not size:
            size = _asset_size(asset.get('browser_download_url', ''))
        result['file_size'] = size

    return jsonify(result)


@bp.route('/check')
def check_update():
    app_type = request.args.get('type', 'mobile')
    current_code = request.args.get('version_code', 0, type=int)

    direct_supported = current_code >= SERVER_DIRECT_MIN_CODE.get(app_type, 0)

    # ============ 主源：服务器本地更新包（updates/<type>/） ============
    local_meta = get_local_package_meta(app_type)
    if local_meta:
        try:
            local_code = int(local_meta.get('version_code') or 0)
        except Exception:
            local_code = 0
        local_version = local_meta.get('latest_version', '0.0.0')
        if local_code > 0 and local_code > current_code:
            if direct_supported:
                return jsonify({
                    'has_update': True,
                    'latest_version': local_version,
                    'latest_code': local_code,
                    'release_notes': local_meta.get('release_notes', ''),
                    'download_url': f'/api/update/download?type={app_type}',
                    'is_external_url': False,
                    'file_size': int(local_meta.get('file_size') or 0),
                    'checksum': local_meta.get('sha256', ''),
                })
            # 旧版客户端（下载无 mTLS 证书）→ 改走 Gitee 免证书外部 URL
            legacy_result = _gitee_fallback(app_type, current_code,
                                            legacy_desktop=(app_type == 'desktop' and current_code < 13))
            if legacy_result is not None:
                return legacy_result
        return jsonify({'has_update': False})

    # ============ 备用源：Gitee releases（服务器本地无对应更新包时） ============
    result = _gitee_fallback(app_type, current_code,
                             legacy_desktop=(app_type == 'desktop' and current_code < 13))
    if result is not None:
        return result
    return jsonify({'error': '无法获取版本信息'}), 500
