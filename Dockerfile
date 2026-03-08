FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# 安装系统依赖
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        default-mysql-client \
        gcc \
        libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 复制并安装 Python 依赖
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . /app/

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 创建数据库表（如果需要）
RUN python manage.py migrate

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "mysql_query_platform.wsgi:application"]
