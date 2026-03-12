#!/usr/bin/env python3
"""
Link Check Test - 使用 requests + session 测试所有链接访问
使用 Python requests 库模拟浏览器访问，并记录 Cookie 会话
"""
import requests
import os
from datetime import datetime

# 基础 URL
BASE_URL = "http://localhost:8000"

# 需要测试的 URL 列表
URLS_TO_TEST = [
    "/",
    "/accounts/login/",
    "/accounts/logout/",
    "/connections/",
    "/connections/create/",
    "/queries/",
    "/queries/sql/",
    "/queries/history/",
    "/desensitization/",
    "/desensitization/rules/",
    "/audit/",
    "/admin/",
]

# 登录凭证
USERNAME = "admin"
PASSWORD = "admin123"


def login_and_get_session():
    """登录并返回带有 Cookie 的 session"""
    session = requests.Session()
    
    # 首先访问登录页获取 CSRF token（如果有的话）
    login_url = f"{BASE_URL}/accounts/login/"
    resp = session.get(login_url)
    
    # 准备登录数据
    login_data = {
        'username': USERNAME,
        'password': PASSWORD,
    }
    
    # 提交登录
    resp = session.post(login_url, data=login_data, allow_redirects=True)
    
    # 检查是否登录成功（通过检查是否还在登录页面）
    if '/accounts/login/' in resp.url:
        print(f"⚠️ 登录可能失败，仍在登录页面")
    else:
        print(f"✅ 登录成功")
    
    return session


def check_url(session, url_path):
    """检查单个 URL 的访问状态"""
    full_url = f"{BASE_URL}{url_path}"
    
    try:
        resp = session.get(full_url, allow_redirects=True, timeout=10)
        status = resp.status_code
        final_url = resp.url
        
        # 判断成功：200 状态码，且没有重定向到登录页（除非是登录/登出页面本身）
        is_login_related = url_path in ['/accounts/login/', '/accounts/logout/']
        is_redirected_to_login = '/accounts/login/' in final_url and not is_login_related
        
        success = (status == 200) and not is_redirected_to_login
        
        note = ""
        if is_redirected_to_login:
            note = "需要登录"
        elif final_url != full_url:
            note = f"重定向到: {final_url.replace(BASE_URL, '')}"
        
        return {
            "url": url_path,
            "status": status,
            "success": success,
            "final_url": final_url.replace(BASE_URL, ''),
            "note": note
        }
        
    except Exception as e:
        return {
            "url": url_path,
            "status": 0,
            "success": False,
            "error": str(e),
            "note": f"异常: {str(e)[:50]}"
        }


def generate_report(results):
    """生成 Markdown 格式的测试报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    report = f"""# 链接访问测试报告

**测试时间**: {now}
**测试账号**: admin / admin123
**测试工具**: Python requests + Session

## 测试结果汇总

| 总链接数 | 通过 | 失败 | 通过率 |
|---------|------|------|--------|
| {total} | {passed} | {failed} | {pass_rate:.1f}% |

## 详细测试结果

| URL | 状态码 | 结果 | 备注 |
|-----|--------|------|------|
"""
    
    for r in results:
        url = r['url']
        status = r.get('status', 'N/A')
        success = '✅' if r['success'] else '❌'
        note = r.get('note', '')
        if 'error' in r:
            note = f"错误: {r['error'][:50]}"
        report += f"| {url} | {status} | {success} | {note} |\n"
    
    # 添加失败详情
    failed_results = [r for r in results if not r['success']]
    if failed_results:
        report += "\n## 失败链接详情\n\n"
        for r in failed_results:
            report += f"### {r['url']}\n"
            report += f"- 状态码: {r.get('status', 'N/A')}\n"
            if 'error' in r:
                report += f"- 错误信息: {r['error']}\n"
            if 'final_url' in r:
                report += f"- 最终URL: {r['final_url']}\n"
            report += "\n"
    
    return report


def main():
    """主函数"""
    print("=" * 60)
    print("链接访问测试 - Python requests + Session")
    print("=" * 60)
    
    # 登录获取 session
    print("\n[1/3] 登录获取 session...")
    session = login_and_get_session()
    
    # 测试所有 URL
    print(f"\n[2/3] 测试 {len(URLS_TO_TEST)} 个链接...")
    results = []
    for url_path in URLS_TO_TEST:
        print(f"  测试: {url_path}...", end=" ", flush=True)
        result = check_url(session, url_path)
        results.append(result)
        status = result.get('status', 'ERR')
        symbol = '✅' if result['success'] else '❌'
        print(f"{status} {symbol}")
    
    # 生成报告
    print("\n[3/3] 生成测试报告...")
    report = generate_report(results)
    
    # 保存报告
    shared_dir = "/home/kimi/.openclaw/workspace/agents/SHARED/test_reports"
    os.makedirs(shared_dir, exist_ok=True)
    
    report_path = os.path.join(shared_dir, "link_check_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    # 输出结果
    print("\n" + "=" * 60)
    total = len(results)
    passed = sum(1 for r in results if r['success'])
    print(f"测试结果: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    print(f"报告保存: {report_path}")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
