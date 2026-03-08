#!/usr/bin/env python
"""
数据迁移脚本 - 将 SQLite 数据迁移到 MySQL
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
        print(f"❌ SQLite 数据库文件不存在: {sqlite_path}")
        return None

    try:
        conn = sqlite3.connect(str(sqlite_path))
        conn.row_factory = sqlite3.Row
        print(f"✅ 成功连接到 SQLite 数据库: {sqlite_path}")
        return conn
    except Exception as e:
        print(f"❌ 无法连接到 SQLite 数据库: {e}")
        return None


def connect_mysql():
    """连接 MySQL 数据库"""
    config = get_mysql_config()
    try:
        conn = mysql.connector.connect(**config)
        print(f"✅ 成功连接到 MySQL 数据库: {config['database']}")
        return conn
    except Exception as e:
        print(f"❌ 无法连接到 MySQL 数据库: {e}")
        return None


def list_sqlite_tables(sqlite_conn):
    """列出 SQLite 中的所有表"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith('sqlite_')]
    print(f"SQLite 表数量: {len(tables)}")
    for table in sorted(tables):
        print(f"  - {table}")
    return tables


def get_table_columns(sqlite_conn, table_name):
    """获取表的列名"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row['name'] for row in cursor.fetchall()]
    return columns


def migrate_table_data(sqlite_conn, mysql_conn, table_name):
    """迁移单个表的数据"""
    print(f"\n正在迁移表: {table_name}")

    sqlite_cursor = sqlite_conn.cursor()
    mysql_cursor = mysql_conn.cursor(dictionary=True)

    # 获取表的列
    columns = get_table_columns(sqlite_conn, table_name)

    # 获取 SQLite 数据
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    sqlite_rows = sqlite_cursor.fetchall()

    if not sqlite_rows:
        print(f"  表 {table_name} 中没有数据，跳过")
        return True

    print(f"  发现 {len(sqlite_rows)} 条记录")

    # 准备插入语句
    placeholders = ", ".join(["%s"] * len(columns))
    insert_sql = f"INSERT INTO `{table_name}` ({', '.join(f'`{c}`' for c in columns)}) VALUES ({placeholders})"

    # 处理数据类型
    processed_rows = []
    for row in sqlite_rows:
        processed_row = []
        for col in columns:
            value = row[col]

            # 处理空值
            if value is None:
                processed_row.append(None)
                continue

            # 处理二进制数据
            if isinstance(value, bytes):
                processed_row.append(value.decode('utf-8', errors='ignore'))
                continue

            # 处理日期时间
            if isinstance(value, str):
                # 尝试解析日期时间格式
                if len(value) > 10 and value[4] == '-' and value[7] == '-':
                    try:
                        # 处理日期时间字符串
                        processed_row.append(value)
                    except:
                        processed_row.append(value)
                else:
                    processed_row.append(value)
            else:
                processed_row.append(value)

        processed_rows.append(processed_row)

    # 执行插入
    try:
        mysql_cursor.executemany(insert_sql, processed_rows)
        mysql_conn.commit()
        print(f"  ✅ 成功迁移 {len(processed_rows)} 条记录")
        return True
    except Exception as e:
        print(f"  ❌ 迁移失败: {e}")
        mysql_conn.rollback()

        # 尝试逐条插入以找出问题
        print("  尝试逐条插入以定位问题...")
        error_count = 0
        successful_count = 0

        for i, row in enumerate(processed_rows):
            try:
                mysql_cursor.execute(insert_sql, row)
                successful_count += 1
                if successful_count % 100 == 0:
                    print(f"    已成功插入 {successful_count} 条")
            except Exception as e2:
                print(f"    第 {i+1} 条记录插入失败: {e2}")
                print(f"    数据: {row}")
                error_count += 1

        mysql_conn.commit()
        print(f"  ✅ 部分成功: {successful_count} 条插入，{error_count} 条失败")

        return error_count == 0
    finally:
        mysql_cursor.close()


def main():
    """主函数"""
    print("=" * 50)
    print("数据迁移工具 - SQLite 到 MySQL")
    print("=" * 50)

    # 加载环境变量
    load_env_file()

    # 连接数据库
    sqlite_conn = connect_sqlite()
    if not sqlite_conn:
        return False

    mysql_conn = connect_mysql()
    if not mysql_conn:
        return False

    # 获取表信息
    tables = list_sqlite_tables(sqlite_conn)

    # 重要：需要根据依赖关系调整迁移顺序
    # 1. 基础认证和内容类型表
    # 2. 用户表
    # 3. 其他表
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

    # 找到剩余的表
    remaining_tables = [t for t in tables if t not in ordered_tables]
    ordered_tables.extend(sorted(remaining_tables))

    # 迁移数据
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
            print(f"❌ 表 {table_name} 迁移过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            failure_count += 1

    # 完成
    print(f"\n{'='*50}")
    print(f"迁移结果:")
    print(f"  成功: {success_count} 个表")
    print(f"  失败: {failure_count} 个表")

    if failure_count == 0:
        print(f"✅ 所有数据迁移完成！")
    else:
        print(f"⚠️  部分数据迁移失败，请检查错误信息")

    return failure_count == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
