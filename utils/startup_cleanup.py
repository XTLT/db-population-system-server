"""启动时执行的一次性清理任务，防止服务器目录 / 数据库无限膨胀。

1. operation_logs 只保留最近 90 天（操作日志只增不删，长期积累会拖大数据库）。
2. updates/<type>/ 目录只保留 version.json 指向的当前包，删除历史版本包
   （每个包 20-55MB，发布脚本遗漏清理时此处兜底，防止 updates 目录无限增长）。
3. 只清理历史冗余，绝不触碰任何业务数据（persons / 补贴 / 报表等）。

调用位置：app_modular.create_app 末尾（每次服务启动时执行一次）。
"""
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta

from config import DB_PATH, UPDATES_DIR

logger = logging.getLogger('population_system')


def cleanup_operation_logs(days: int = 90):
    """删除 days 天前的操作日志。created_at 为 '%Y-%m-%d %H:%M:%S' 字符串，可直接比较。"""
    try:
        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect(DB_PATH)
        try:
            cur = conn.execute(
                "DELETE FROM operation_logs WHERE created_at < ?", (cutoff,))
            deleted = cur.rowcount
            conn.commit()
        finally:
            conn.close()
        if deleted:
            logger.info(f"启动清理：删除超过 {days} 天的操作日志 {deleted} 条")
    except Exception as e:
        logger.warning(f"启动清理 operation_logs 失败: {e}")


def cleanup_old_update_packages():
    """updates/<type>/ 只保留 version.json 指向的当前包，删除其余历史包。"""
    try:
        for app_type in ('desktop', 'mobile', 'server'):
            d = os.path.join(UPDATES_DIR, app_type)
            meta_path = os.path.join(d, 'version.json')
            if not os.path.isdir(d) or not os.path.exists(meta_path):
                continue
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            keep = meta.get('file', '')
            removed = 0
            for fname in os.listdir(d):
                if fname == keep or fname == 'version.json':
                    continue
                p = os.path.join(d, fname)
                if os.path.isfile(p):
                    os.remove(p)
                    removed += 1
            if removed:
                logger.info(f"启动清理：updates/{app_type} 删除历史更新包 {removed} 个")
    except Exception as e:
        logger.warning(f"启动清理 updates 目录失败: {e}")


def run_startup_cleanup():
    cleanup_operation_logs(90)
    cleanup_old_update_packages()
