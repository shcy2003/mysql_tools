#!/usr/bin/env python3
"""
MySQL Query Platform API 自动化测试运行脚本
"""
import sys
import os
import subprocess

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests(test_file):
    """运行指定的测试文件"""
    print(f"\n{'='*60}")
    print(f"正在运行: {test_file}")
    print(f"{'='*60}")

    cmd = [sys.executable, "manage.py", "test", test_file, "-v", "2"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
        print(f"\n错误输出:\n{result.stderr}")

    return result.returncode == 0


def run_all_tests():
    """运行所有 API 测试"""
    print("MySQL Query Platform API 自动化测试")
    print("=" * 60)

    test_files = [
        "tests.test_api_full.HealthCheckAPITests",
        "tests.test_api_full.ConnectionsAPITests",
        "tests.test_api_full.QueriesAPITests",
        "tests.test_api_full.APIDocumentationTests",
        "tests.test_api_full.ParameterBoundaryTests",
        "tests.test_api_full.ErrorHandlingTests"
    ]

    all_passed = True

    for test_file in test_files:
        try:
            passed = run_tests(test_file)
            all_passed = all_passed and passed
        except Exception as e:
            print(f"执行测试时出错: {test_file} - {str(e)}")
            all_passed = False

    print("\n" + "=" * 60)
    print("测试结果")
    print("=" * 60)

    if all_passed:
        print("✅ 所有测试通过!")
        return True
    else:
        print("❌ 部分测试失败!")
        return False


if __name__ == "__main__":
    # 设置 Django 环境
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')

    # 运行测试
    success = run_all_tests()

    # 根据测试结果设置退出码
    sys.exit(0 if success else 1)
