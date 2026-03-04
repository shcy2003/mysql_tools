"""
Page Health Check - P0 Emergency Task
Batch test all pages to find 500 errors
"""
import requests
import time
import sys
from datetime import datetime
from urllib.parse import urljoin

# Base URL
BASE_URL = "http://localhost:8000"

# URLs to test (based on urls.py analysis)
URLS_TO_TEST = [
    # Root and admin
    "/",
    "/admin/",
    "/admin/login/",
    
    # Accounts
    "/accounts/login/",
    "/accounts/logout/",
    "/accounts/register/",
    "/accounts/profile/",
    "/accounts/password_change/",
    
    # Connections
    "/connections/",
    "/connections/new/",
    
    # Queries
    "/queries/",
    "/queries/new/",
    
    # Audit
    "/audit/",
    "/audit/logs/",
    
    # Desensitization
    "/desensitization/",
    "/desensitization/rules/",
    
    # API Endpoints
    "/api/health/",
    "/api/health/db/",
    "/api/health/db/stats/",
    "/api/connections/",
    "/api/queries/",
]


def test_url(session, url):
    """Test a single URL and return result"""
    full_url = urljoin(BASE_URL, url)
    start_time = time.time()
    
    try:
        response = session.get(full_url, timeout=10, allow_redirects=True)
        elapsed = round((time.time() - start_time) * 1000, 2)
        
        result = {
            'url': url,
            'full_url': full_url,
            'status_code': response.status_code,
            'response_time_ms': elapsed,
            'is_500': response.status_code >= 500,
            'is_error': response.status_code >= 400 and response.status_code != 404,
            'error': None
        }
        
        return result
        
    except requests.exceptions.Timeout:
        return {
            'url': url,
            'full_url': full_url,
            'status_code': 'TIMEOUT',
            'response_time_ms': round((time.time() - start_time) * 1000, 2),
            'is_500': True,
            'is_error': True,
            'error': 'Request timeout'
        }
    except requests.exceptions.ConnectionError as e:
        return {
            'url': url,
            'full_url': full_url,
            'status_code': 'CONN_ERROR',
            'response_time_ms': 0,
            'is_500': True,
            'is_error': True,
            'error': f'Connection error: {str(e)}'
        }
    except Exception as e:
        return {
            'url': url,
            'full_url': full_url,
            'status_code': 'EXCEPTION',
            'response_time_ms': 0,
            'is_500': True,
            'is_error': True,
            'error': f'Exception: {str(e)}'
        }


def run_health_check():
    """Run the full health check and generate report"""
    print("=" * 80)
    print("PAGE HEALTH CHECK - P0 Emergency Task")
    print(f"Started at: {datetime.now().isoformat()}")
    print(f"Base URL: {BASE_URL}")
    print(f"Total URLs to test: {len(URLS_TO_TEST)}")
    print("=" * 80)
    
    session = requests.Session()
    results = []
    errors_500 = []
    errors_other = []
    
    # Test all URLs
    for i, url in enumerate(URLS_TO_TEST, 1):
        print(f"\n[{i}/{len(URLS_TO_TEST)}] Testing: {url}")
        result = test_url(session, url)
        results.append(result)
        
        print(f"  Status: {result['status_code']}")
        print(f"  Time: {result['response_time_ms']}ms")
        
        if result['is_500']:
            errors_500.append(result)
            print(f"  ⚠️  500 ERROR DETECTED!")
            if result['error']:
                print(f"  Error: {result['error']}")
        elif result['is_error']:
            errors_other.append(result)
            print(f"  ⚠️  Error (non-500)")
    
    # Generate report
    report = generate_report(results, errors_500, errors_other)
    
    # Save report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f'/home/kimi/.openclaw/workspace/reports/health_check_{timestamp}.md'
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print("\n" + "=" * 80)
    print("HEALTH CHECK COMPLETE")
    print(f"Report saved to: {report_path}")
    print("=" * 80)
    
    return results, errors_500, errors_other, report_path


def generate_report(results, errors_500, errors_other):
    """Generate markdown report"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total = len(results)
    success = sum(1 for r in results if not r['is_error'])
    success_rate = round((success / total) * 100, 2) if total > 0 else 0
    
    report = f"""# Page Health Check Report

**Generated:** {timestamp}
**Base URL:** {BASE_URL}
**Total URLs Tested:** {total}

## Summary

| Metric | Value |
|--------|-------|
| Total URLs | {total} |
| Successful | {success} |
| 500 Errors | {len(errors_500)} |
| Other Errors | {len(errors_other)} |
| Success Rate | {success_rate}% |
| Health Status | {'✅ HEALTHY' if len(errors_500) == 0 else '❌ UNHEALTHY'} |

## 500 Errors Detected

"""
    
    if errors_500:
        report += "| URL | Status | Time (ms) | Error |\n"
        report += "|-----|--------|-----------|-------|\n"
        for err in errors_500:
            error_msg = err.get('error', 'N/A')[:50] if err.get('error') else 'N/A'
            report += f"| {err['url']} | {err['status_code']} | {err['response_time_ms']} | {error_msg} |\n"
    else:
        report += "✅ No 500 errors detected!\n"
    
    report += "\n## Other Errors (4xx, etc.)\n\n"
    
    if errors_other:
        report += "| URL | Status | Time (ms) | Error |\n"
        report += "|-----|--------|-----------|-------|\n"
        for err in errors_other:
            error_msg = err.get('error', 'N/A')[:50] if err.get('error') else 'N/A'
            report += f"| {err['url']} | {err['status_code']} | {err['response_time_ms']} | {error_msg} |\n"
    else:
        report += "✅ No other errors detected!\n"
    
    report += """
## All Tested URLs

| URL | Status | Time (ms) | Result |
|-----|--------|-----------|--------|
"""
    
    for r in results:
        status_icon = '✅' if not r['is_error'] else '❌'
        report += f"| {r['url']} | {r['status_code']} | {r['response_time_ms']} | {status_icon} |\n"
    
    report += "\n---\n*Report generated by Page Health Check System*\n"
    
    return report


if __name__ == '__main__':
    run_health_check()
