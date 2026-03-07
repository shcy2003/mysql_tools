#!/usr/bin/env python3
"""
MySQL Query Platform - Simple Status Check
"""
import requests
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*60)
    print("  " + title)
    print("="*60)

def print_ok(message):
    print("  [OK] " + message)

def print_fail(message):
    print("  [FAIL] " + message)

def print_info(message):
    print("  [INFO] " + message)

def check_login_page():
    print_header("Check Login Page")
    try:
        response = requests.get(f"{BASE_URL}/accounts/login/")
        if response.status_code == 200:
            print_ok("Login page is accessible")
            content = response.text.lower()
            has_issue = False
            if 'navbar' in content:
                print_fail("Navigation bar found - should be hidden")
                has_issue = True
            else:
                print_ok("Navigation bar is hidden")
            if 'sidebar' in content:
                print_fail("Sidebar found - should be hidden")
                has_issue = True
            else:
                print_ok("Sidebar is hidden")
            return not has_issue
        else:
            print_fail(f"Login page not accessible, status code: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Login page check failed: {e}")
        return False

def check_endpoint(url, name, check_login=False):
    print_header(f"Check {name}")
    try:
        response = requests.get(url, allow_redirects=True)
        if check_login and 'accounts/login' in response.url:
            print_info("Requires login - this is normal")
            return True
        if response.status_code == 200:
            print_ok(f"{name} is accessible")
            return True
        else:
            print_fail(f"{name} not accessible, status code: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"{name} check failed: {e}")
        return False

def check_server():
    print_header("Check Server Status")
    try:
        response = requests.get(f"{BASE_URL}")
        if response.status_code in [200, 301, 302]:
            print_ok("Server is running")
            return True
        else:
            print_fail(f"Server response abnormal, status code: {response.status_code}")
            return False
    except Exception as e:
        print_fail(f"Unable to connect to server: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  MySQL Query Platform - Feature Verification")
    print("  Start Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    results = []

    results.append(check_server())
    results.append(check_login_page())
    results.append(check_endpoint(f"{BASE_URL}/", "Home Page", check_login=True))
    results.append(check_endpoint(f"{BASE_URL}/queries/sql/", "SQL Query Page", check_login=True))
    results.append(check_endpoint(f"{BASE_URL}/connections/", "Connection Page", check_login=True))

    print_header("Check API Endpoints")
    results.append(check_endpoint(f"{BASE_URL}/api/connections/tree/", "Connection Tree API"))
    results.append(check_endpoint(f"{BASE_URL}/api/queries/table_structure/", "Table Structure API"))

    print("\n" + "="*60)
    print("  Results Summary")
    print("="*60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed == 0:
        print("\n  All checks passed!")
    else:
        print(f"\n  {failed} check(s) failed, please investigate")

    print("\n" + "="*60 + "\n")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
