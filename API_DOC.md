# MySQL 查询平台 API 文档

## 基础信息

- **Base URL**: `http://127.0.0.1:8000`
- **认证方式**: Session 认证 (登录后使用 session cookie)
- **响应格式**: JSON

### 通用响应格式

```json
{
    "code": 0,
    "message": "success",
    "data": {}
}
```

### 状态码说明

| code | 说明 |
|------|------|
| 0 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 页面列表

### 公开页面（无需登录）

| URL | 说明 | 方法 |
|-----|------|------|
| `/accounts/login/` | 登录页面 | GET |
| `/accounts/login/` | 登录提交 | POST |

### 需要登录的页面

| URL | 说明 |
|-----|------|
| `/` | 首页（重定向到 /queries/） |
| `/queries/` | 查询列表（首页） |
| `/queries/sql/` | SQL 查询页面 |
| `/queries/sql/new/` | SQL 查询（新界面） |
| `/queries/history/` | 查询历史 |
| `/connections/` | 连接管理列表 |
| `/connections/create/` | 创建连接 |
| `/connections/edit/<id>/` | 编辑连接 |
| `/connections/delete/<id>/` | 删除连接 |
| `/connections/test/<id>/` | 测试连接 |
| `/audit/` | 审计日志（仅管理员） |
| `/desensitization/` | 脱敏规则列表（仅管理员） |
| `/desensitization/create/` | 创建脱敏规则 |
| `/desensitization/edit/<id>/` | 编辑脱敏规则 |
| `/desensitization/delete/<id>/` | 删除脱敏规则 |
| `/accounts/profile/` | 用户个人信息 |

---

## API 接口

### 1. 连接管理 API

#### 1.1 获取连接树

```
GET /api/connections/tree/
```

**认证**: 需要登录

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": [
        {
            "id": 1,
            "name": "本地MySQL",
            "host": "localhost",
            "port": 3306,
            "databases": [
                {
                    "name": "test_db",
                    "tables": ["users", "orders"]
                }
            ]
        }
    ]
}
```

---

#### 1.2 获取数据库列表

```
GET /api/connections/<connection_id>/databases/
```

**认证**: 需要登录

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| connection_id | int | 是 | 连接 ID |

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": ["information_schema", "mysql", "test_db"]
}
```

---

#### 1.3 获取表列表

```
GET /api/connections/<connection_id>/tables/?database=<database_name>
```

**认证**: 需要登录

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| connection_id | int | 是 | 连接 ID |
| database | string | 是 | 数据库名称 |

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": ["users", "orders", "products"]
}
```

---

### 2. 查询 API

#### 2.1 通用数据查询

```
GET /api/queries/data/
```

或

```
POST /api/queries/data/
```

**认证**: 需要登录

**GET 参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| connection_id | int | 是 | 连接 ID |
| database | string | 是 | 数据库名称 |
| table | string | 是 | 表名 |
| columns | string | 否 | 列名（逗号分隔），默认 * |
| page | int | 否 | 页码，默认 1 |
| page_size | int | 否 | 每页大小，默认 20 |
| sort_column | string | 否 | 排序列名 |
| sort_order | string | 否 | 排序方向 asc/desc |

**POST 请求体**:
```json
{
    "connection_id": 1,
    "database": "test_db",
    "table": "users",
    "columns": "id,name,email",
    "page": 1,
    "page_size": 20,
    "filters": [
        {"column": "age", "operator": ">=", "value": 18}
    ],
    "filter_logic": "AND"
}
```

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "list": [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com"}
        ],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 100,
            "total_pages": 5
        }
    }
}
```

**筛选操作符**:
| 操作符 | 说明 | 示例 |
|--------|------|------|
| eq | 等于 | {"column": "status", "operator": "eq", "value": "active"} |
| neq | 不等于 | {"column": "status", "operator": "neq", "value": "deleted"} |
| gt | 大于 | {"column": "age", "operator": "gt", "value": 18} |
| gte | 大于等于 | {"column": "age", "operator": "gte", "value": 18} |
| lt | 小于 | {"column": "age", "operator": "lt", "value": 65} |
| lte | 小于等于 | {"column": "age", "operator": "lte", "value": 65} |
| contains | 包含 | {"column": "name", "operator": "contains", "value": "张"} |
| startswith | 开头是 | {"column": "email", "operator": "startswith", "value": "test"} |
| endswith | 结尾是 | {"column": "email", "operator": "endswith", "value": ".com"} |
| in | 在列表中 | {"column": "status", "operator": "in", "value": ["active", "pending"]} |

---

#### 2.2 执行 SQL 查询

```
POST /api/queries/execute/
```

**认证**: 需要登录

