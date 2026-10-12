import json
import time
import urllib.request

from . import release_api_url, _cache, CACHE_TTL


def _fetch_releases(repo):
    """从GitHub获取指定仓库的发行版信息（按仓库分别带缓存）"""
    now = time.time()
    entry = _cache.get(repo)
    if entry and (now - entry['timestamp']) < CACHE_TTL:
        return entry['data']
    try:
        req = urllib.request.Request(
            release_api_url(repo),
            headers={'User-Agent': 'PopulationSystem/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            _cache[repo] = {'data': data, 'timestamp': now}
            return data
    except Exception as e:
        print(f'获取发行版信息失败({repo}): {e}')
        return (_cache.get(repo) or {}).get('data') or []
