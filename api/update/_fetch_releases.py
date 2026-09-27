import json
import time
import urllib.request

from . import GITHUB_API_URL, _cache, CACHE_TTL


def _fetch_releases():
    """从GitHub获取发行版信息（带缓存）"""
    now = time.time()
    if _cache['data'] and (now - _cache['timestamp']) < CACHE_TTL:
        return _cache['data']
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={'User-Agent': 'PopulationSystem/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            _cache['data'] = data
            _cache['timestamp'] = now
            return data
    except Exception as e:
        print(f'获取GitHub发行版失败: {e}')
        return _cache['data'] or []
