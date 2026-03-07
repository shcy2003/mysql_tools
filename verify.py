#!/usr/bin/env python3
"""
MySQL Query Platform - Feature Verification Script
Quickly verify if main features are working correctly
"""
import requests
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def print_header(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def print_success(message):
    print(f"  ✅ {message}")

def print_error(message):
    print(f"  ❌ {message}")

def print_info(message):
    print(f"  ℹ️  {message}")

def check_login_page():
    print_header("Verify Login Page")
    try:
        response = requests.get(f"{BASE_URL}/accounts/login/")
        if response.status_code == 200:
            print_success("Login page is accessible")
            content = response.text.lower()
            if 'navbar' in content:
                print_error("Navigation bar found - should be hidden")
            else:
                print_success("Navigation bar is hidden")
            if 'sidebar' in content:
                print_error("Sidebar found - should be hidden")
            else:
                print_success("Sidebar is hidden")
            if 'login-card' in content or 'login-wrapper' in content:
                print_success("Login card exists")
            return True
        else:
            print_error(f"Login page not accessible, status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Login page verification failed: {e}")
        return False

def check_api_endpoint(url, name, expected_status=200, check_login=False):
    print_header(f"Verify {name}")
    try:
        response = requests.get(url, allow_redirects=True)
        if check_login and 'accounts/login' in response.url:
            print_info("Requires login - this is normal")
            return True
        if response.status_code == expected_status:
            print_success(f"{name} is accessible")
            return True
        else:
            print_error(f"{name} not accessible, status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"{name} verification failed: {e}")
        return False

def check_static_files():
    print_header("Verify Static Files")
    static_files = [
        ("/static/css/styles.css", "CSS File"),
        ("/static/js/main.js", "JavaScript File"),
    ]
    for path, name in static_files:
        try:
            response = requests.get(f"{BASE_URL}{path}")
            if response.status_code == 200:
                print_success(f"{name} is loaded successfully")
            else:
                print_error(f"{name} failed to load, status code: {response.status_code}")
        except Exception as e:
            print_error(f"{name} loading failed: {e}")

def check_server_status():
    print_header("Server Status Check")
    try:
        response = requests.get(f"{BASE_URL}")
        if response.status_code in [200, 301, 302]:
            print_success("Server is running")
            return True
        else:
            print_error(f"Server response abnormal, status code: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Unable to connect to server: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("  MySQL Query Platform - Feature Verification Tool")
    print("  Start Time: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)

    results = []

    results.append(check_server_status())
    results.append(check_login_page())
    results.append(check_api_endpoint(f"{BASE_URL}/", "Home Page", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/queries/sql/", "SQL Query Page", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/connections/", "Connection Management Page", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/queries/history/", "Query History Page", check_login=True))
    results.append(check_api_endpoint(f"{BASE_URL}/desensitization/", "Desensitization Rules Page", check_login=True))

    print_header("API Endpoints Verification")

    results.append(check_api_endpoint(f"{BASE_URL}/api/connections/tree/", "Connection Tree API"))
    results.append(check_api_endpoint(f"{BASE_URL}/api/queries/table_structure/", "Table Structure API"))
    results.append(check_api_endpoint(f"{BASE_URL}/api/queries/export_excel/", "Export Excel API"))

    check_static_files()

    print("\n" + "="*60)
    print("  Verification Results Summary")
    print("="*60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n  Total: {total} items")
    print(f"  Passed: {passed} items")
    print(f"  Failed: {failed} items")

    if failed == 0:
        print("\n  🎉 All verifications passed!")
    else:
        print(f"\n  ⚠️  {failed} verification(s) failed, please check")

    print("\n" + "="*60 + "\n")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
