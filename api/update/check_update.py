from flask import request, jsonify

from . import bp, RELEASE_REPOS, DEFAULT_RELEASE_TYPE
from ._fetch_releases import _fetch_releases
from ._find_asset import _find_asset
from ._parse_version import _parse_version


@bp.route('/check')
def check_update():
    app_type = request.args.get('type', 'mobile')
    current_code = request.args.get('version_code', 0, type=int)

    # 按端选择对应的 release 仓库（mobile/desktop/server 各自独立仓库）
    repo = RELEASE_REPOS.get(app_type, RELEASE_REPOS[DEFAULT_RELEASE_TYPE])
    releases = _fetch_releases(repo)
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
    # 旧版桌面客户端（<13）仅支持 zip 解压更新；新版优先 .exe 安装包静默安装
    legacy_desktop = app_type == 'desktop' and current_code < 13
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
        result['file_size'] = asset.get('size', 0)

    return jsonify(result)