**请求体**:
```json
{
    "connection_id": 1,
    "sql": "SELECT * FROM users WHERE status = 'active' LIMIT 10"
}
```

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": {
        "columns": ["id", "name", "email", "status"],
        "rows": [
            {"id": 1, "name": "张三", "email": "zhangsan@example.com", "status": "active"}
        ],
        "row_count": 1,
        "execution_time_ms": 15.23,
        "limited": false
    }
}
```

**说明**:
- 只支持 SELECT 查询
- 如果查询没有 LIMIT，自动添加 LIMIT 10
- `limited` 字段表示是否自动添加了 LIMIT

---

#### 1.4 获取字段列表

```
GET /api/connections/<connection_id>/columns/?database=<database_name>&table=<table_name>
```

**认证**: 需要登录

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| connection_id | int | 是 | 连接 ID |
| database | string | 是 | 数据库名称 |
| table | string | 是 | 表名称 |

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": [
        {"name": "id", "type": "int", "nullable": "NO", "key": "PRI", "default": null, "extra": "auto_increment"},
        {"name": "username", "type": "varchar(50)", "nullable": "NO", "key": "", "default": null, "extra": ""}
    ]
}
```

---

#### 1.5 测试数据库连接

```
POST /api/connections/test/
```

**认证**: 需要登录

**请求体**:
```json
{
    "host": "localhost",
    "port": 3306,
    "username": "root",
    "password": "your_password"
}
```

**响应示例**:
```json
{
    "code": 0,
    "message": "连接成功",
    "data": {}
}
```

---

#### 2.3 获取表结构

```
GET /api/queries/table_structure/?connection_id=<id>&database=<db>&table=<table>
```

**认证**: 需要登录

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| connection_id | int | 是 | 连接 ID |
| database | string | 是 | 数据库名称 |
| table | string | 是 | 表名称 |

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": [
        {"Field": "id", "Type": "int", "Null": "NO", "Key": "PRI", "Default": null, "Extra": "auto_increment"}
    ]
}
```

---

#### 2.4 获取表行数

```
GET /api/queries/table_row_count/?connection_id=<id>&database=<db>&table=<table>
```

**认证**: 需要登录

**参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| connection_id | int | 是 | 连接 ID |
| database | string | 是 | 数据库名称 |
| table | string | 是 | 表名称 |

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": {"row_count": 1000}
}
```

---

#### 2.5 获取保存的查询

```
GET /api/queries/saved/
```

**认证**: 需要登录

**响应示例**:
```json
{
    "code": 0,
    "message": "success",
    "data": [
        {"id": 1, "name": "我的查询", "sql": "SELECT * FROM users", "connection_id": 1, "database": "test", "created_at": "2026-01-01 12:00:00"}
    ]
}
```

---

#### 2.6 导出 Excel

```
POST /api/queries/export_excel/
```

**认证**: 需要登录

**请求体**:
```json
{
    "connection_id": 1,
    "database": "test_db",
    "sql": "SELECT * FROM users LIMIT 1000"
}
```

**响应**: 返回 Excel 文件 (application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)

---

### 3. 健康检查 API

#### 3.1 所有连接健康状态

```
GET /api/health/
```

**认证**: 不需要

**响应示例**:
```json
{
    "timestamp": "2026-03-06T10:00:00",
    "connections": {
        "default": {
            "status": "healthy",
            "db_name": "default",
            "response_time_ms": 5.2,
            "error": null
        }
    },
    "overall_status": "healthy"
}
```

---

#### 3.2 数据库连接健康检查

```
GET /api/health/db/
```

**认证**: 不需要

**响应示例**:
```json
{
    "status": "healthy",
    "db_name": "default",
    "response_time_ms": 5.2,
    "timestamp": "2026-03-06T10:00:00",
    "error": null
}
```

---

#### 3.3 数据库统计信息

```
GET /api/health/db/stats/
```

**认证**: 不需要

**响应示例**:
```json
{
    "db_name": "default",
    "timestamp": "2026-03-06T10:00:00",
    "connection_info": {
        "vendor": "sqlite",
        "display_name": "Default",
        "host": "localhost",
        "port": "default",
        "database": "db.sqlite3",
        "user": "unknown",
        "engine": "sqlite3"
    },
    "health_status": {
        "status": "healthy",
        "db_name": "default",
        "response_time_ms": 3.1,
        "error": null
    }
}
```

---

## 测试账号

- **用户名**: testuser
- **密码**: testpass123
- **角色**: 管理员 (admin)

---

## 使用示例

### 使用 Python requests

```python
import requests

# 登录获取 session
session = requests.Session()
login_data = {
    'username': 'testuser',
    'password': 'testpass123'
}
session.post('http://127.0.0.1:8000/accounts/login/', data=login_data)

# 调用 API
response = session.get('http://127.0.0.1:8000/api/connections/tree/')
print(response.json())
```

### 使用 curl

```bash
# 登录
curl -c cookies.txt -d "username=testuser&password=testpass123" http://127.0.0.1:8000/accounts/login/

# 调用 API（需要带 cookie）
curl -b cookies.txt http://127.0.0.1:8000/api/connections/tree/
```