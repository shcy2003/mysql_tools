#!/usr/bin/env python
"""测试数据库连接"""

import mysql.connector

def test_connection():
    """测试连接"""
    try:
        connection_params = {
            'host': '127.0.0.1',
            'port': 3306,
            'user': 'root',
            'password': 'shcy2005',
            'database': 'test'
        }

        print("Connection params:")
        print(connection_params)

        pool_params = connection_params.copy()
        pool_params.pop('database', None)

        print("\nTrying to connect to MySQL...")
        db_conn = mysql.connector.connect(**pool_params)
        print("OK: Connected successfully!")

        # 列出数据库
        cursor = db_conn.cursor(dictionary=True)
        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        print(f"\nFound {len(databases)} databases:")
        for db in databases:
            print(f"  - {db['Database']}")

        cursor.close()
        db_conn.close()
        return True

    except Exception as e:
        print(f"\nERROR: Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_connection()
