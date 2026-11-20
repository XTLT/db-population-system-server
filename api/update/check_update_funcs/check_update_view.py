"""GET /api/update/check：检查更新（服务器本地包优先，Gitee 备用）。"""

from flask import request, jsonify

from .._check_local_package import get_local_package_meta
from .constants import SERVER_DIRECT_MIN_CODE
from .gitee_fallback import gitee_fallback


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
            legacy_result = gitee_fallback(app_type, current_code,
                                           legacy_desktop=(app_type == 'desktop' and current_code < 13))
            if legacy_result is not None:
                return legacy_result
        return jsonify({'has_update': False})

    # ============ 备用源：Gitee releases（服务器本地无对应更新包时） ============
    result = gitee_fallback(app_type, current_code,
                            legacy_desktop=(app_type == 'desktop' and current_code < 13))
    if result is not None:
        return result
    return jsonify({'error': '无法获取版本信息'}), 500
