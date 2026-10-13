import urllib.request


def _asset_size(url):
    """通过 HEAD 请求获取下载文件的真实大小（Gitee 的 releases API 不返回 size 字段）"""
    if not url:
        return 0
    try:
        req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'PopulationSystem/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return int(resp.headers.get('Content-Length', 0) or 0)
    except Exception:
        return 0


def _find_asset(release, app_type, legacy_desktop=False):
    """从发行版中查找对应的下载文件

    legacy_desktop=True 时（旧版桌面客户端，仅支持 zip 解压更新）只找 .zip；
    新版桌面客户端优先 .exe 安装包，找不到再回退 .zip。
    """
    assets = release.get('assets', [])

    if app_type == 'mobile':
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.apk'):
                return asset
    elif app_type == 'desktop':
        if legacy_desktop:
            for asset in assets:
                name = asset.get('name', '')
                if name.endswith('.zip') and ('人口通' in name or name.startswith('population_')):
                    return asset
            return None
        # 优先 .exe 安装包（可静默安装覆盖更新），找不到再回退 .zip
        for asset in assets:
            name = asset.get('name', '')
            if name.endswith('.exe') and ('人口通' in name or name.startswith('population_')):
                return asset
        for asset in assets:
            name = asset.get('name', '')
            if name.endswith('.zip') and ('人口通' in name or name.startswith('population_')):
                return asset
    else:
        for asset in assets:
            name = asset.get('name', '')
            if name.endswith('.zip') and ('服务器' in name or '服务' in name or name.startswith('population_server')):
                return asset

    return None
