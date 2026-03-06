import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # Check if column exists
    cursor.execute("PRAGMA table_info(queries_queryhistory)")
    columns = [column[1] for column in cursor.fetchall()]

    print(f"Current columns: {columns}")

    if 'execution_time' not in columns:
        print("Adding execution_time column...")
        cursor.execute("ALTER TABLE queries_queryhistory ADD COLUMN execution_time REAL")
        print("Column added successfully!")
    else:
        print("Column execution_time already exists!")
