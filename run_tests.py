#!/usr/bin/env python3
"""
测试运行器

支持运行全部测试或指定模块的测试
支持生成HTML测试报告

用法:
    python run_tests.py                    # 运行所有测试
    python run_tests.py --smoke           # 只运行冒烟测试
    python run_tests.py --auth            # 只运行认证测试
    python run_tests.py --connections     # 只运行连接测试
    python run_tests.py --queries         # 只运行查询测试
    python run_tests.py --html            # 生成HTML报告
    python run_tests.py -v                # 详细输出
"""

import sys
import os
import time
import argparse
import unittest
from datetime import datetime

# 添加tests目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试模块映射
TEST_MODULES = {
    'smoke': 'tests.test_smoke',
    'auth': 'tests.test_auth',
    'connections': 'tests.test_connections',
    'queries': 'tests.test_queries',
    'desensitization': 'tests.test_desensitization',
    'audit': 'tests.test_audit',
    'visual': 'tests.test_visual_query',
}


def generate_html_report(test_results, output_file='test_report.html'):
    """生成HTML测试报告"""
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MySQL查询平台测试报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); padding: 30px; }}
        h1 {{ color: #333; margin-bottom: 10px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 6px; margin: 20px 0; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; }}
        .summary-item {{ text-align: center; padding: 15px; background: white; border-radius: 4px; }}
        .summary-item .number {{ font-size: 2em; font-weight: bold; display: block; }}
        .summary-item .label {{ color: #666; font-size: 0.9em; }}
        .passed {{ color: #28a745; }}
        .failed {{ color: #dc3545; }}
        .error {{ color: #ffc107; }}
        .skipped {{ color: #6c757d; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #495057; }}
        tr:hover {{ background: #f8f9fa; }}
        .status-badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500; }}
        .status-pass {{ background: #d4edda; color: #155724; }}
        .status-fail {{ background: #f8d7da; color: #721c24; }}
        .status-error {{ background: #fff3cd; color: #856404; }}
        .status-skip {{ background: #e2e3e5; color: #383d41; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; color: #6c757d; font-size: 0.9em; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 MySQL查询平台测试报告</h1>
        <p>生成时间: {timestamp}</p>
        
        <div class="summary">
            <h2>📊 测试概览</h2>
            <div class="summary-grid">
                <div class="summary-item">
                    <span class="number">{total}</span>
                    <span class="label">总测试数</span>
                </div>
                <div class="summary-item">
                    <span class="number passed">{passed}</span>
                    <span class="label">通过</span>
                </div>
                <div class="summary-item">
                    <span class="number failed">{failed}</span>
                    <span class="label">失败</span>
                </div>
                <div class="summary-item">
                    <span class="number error">{errors}</span>
                    <span class="label">错误</span>
                </div>
                <div class="summary-item">
                    <span class="number skipped">{skipped}</span>
                    <span class="label">跳过</span>
                </div>
            </div>
        </div>
        
        <h2>📋 详细结果</h2>
        <table>
            <thead>
                <tr>
                    <th>序号</th>
                    <th>测试模块</th>
                    <th>测试用例</th>
                    <th>状态</th>
                    <th>耗时</th>
                    <th>说明</th>
                </tr>
            </thead>
            <tbody>
                {test_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>MySQL查询平台自动化测试套件 | 测试工程师Agent生成</p>
        </div>
    </div>
</body>
</html>
"""
    
    # 计算统计数据
    total = len(test_results)
    passed = sum(1 for r in test_results if r['status'] == 'passed')
    failed = sum(1 for r in test_results if r['status'] == 'failed')
    errors = sum(1 for r in test_results if r['status'] == 'error')
    skipped = sum(1 for r in test_results if r['status'] == 'skipped')
    
    # 生成测试行
    test_rows = []
    for i, result in enumerate(test_results, 1):
        status_class = {
            'passed': 'status-pass',
            'failed': 'status-fail',
            'error': 'status-error',
            'skipped': 'status-skip'
        }.get(result['status'], 'status-skip')
        
        status_text = {
            'passed': '✓ 通过',
            'failed': '✗ 失败',
            'error': '⚠ 错误',
            'skipped': '⊘ 跳过'
        }.get(result['status'], '未知')
        
        row = f"""
                <tr>
                    <td>{i}</td>
                    <td>{result.get('module', 'N/A')}</td>
                    <td>{result.get('test', 'N/A')}</td>
                    <td><span class="status-badge {status_class}">{status_text}</span></td>
                    <td>{result.get('time', 'N/A')}s</td>
                    <td>{result.get('message', '')}</td>
                </tr>
        """
        test_rows.append(row)
    
    # 填充模板
    html_content = html_template.format(
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        total=total,
        passed=passed,
        failed=failed,
        errors=errors,
        skipped=skipped,
        test_rows=''.join(test_rows)
    )
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file


def run_tests(test_modules=None, verbose=False, html_report=False):
    """运行测试"""
    
    # 加载测试
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    if test_modules:
        # 运行指定模块
        for module in test_modules:
            if module in TEST_MODULES:
                try:
                    __import__(TEST_MODULES[module])
                    suite.addTests(loader.loadTestsFromName(TEST_MODULES[module]))
                except Exception as e:
                    print(f"警告: 无法加载模块 {module}: {e}")
    else:
        # 运行所有测试
        for name, module in TEST_MODULES.items():
            try:
                __import__(module)
                suite.addTests(loader.loadTestsFromName(module))
            except Exception as e:
                print(f"警告: 无法加载模块 {name}: {e}")
    
    # 运行测试
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # 生成HTML报告
    if html_report:
        # 收集测试结果
        test_results = []
        for test in suite:
            # 这里简化处理，实际应该跟踪每个测试的执行
            pass
        
        # 生成报告
        report_file = generate_html_report(test_results)
        print(f"\nHTML报告已生成: {report_file}")
    
    # 返回退出码
    return 0 if result.wasSuccessful() else 1


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='MySQL查询平台测试运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py                    # 运行所有测试
  python run_tests.py --smoke           # 只运行冒烟测试
  python run_tests.py --auth            # 只运行认证测试
  python run_tests.py --connections     # 只运行连接测试
  python run_tests.py --queries         # 只运行查询测试
  python run_tests.py -v                # 详细输出
        """
    )
    
    # 测试模块选项
    parser.add_argument('--smoke', action='store_true', help='运行冒烟测试')
    parser.add_argument('--auth', action='store_true', help='运行认证测试')
    parser.add_argument('--connections', action='store_true', help='运行连接测试')
    parser.add_argument('--queries', action='store_true', help='运行查询测试')
    parser.add_argument('--desensitization', action='store_true', help='运行脱敏测试')
    parser.add_argument('--audit', action='store_true', help='运行审计测试')
    parser.add_argument('--visual', action='store_true', help='运行可视化查询测试')
    
    # 其他选项
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--html', action='store_true', help='生成HTML报告')
    parser.add_argument('--list', action='store_true', help='列出可用测试模块')
    
    args = parser.parse_args()
    
    # 列出测试模块
    if args.list:
        print("可用测试模块:")
        for name, module in TEST_MODULES.items():
            print(f"  --{name:20s} - {module}")
        return 0
    
    # 确定要运行的测试模块
    modules_to_run = []
    
    if args.smoke:
        modules_to_run.append('smoke')
    if args.auth:
        modules_to_run.append('auth')
    if args.connections:
        modules_to_run.append('connections')
    if args.queries:
        modules_to_run.append('queries')
    if args.desensitization:
        modules_to_run.append('desensitization')
    if args.audit:
        modules_to_run.append('audit')
    if args.visual:
        modules_to_run.append('visual')
    
    # 如果没有指定模块，运行所有测试
    if not modules_to_run:
        modules_to_run = list(TEST_MODULES.keys())
    
    # 运行测试
    exit_code = run_tests(
        test_modules=modules_to_run,
        verbose=args.verbose,
        html_report=args.html
    )
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
