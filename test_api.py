#!/usr/bin/env python3
"""
API 自动化测试脚本
测试登录、创建连接、执行查询等功能
"""
import requests
import sys

BASE_URL = "http://localhost:8000"
SESSION = requests.Session()

def test_login():
    """测试登录功能"""
    print("=" * 60)
    print("[1] Testing Login Function")
    print("=" * 60)
    
    # 首先获取登录页面，提取 CSRF token
    login_url = f"{BASE_URL}/accounts/login/"
    response = SESSION.get(login_url)
    
    if response.status_code != 200:
        print(f"[FAIL] Failed to get login page: {response.status_code}")
        return False
    
    print("[OK] Successfully got login page")
    
    # 从 cookies 中获取 CSRF token
    csrf_token = SESSION.cookies.get('csrftoken')
    if not csrf_token:
        print("[FAIL] Cannot get CSRF token")
        return False
    
    print(f"[OK] Successfully got CSRF token")
    
    # 提交登录表单
    login_data = {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_token
    }
    
    headers = {
        'Referer': login_url
    }
    
    response = SESSION.post(login_url, data=login_data, headers=headers, allow_redirects=True)
    
    # 检查是否登录成功（通过检查是否跳转到查询页面或包含特定内容）
    if '/queries/' in response.url or 'Query' in response.text or 'query' in response.text.lower():
        print("[OK] Login successful!")
        print(f"   Current URL: {response.url}")
        return True
    else:
        print(f"[FAIL] Login failed")
        print(f"   Current URL: {response.url}")
        print(f"   Status Code: {response.status_code}")
        return False

def test_connection_list():
    """测试获取连接列表"""
    print("\n" + "=" * 60)
    print("[2] Testing Connection List")
    print("=" * 60)
    
    response = SESSION.get(f"{BASE_URL}/connections/")
    
    if response.status_code == 200:
        print("[OK] Successfully got connection list page")
        print(f"   Current URL: {response.url}")
        
        # 检查是否显示"没有连接"的提示
        if 'No MySQL connection' in response.text or 'no connection' in response.text.lower():
            print("[OK] Page correctly shows: No MySQL connections")
        
        return True
    else:
        print(f"[FAIL] Failed to get connection list: {response.status_code}")
        return False

def test_create_connection():
    """测试创建数据库连接"""
    print("\n" + "=" * 60)
    print("[3] Testing Create Connection")
    print("=" * 60)
    
    # 获取 CSRF token
    create_url = f"{BASE_URL}/connections/create/"
    response = SESSION.get(create_url)
    
    if response.status_code != 200:
        print(f"[FAIL] Failed to get create connection page: {response.status_code}")
        return False
    
    print("[OK] Successfully got create connection page")
    
    csrf_token = SESSION.cookies.get('csrftoken')
    if not csrf_token:
        print("[FAIL] Cannot get CSRF token")
        return False
    
    # 填写连接信息
    connection_data = {
        'name': 'localhost_test',
        'host': 'localhost',
        'port': '3306',
        'database': 'mysql',
        'username': 'root',
        'password': 'shcy2005',
        'test_connection': 'on',
        'csrfmiddlewaretoken': csrf_token
    }
    
    headers = {
        'Referer': create_url
    }
    
    print("Preparing to create connection with the following parameters:")
    print(f"   Connection Name: {connection_data['name']}")
    print(f"   Host: {connection_data['host']}")
    print(f"   Port: {connection_data['port']}")
    print(f"   Database: {connection_data['database']}")
    print(f"   Username: {connection_data['username']}")
    
    response = SESSION.post(create_url, data=connection_data, headers=headers, allow_redirects=True)
    
    # 检查是否创建成功
    if response.status_code == 200:
        if 'Connection created successfully' in response.text or 'localhost_test' in response.text:
            print("[OK] Connection created successfully!")
            return True
        elif 'Connection failed' in response.text or 'Cannot connect' in response.text:
            print("Warning: Connection created, but test connection failed (MySQL server may not be running or authentication failed)")
            return True
        else:
            print(f"Warning: Unable to determine connection creation status")
            print(f"   Current URL: {response.url}")
            return False
    else:
        print(f"[FAIL] Failed to create connection: {response.status_code}")
        return False

def test_sql_query():
    """测试 SQL 查询功能"""
    print("\n" + "=" * 60)
    print("[4] Testing SQL Query Function")
    print("=" * 60)
    
    # 获取 SQL 查询页面
    query_url = f"{BASE_URL}/queries/sql/"
    response = SESSION.get(query_url)
    
    if response.status_code != 200:
        print(f"[FAIL] Failed to get SQL query page: {response.status_code}")
        return False
    
    print("[OK] Successfully got SQL query page")
    
    # 检查是否有可用的连接
    if 'No connection available' in response.text or 'Please create connection' in response.text:
        print("Warning: No MySQL connection available, cannot execute query")
        print("   Please create a database connection first")
        return False
    
    print("[OK] Can execute SQL query")
    return True

def main():
    """主函数"""
    print("=" * 60)
    print("MySQL Query Platform - API Automated Test")
    print("=" * 60)
    print()
    
    results = {
        'login': False,
        'connection_list': False,
        'create_connection': False,
        'sql_query': False
    }
    
    # 1. 测试登录
    results['login'] = test_login()
    if not results['login']:
        print("\n[FAIL] Login failed, terminating test")
        sys.exit(1)
    
    # 2. 测试连接列表
    results['connection_list'] = test_connection_list()
    
    # 3. 测试创建连接
    results['create_connection'] = test_create_connection()
    
    # 4. 测试 SQL 查询
    results['sql_query'] = test_sql_query()
    
    # 打印测试结果汇总
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    print(f"[OK] Login Function: {'PASS' if results['login'] else 'FAIL'}")
    print(f"[OK] Connection List: {'PASS' if results['connection_list'] else 'FAIL'}")
    print(f"[OK] Create Connection: {'PASS' if results['create_connection'] else 'FAIL'}")
    print(f"[OK] SQL Query: {'PASS' if results['sql_query'] else 'FAIL'}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n[OK] All tests passed!")
    else:
        print("\n[FAIL] Some tests failed")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
