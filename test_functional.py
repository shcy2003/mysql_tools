#!/usr/bin/env python3
"""
功能测试脚本 - 测试 Django 项目的各项功能
"""
import urllib.request
import urllib.parse
import json
import sys

BASE_URL = "http://localhost:8000"

def test_url(url, method="GET", data=None, headers=None):
    """测试 URL"""
    full_url = f"{BASE_URL}{url}"
    try:
        if method == "POST" and data:
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            req = urllib.request.Request(full_url, data=encoded_data, method=method)
        else:
            req = urllib.request.Request(full_url, method=method)
        
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        response = urllib.request.urlopen(req, timeout=10)
        return {
            "status": response.status,
            "content": response.read().decode('utf-8', errors='ignore')[:500]
        }
    except urllib.error.HTTPError as e:
        return {
            "status": e.code,
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": -1,
            "error": str(e)
        }

def main():
    print("=" * 80)
    print("Django Project Functional Test")
    print("=" * 80)
    print()
    
    # 测试首页
    print("[1] Testing home page...")
    result = test_url("/")
    if result["status"] == 200:
        print(f"    [OK] Home page accessible (200)")
    elif result["status"] == 302:
        print(f"    [OK] Home page redirects to login (302)")
    else:
        print(f"    [FAIL] Home page failed ({result['status']})")
    
    # 测试登录页
    print("[2] Testing login page...")
    result = test_url("/accounts/login/")
    if result["status"] == 200:
        print(f"    [OK] Login page accessible (200)")
    else:
        print(f"    [FAIL] Login page failed ({result['status']})")
    
    # 测试管理员后台
    print("[3] Testing admin panel...")
    result = test_url("/admin/")
    if result["status"] == 302:
        print(f"    [OK] Admin panel requires login (302)")
    elif result["status"] == 200:
        print(f"    [OK] Admin panel accessible (200)")
    else:
        print(f"    [FAIL] Admin panel failed ({result['status']})")

    # 测试连接管理
    print("[4] Testing connections...")
    result = test_url("/connections/")
    if result["status"] == 302:
        print(f"    [OK] Connections requires login (302)")
    elif result["status"] == 200:
        print(f"    [OK] Connections accessible (200)")
    else:
        print(f"    [FAIL] Connections failed ({result['status']})")

    # 测试查询功能
    print("[5] Testing queries...")
    result = test_url("/queries/")
    if result["status"] == 302:
        print(f"    [OK] Queries requires login (302)")
    elif result["status"] == 200:
        print(f"    [OK] Queries accessible (200)")
    else:
        print(f"    [FAIL] Queries failed ({result['status']})")
    
    print()
    print("=" * 80)
    print("Test completed")
    print("=" * 80)

if __name__ == "__main__":
    main()
