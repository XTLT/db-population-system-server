"""到龄提醒的进程内缓存与常量（多 worker 各自持有，仅用于减少重复扫描）。"""

import threading

MAX_LINES = 100

# (年, 月) -> 上次检查的 monotonic 时间戳；当月两组名单都已生成时记为永久
checked_months = {}
checked_lock = threading.Lock()
CACHE_TTL = 600
CACHE_FOREVER = float("inf")
