-- MySQL Query Platform - 数据库初始化脚本
-- 使用前请先创建数据库: CREATE DATABASE mysql_query_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 注意: 这些表会由 Django migrations 自动创建
-- 此文件仅提供数据库创建脚本和示例数据

-- 创建数据库（如果尚未创建）
-- 请手动执行:
-- CREATE DATABASE IF NOT EXISTS mysql_query_platform CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE mysql_query_platform;

-- 创建用户并授权（可选）
-- CREATE USER IF NOT EXISTS 'mqp_user'@'%' IDENTIFIED BY 'your_password';
-- GRANT ALL PRIVILEGES ON mysql_query_platform.* TO 'mqp_user'@'%';
-- FLUSH PRIVILEGES;

-- Django 将自动创建以下表:
-- - accounts_user (用户表)
-- - accounts_user_groups
-- - accounts_user_user_permissions
-- - connections_mysqlconnection (连接表)
-- - queries_queryhistory (查询历史表)
-- - desensitization_maskingrule (脱敏规则表)
-- - audit_auditlog (审计日志表)
-- - auth_group
-- - auth_group_permissions
-- - auth_permission
-- - django_admin_log
-- - django_content_type
-- - django_migrations
-- - django_session

-- 示例: 创建默认管理员用户（通过 Django createsuperuser 命令创建更好）
-- 请使用: python manage.py createsuperuser

SET FOREIGN_KEY_CHECKS = 1;
