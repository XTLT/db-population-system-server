"""备用源：Gitee releases。找不到返回 None。"""

from flask import jsonify

from .. import RELEASE_REPOS, DEFAULT_RELEASE_TYPE
from .._fetch_releases import _fetch_releases
from .._find_asset import _find_asset, _asset_size
from .._parse_version import _parse_version


def gitee_fallback(app_type, current_code, legacy_desktop=False):
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
