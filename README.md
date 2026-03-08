# MySQL 查询平台

一个现代化的 MySQL 查询平台，支持 SQL 执行、数据脱敏、连接管理和查询历史记录。

## 功能特性

- 📊 **SQL 查询编辑器** - 提供语法高亮和智能提示的 SQL 编辑器
- 📈 **查询结果展示** - 表格展示查询结果，支持分页和导出
- 🎯 **数据脱敏** - 内置多种脱敏规则，保护敏感数据
- 🔌 **连接管理** - 支持管理多个 MySQL 连接
- 📜 **查询历史** - 完整的查询审计和历史记录
- 📱 **响应式 UI** - 适配桌面和移动设备
- 🚀 **高性能** - 连接池管理和查询优化

## 技术栈

- **后端**: Django 6.0 + Django REST Framework
- **前端**: Bootstrap 5 + jQuery
- **数据库**: SQLite (默认) 或 MySQL
- **API 文档**: Swagger UI (drf-yasg)

## 快速开始

### 1. 环境要求

- Python 3.10+
- MySQL 5.7+ (可选)
- pip 包管理器

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd mysql_query_platform

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑 .env 文件，配置数据库和其他参数
```

#### 环境变量说明

```env
# Django 配置
DJANGO_SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True

# 数据库配置（使用 SQLite 时可忽略下面的配置）
DJANGO_DB_ENGINE=django.db.backends.mysql
DJANGO_DB_NAME=mysql_query_platform
DJANGO_DB_USER=root
DJANGO_DB_PASSWORD=your_mysql_password
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=3306
DJANGO_DB_CHARSET=utf8mb4
```

### 4. 数据库初始化

```bash
# 数据库迁移（创建表结构）
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser
```

### 5. 启动开发服务器

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/

### 6. 访问 API 文档

http://127.0.0.1:8000/api-doc/

## 使用 Docker 部署

### 1. 使用 Docker Compose

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: mysql_query_platform
      MYSQL_ROOT_PASSWORD: root
      MYSQL_PASSWORD: root
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  web:
    build: .
    environment:
      DJANGO_SECRET_KEY: your-secret-key-here
      DJANGO_DB_ENGINE: django.db.backends.mysql
      DJANGO_DB_NAME: mysql_query_platform
      DJANGO_DB_USER: root
      DJANGO_DB_PASSWORD: root
      DJANGO_DB_HOST: db
      DJANGO_DB_PORT: 3306
    ports:
      - "8000:8000"
    depends_on:
      - db
    restart: always

volumes:
  mysql_data:
```

启动服务：

```bash
docker-compose up -d
```

### 2. 使用 Docker 单独构建

```bash
# 构建镜像
docker build -t mysql-query-platform .

# 运行容器（使用外部 MySQL）
docker run -d -p 8000:8000 \
  -e DJANGO_SECRET_KEY=your-secret-key \
  -e DJANGO_DB_ENGINE=django.db.backends.mysql \
  -e DJANGO_DB_NAME=mysql_query_platform \
  -e DJANGO_DB_USER=root \
  -e DJANGO_DB_PASSWORD=password \
  -e DJANGO_DB_HOST=your-mysql-host \
  -e DJANGO_DB_PORT=3306 \
  --name mysql-query-platform \
  mysql-query-platform
```

## 使用说明

### 1. 添加数据库连接

1. 登录系统（使用超级用户账号）
2. 点击 "连接管理"
3. 点击 "新建连接"
4. 填写连接信息：
   - 连接名称
   - 主机地址
   - 端口号（默认 3306）
   - 数据库名称
   - 用户名
   - 密码

### 2. 执行 SQL 查询

1. 从左侧连接树选择一个连接
2. 在 SQL 编辑器中输入查询语句
3. 点击 "执行" 按钮
4. 查看查询结果和执行时间

### 3. 配置脱敏规则

1. 点击 "脱敏规则"
2. 点击 "创建规则"
3. 填写规则信息：
   - 规则名称
   - 要脱敏的列名
   - 脱敏类型（完全脱敏、部分脱敏、正则匹配）
   - 脱敏参数

### 4. 查看查询历史

1. 点击 "查询历史"
2. 查看所有查询记录
3. 支持按时间、用户、连接进行筛选

## 部署到生产环境

### 1. 配置生产环境

```bash
# 使用生产配置
cp .env.example .env.production
# 编辑生产配置
```

### 2. 使用 Gunicorn 部署

```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:8000 mysql_query_platform.wsgi:application
```

### 3. 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /path/to/your/project/static/;
    }

    location /media/ {
        alias /path/to/your/project/media/;
    }
}
```

## 故障排除

### 1. 数据库连接失败

- 检查数据库服务是否启动
- 确认数据库配置是否正确
- 检查防火墙和网络连接

### 2. 页面无法访问

- 检查端口是否被占用
- 确认 Django 服务是否正常运行
- 查看服务器日志

### 3. 查询超时

- 优化 SQL 查询语句
- 增加数据库连接超时设置
- 检查数据库服务器负载

## 开发

### 1. 项目结构

```
mysql_query_platform/
├── mysql_query_platform/          # 项目配置
├── accounts/                      # 用户管理
├── connections/                   # 连接管理
├── queries/                       # 查询管理
├── desensitization/               # 脱敏规则
├── audit/                         # 审计日志
├── apidoc/                        # API 文档
├── monitoring/                    # 监控
├── static/                        # 静态文件
├── templates/                     # 模板文件
├── manage.py                      # 管理命令
├── requirements.txt               # 依赖包
├── Dockerfile                     # Docker 镜像
├── docker-compose.yml            # Docker Compose
└── init_mysql.sql                # 数据库初始化脚本
```

### 2. 开发命令

```bash
# 运行开发服务器
python manage.py runserver

# 运行测试
python manage.py test

# 数据库迁移
python manage.py makemigrations
python manage.py migrate

# 创建管理员用户
python manage.py createsuperuser
```

## 贡献

1. Fork 项目
2. 创建功能分支 (git checkout -b feature/AmazingFeature)
3. 提交更改 (git commit -m 'Add some AmazingFeature')
4. 推送到分支 (git push origin feature/AmazingFeature)
5. 打开 Pull Request

## 许可证

MIT License

## 支持

如有问题或建议，欢迎通过以下方式联系：

- 提交 Issue
- 发送邮件

---

**注意**: 生产环境部署时，请确保：
- 更改默认的 `DJANGO_SECRET_KEY`
- 禁用 DEBUG 模式
- 配置合适的数据库连接
- 使用 HTTPS 协议
