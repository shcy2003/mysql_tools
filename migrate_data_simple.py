#!/usr/bin/env python
"""
数据迁移脚本 - 将 SQLite 数据迁移到 MySQL (简化版，避免编码问题)
"""

import os
import sys
import sqlite3
import mysql.connector
from pathlib import Path
from datetime import datetime


def load_env_file():
    """加载 .env 文件"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    os.environ[key] = value


def get_mysql_config():
    """获取 MySQL 配置"""
    return {
        'host': os.environ.get('DJANGO_DB_HOST', 'localhost'),
        'port': int(os.environ.get('DJANGO_DB_PORT', '3306')),
        'user': os.environ.get('DJANGO_DB_USER', 'root'),
        'password': os.environ.get('DJANGO_DB_PASSWORD', ''),
        'database': os.environ.get('DJANGO_DB_NAME', 'mysql_query_platform'),
        'charset': os.environ.get('DJANGO_DB_CHARSET', 'utf8mb4'),
    }


def get_sqlite_path():
    """获取 SQLite 数据库路径"""
    return Path(__file__).parent / 'db.sqlite3'


def connect_sqlite():
    """连接 SQLite 数据库"""
    sqlite_path = get_sqlite_path()
    if not sqlite_path.exists():
        print("Error: SQLite database file not found: %s" % sqlite_path)
        return None

    try:
        conn = sqlite3.connect(str(sqlite_path))
        conn.row_factory = sqlite3.Row
        print("Success: Connected to SQLite database: %s" % sqlite_path)
        return conn
    except Exception as e:
        print("Error: Cannot connect to SQLite database: %s" % e)
        return None


def connect_mysql():
    """连接 MySQL 数据库"""
    config = get_mysql_config()
    try:
        conn = mysql.connector.connect(**config)
        print("Success: Connected to MySQL database: %s" % config['database'])
        return conn
    except Exception as e:
        print("Error: Cannot connect to MySQL database: %s" % e)
        return None


def list_sqlite_tables(sqlite_conn):
    """列出 SQLite 中的所有表"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    print("SQLite table count: %d" % len(tables))
    for table in sorted(tables):
        print("  - %s" % table)
    return tables


def get_table_columns(sqlite_conn, table_name):
    """获取表的列名"""
    cursor = sqlite_conn.cursor()
    cursor.execute("PRAGMA table_info(%s)" % table_name)
    columns = [row['name'] for row in cursor.fetchall()]
    return columns


def migrate_table_data(sqlite_conn, mysql_conn, table_name):
    """迁移单个表的数据"""
    print("\nMigrating table: %s" % table_name)

    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor(dictionary=True)

    # 获取表的列
    columns = get_table_columns(sqlite_conn, table_name)

    # 获取 SQLite 数据
    sqlite_cursor.execute("SELECT * FROM %s" % table_name)
    sqlite_rows = sqlite_cursor.fetchall()

    if not sqlite_rows:
        print("  Table %s is empty, skipping" % table_name)
        return True

    print("  Found %d records" % len(sqlite_rows))

    # 准备插入语句
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = "INSERT INTO `%s` (%s) VALUES (%s)" % (
        table_name,
        ", ".join("`%s`" % c for c in columns),
        placeholders
    )

    # 处理数据类型
    processed_rows = []
    for row in sqlite_rows:
        processed_row = []
        for col in columns:
            value = row[col]

            if value is None:
                processed_row.append(None)
                continue

            if isinstance(value, bytes):
                processed_row.append(value.decode('utf-8', errors='ignore'))
                continue

            if isinstance(value, str):
                processed_row.append(value)
            else:
                processed_row.append(value)

        processed_rows.append(processed_row)

    # 执行插入
    try:
        mysql_cursor.executemany(insert_sql, processed_rows)
        mysql_conn.commit()
        print("  Success: Migrated %d records" % len(processed_rows))
        return True
    except Exception as e:
        print("  Error: Migration failed: %s" % e)
        mysql_conn.rollback()

        print("  Trying to insert records one by one...")
        error_count = 0
        successful_count = 0

        for i, row in enumerate(processed_rows):
            try:
                mysql_cursor.execute(insert_sql, row)
                successful_count += 1
                if successful_count % 100 == 0:
                    print("    Inserted %d records" % successful_count)
            except Exception as e2:
                print("    Error inserting record %d: %s" % (i+1, e2))
                print("    Data: %s" % row)
                error_count += 1

        mysql_conn.commit()
        print("  Partial success: %d inserted, %d failed" % (successful_count, error_count))

        return error_count == 0
    finally:
        mysql_cursor.close()


def main():
    """主函数"""
    print("=" * 50)
    print("Data Migration Tool - SQLite to MySQL")
    print("=" * 50)

    load_env_file()

    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return False

    mysql_conn = connect_mysql()
    if not mysql_conn:
        return False

    tables = list_sqlite_tables(sqlite_conn)

    ordered_tables = [
        'django_migrations',
        'django_content_type',
        'auth_permission',
        'auth_group',
        'auth_group_permissions',
        'accounts_user',
        'auth_user_groups',
        'auth_user_user_permissions',
        'django_session',
        'connections_mysqlconnection',
        'desensitization_maskingrule',
        'queries_queryhistory',
        'audit_auditlog',
        'django_admin_log',
    ]

    remaining_tables = [t for t in tables if t not in ordered_tables]
    ordered_tables.extend(sorted(remaining_tables))

    success_count = 0
    failure_count = 0

    for table_name in ordered_tables:
        if table_name not in tables:
            continue

        try:
            if migrate_table_data(sqlite_conn, mysql_conn, table_name):
                success_count += 1
            else:
                failure_count += 1
        except Exception as e:
            print("Error: Migration error for table %s: %s" % (table_name, e))
            import traceback
            traceback.print_exc()
            failure_count += 1

    print("\n" + "="*50)
    print("Migration Results:")
    print("  Success: %d tables" % success_count)
    print("  Failed: %d tables" % failure_count)

    if failure_count == 0:
        print("Success: All data migrated!")
    else:
        print("Warning: Some data migration failed, please check error messages")

    return failure_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
