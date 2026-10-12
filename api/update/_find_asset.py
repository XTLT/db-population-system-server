def _find_asset(release, app_type):
    """从发行版中查找对应的下载文件"""
    assets = release.get('assets', [])

    if app_type == 'mobile':
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.apk'):
                return asset
    elif app_type == 'desktop':
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
