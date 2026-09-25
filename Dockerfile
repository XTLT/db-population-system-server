# ========================================
# 多阶段构建 - 优化镜像大小
# ========================================

# 构建阶段
FROM python:3.11-slim as builder

# 设置工作目录
WORKDIR /build

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 创建虚拟环境并安装依赖
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ========================================
# 生产阶段
# ========================================
FROM python:3.11-slim

# 设置标签
LABEL maintainer="your-email@example.com"
LABEL version="1.0.0"
LABEL description="人口通 - Flask 后端"

# 创建非 root 用户
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 设置工作目录
WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制应用代码
COPY --chown=appuser:appuser . .

# 创建必要的目录
RUN mkdir -p /app/data /app/uploads /app/logs /app/backups /app/certs \
    && chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

# 环境变量
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 启动命令
CMD ["gunicorn", "--config", "gunicorn_config.py", "web_app:app"]
