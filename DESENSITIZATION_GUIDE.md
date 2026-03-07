# 脱敏规则配置指南

## 概述

本指南说明如何为单表查询和联表查询配置脱敏规则。

## 脱敏规则匹配模式

系统支持以下几种字段匹配模式：

### 1. 简单列名匹配（单表查询）
仅通过列名匹配，适用于单表查询。

**配置示例：**
- 列名：`email`
- 效果：匹配所有查询结果中的 `email` 列

### 2. 表名.列名 匹配（联表查询）
通过 `表名.列名` 格式匹配，适用于联表查询中需要区分不同表的同名字段。

**配置示例：**
- 列名：`users.email`
- 效果：仅匹配来自 `users` 表的 `email` 列

- 列名：`customers.email`
- 效果：仅匹配来自 `customers` 表的 `email` 列

### 3. 表别名.列名 匹配（联表查询）
通过 `表别名.列名` 格式匹配，适用于使用表别名的联表查询。

**配置示例：**
对于 SQL：`SELECT u.name, u.email FROM users u`
- 列名：`u.email`
- 效果：匹配别名为 `u` 的表的 `email` 列

### 4. 列别名匹配
通过列别名匹配，适用于查询中使用了列别名的情况。

**配置示例：**
对于 SQL：`SELECT email AS user_email FROM users`
- 列名：`user_email`
- 效果：匹配别名为 `user_email` 的列

## 使用示例

### 示例 1：单表查询脱敏

**SQL:**
```sql
SELECT id, name, email, phone FROM users
```

**脱敏规则配置：**
- 规则名称：用户手机号脱敏
- 列名列表：`["phone"]`
- 脱敏类型：部分脱敏
- 脱敏参数：`{"keep_first": 3, "keep_last": 4}`

**效果：**
| id | name | email | phone |
|----|------|-------|-------|
| 1 | 张三 | zhang@example.com | 138****5678 |

### 示例 2：联表查询 - 区分同名字段

**SQL:**
```sql
SELECT
    u.id,
    u.name,
    u.email AS user_email,
    c.name AS company_name,
    c.email AS company_email
FROM users u
JOIN companies c ON u.company_id = c.id
```

**脱敏规则配置：**

规则 1：用户邮箱脱敏
- 列名列表：`["u.email", "user_email"]`
- 脱敏类型：完全脱敏

规则 2：公司邮箱脱敏
- 列名列表：`["c.email", "company_email"]`
- 脱敏类型：部分脱敏
- 脱敏参数：`{"keep_first": 1, "keep_last": 0}`

**效果：**
| id | name | user_email | company_name | company_email |
|----|------|------------|--------------|---------------|
| 1 | 张三 | ********** | ABC公司 | c********** |

### 示例 3：复杂联表查询

**SQL:**
```sql
SELECT
    o.id,
    o.order_date,
    u.name AS customer_name,
    u.phone,
    p.product_name,
    p.price
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN products p ON o.product_id = p.id
```

**脱敏规则配置：**

规则：客户手机号脱敏
- 列名列表：`["u.phone", "phone", "users.phone"]`
- 脱敏类型：部分脱敏
- 脱敏参数：`{"keep_first": 3, "keep_last": 4}`

**说明：**
配置多个列名模式可以确保在不同查询场景下都能正确匹配：
- `u.phone` - 匹配使用表别名的查询
- `phone` - 匹配简单查询
- `users.phone` - 匹配使用完整表名的查询

## 最佳实践

1. **为联表查询配置多种模式**：
   同时配置 `表别名.列名`、`表名.列名` 和简单列名，提高匹配成功率

2. **使用列别名提高可读性**：
   在 SQL 中使用明确的列别名，并在脱敏规则中配置这些别名

3. **测试不同查询场景**：
   配置规则后，测试不同的查询方式确保脱敏生效

4. **优先使用表别名**：
   在联表查询中使用表别名可以让脱敏规则更清晰
