# ========================================
# Gunicorn 配置文件
# ========================================

import os
import multiprocessing

# 服务器绑定
bind = os.getenv('BIND_ADDRESS', '0.0.0.0:5000')

# 工作进程数（推荐：CPU核心数 * 2 + 1）
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))

# 每个工作进程的线程数
threads = int(os.getenv('THREADS', 2))

# 工作模式
worker_class = 'sync'  # 或 'gevent' 用于异步

# 超时时间
timeout = 120

# 保持连接时间
keepalive = 5

# 最大请求数（防止内存泄漏）
max_requests = 1000
max_requests_jitter = 50

# 预加载应用
preload_app = True

# 守护进程
daemon = False

# 进程 ID 文件
pidfile = '/tmp/gunicorn.pid'

# 日志配置
accesslog = '/app/logs/access.log'
errorlog = '/app/logs/error.log'
loglevel = os.getenv('LOG_LEVEL', 'info')

# 访问日志格式
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# 安全相关
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# 性能调优
worker_connections = 1000
backlog = 2048

# 优雅重启超时
graceful_timeout = 30

# 捕获输出
capture_output = True

# 启用标准输出流
enable_stdio_inheritance = True

# 进程名称
proc_name = 'population-api'

# 当工作进程退出时的行为
def on_exit(server):
    """服务退出时的清理工作"""

def when_ready(server):
    """服务就绪时的初始化工作"""
    server.log.info("Server is ready. Listening on: %s", bind)

def pre_fork(server, worker):
    """Fork 前的准备工作"""

def post_fork(server, worker):
    """Fork 后的清理工作"""
