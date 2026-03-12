# MySQL 查询平台 - 代码验证清单

## ✅ 环境检查（已完成）

- [x] Python 版本：3.14.0
- [x] Django 版本：6.0.2
- [x] 虚拟环境：/mnt/d/git/sql_tools/venv
- [x] 依赖包：
  - Django 6.0.2
  - mysqlclient 2.2.8
  - asgiref 3.11.1
  - sqlparse 0.5.5
  - tzdata 2025.3
- [x] requirements.txt 已生成

---

## ⚠️ 发现的潜在问题

### 1. 代码逻辑问题

#### `accounts/views.py` - login_view()
**问题**：`get_client_ip(request)` 在函数调用前未定义
```python
user.last_login_ip = get_client_ip(request)  # ❌ 未定义
```
**建议在哪里定义**：应该在视图文件顶部或单独的 utils.py 中定义

#### `queries/utils.py` - run_query()
**问题**：`get_client_ip(connection)` 参数类型错误
```python
create_audit_log(
    ...
    ip_address=get_client_ip(connection),  # ❌ 应该是 request，不是 connection
    ...
)
```
**应该改为**：`get_client_ip(request)`

---

### 2. 依赖问题

**缺失依赖**：代码中使用了 `mysql.connector`，但 requirements.txt 只有 `mysqlclient`
```python
import mysql.connector  # connections/utils.py
```
**建议**：添加 `mysql-connector-python` 到 requirements.txt

---

## 📋 待验证清单（等代码完成后）

### A. 数据库迁移
- [ ] 执行 `python manage.py makemigrations` - 检查是否有错误
- [ ] 执行 `python manage.py migrate` - 创建表
- [ ] ] 验证 db.sqlite3 是否创建
- [ ] 验证表结构：
  - [ ] accounts_user
  - [ ] connections_mysqlconnection
  - [ ] desensitization_maskingrule
  - [ ] queries_queryhistory
  - [ ] audit_auditlog

### B. 代码完整性检查
- [ ] 检查所有 views.py 是否完整（没有未完成的函数）
- [ ] 检查所有 forms.py 是否创建
- [ ] 检查所有模板文件是否创建：
  - [ ] accounts/login.html
  - [ ] accounts/register.html
  - [ ] base.html
  - [ ] queries/list.html
  - [ ] queries/sql_query.html
  - [ ] queries/visual_query.html
  - [ ] connections/list.html
  - [ ] connections/create.html
  - [ ] desensitization/list.html
  - [ ] desensitization/create.html
  - [ ] audit/list.html

### C. 安全性检查
- [ ] 验证 SQL 注入防护（查询是否使用参数化）
- [ ] 验证 CSRF 保护是否启用
- [ ] 验证登录装饰器是否应用到所有需要认证的视图
- [ ] 验证管理员权限检查是否正确

### D. 功能逻辑检查
- [ ] 脱敏规则测试：
  - [ ] 完全脱敏（full）
  - [ ] 部分脱敏（partial）
  - [ ] 正则匹配（regex）
- [ ] 查询功能测试：
  - [ ] SQL 文本查询
  - [ ] 可视化查询构建器
- [ ] 权限控制测试：
  - [ ] 普通用户只能查询
  - [ ] 管理员可以管理连接和脱敏规则
  - [ ] 管理员可以查看审计日志

### E. 边界情况测试
- [ ] 空查询结果
- [ ] 超长字段脱敏
- [ ] 无权限用户访问管理功能
- [ ] MySQL 连接失败处理
- [ ] SQL 语法错误处理

---

## 🐛 已知 Bug 列表

1. **`accounts/views.py`** - `get_client_ip()` 未定义
2. **`queries/utils.py`** - `get_client_ip(connection)` 参数错误

---

## 💡 建议修复

### 1. 添加 `get_client_ip()` 工具函数

在 `accounts/utils.py` 或项目根目录的 `utils.py` 中创建：

```python
def get_client_ip(request):
    """获取客户端 IP 地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

### 2. 修复 `queries/utils.py`

```python
# 将 run_query 函数的签名改为：
def run_query(connection, sql, user, request):
    # ...
    # 将 get_client_ip(connection) 改为：
    ip_address=get_client_ip(request)
```

---

## 📝 测试用例（需要真实 MySQL）

### 测试数据准备
```sql
-- 创建测试数据库
CREATE DATABASE test_db;

-- 创建测试表
CREATE TABLE test_db.users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    id_card VARCHAR(18)
);

-- 插入测试数据
INSERT INTO test_db.users (username, phone, email, id_card) VALUES
('user1', '13800138000', 'user1@example.com', '110101199001011234'),
('user2', '13900139000', 'user2@example.com', '110101199002025678');
```

### 测试场景

1. **用户认证测试**
   - 创建管理员用户
   - 创建普通用户
   - 测试登录/登出
   - 测试权限隔离

2. **连接管理测试**
   - 创建 MySQL 连接
   - 测试连接
   - 删除连接

3. **查询功能测试**
   - SQL 查询：`SELECT * FROM users`
   - 验证查询历史记录
   - 验证审计日志

4. **脱敏功能测试**
   - 创建脱敏规则：
     - phone 字段：部分脱敏（保留前3后4）
     - email 字段：正则匹配（@ 替换为 *）
   - 执行查询
   - 验证脱敏结果

---

生成时间：2026-03-02 21:00
