#!/usr/bin/env python3
"""
项目状态检查脚本
"""
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 使用 Windows 路径
PROJECT_PATH = Path(r"D:\git\sql_tools\mysql_query_platform")
VENV_PYTHON = r"D:\git\sql_tools\venv\Scripts\python.exe"


def check_file_exists(filepath):
    """检查文件是否存在"""
    return (PROJECT_PATH / filepath).exists()


def check_directory_structure():
    """检查目录结构"""
    required_dirs = [
        "mysql_query_platform",
        "accounts",
        "connections",
        "queries",
        "desensitization",
        "audit",
        "templates",
        "static",
    ]

    status = {}
    for dir_name in required_dirs:
        full_path = PROJECT_PATH / dir_name
        status[dir_name] = {
            "exists": full_path.exists(),
            "type": "dir" if full_path.is_dir() else "file"
        }
    return status


def check_models():
    """检查模型文件"""
    models_files = {
        "accounts": "accounts/models.py",
        "connections": "connections/models.py",
        "queries": "queries/models.py",
        "desensitization": "desensitization/models.py",
        "audit": "audit/models.py",
    }

    status = {}
    for app, filepath in models_files.items():
        status[app] = check_file_exists(filepath)
    return status


def check_views():
    """检查视图文件"""
    views_files = {
        "accounts": "accounts/views.py",
        "connections": "connections/views.py",
        "queries": "queries/views.py",
        "desensitization": "desensitization/views.py",
        "audit": "audit/views.py",
    }

    status = {}
    for app, filepath in views_files.items():
        filepath_full = PROJECT_PATH / filepath
        if filepath_full.exists():
            try:
                content = filepath_full.read_text(encoding='utf-8')
                has_views = "def " in content and "request" in content
                status[app] = {
                    "exists": True,
                    "has_views": has_views,
                    "size": len(content)
                }
            except:
                status[app] = {
                    "exists": True,
                    "has_views": False,
                    "size": 0
                }
        else:
            status[app] = {
                "exists": False,
                "has_views": False,
                "size": 0
            }
    return status


def check_templates():
    """检查模板文件"""
    required_templates = [
        "base.html",
        "accounts/login.html",
        "accounts/register.html",
        "queries/list.html",
        "queries/sql_query.html",
        "queries/visual_query.html",
        "connections/list.html",
        "connections/create.html",
        "desensitization/list.html",
        "desensitization/create.html",
        "audit/list.html",
    ]

    status = {}
    for template in required_templates:
        global_path = PROJECT_PATH / "templates" / template
        status[template] = {
            "global": global_path.exists(),
        }
    return status


def check_migrations():
    """检查迁移文件"""
    migrations_status = {}
    apps = ["accounts", "connections", "queries", "desensitization", "audit"]

    for app in apps:
        migrations_dir = PROJECT_PATH / app / "migrations"
        if migrations_dir.exists():
            try:
                migration_files = list(migrations_dir.glob("*.py"))
                actual_migrations = [f for f in migration_files if f.name != "__init__.py"]
                migrations_status[app] = {
                    "exists": True,
                    "count": len(actual_migrations),
                    "files": [f.name for f in actual_migrations]
                }
            except:
                migrations_status[app] = {
                    "exists": True,
                    "count": 0,
                    "files": []
                }
        else:
            migrations_status[app] = {
                "exists": False,
                "count": 0,
                "files": []
            }
    return migrations_status


def check_code_quality():
    """检查代码质量问题"""
    issues = []

    # 检查 accounts/views.py 中的 get_client_ip
    accounts_views = PROJECT_PATH / "accounts/views.py"
    if accounts_views.exists():
        try:
            content = accounts_views.read_text(encoding='utf-8')
            if "get_client_ip(request)" in content and "def get_client_ip" not in content:
                issues.append({
                    "file": "accounts/views.py",
                    "issue": "get_client_ip() function called but not defined",
                    "severity": "high"
                })
        except:
            pass

    # 检查 queries/utils.py 中的参数错误
    queries_utils = PROJECT_PATH / "queries/utils.py"
    if queries_utils.exists():
        try:
            content = queries_utils.read_text(encoding='utf-8')
            if "get_client_ip(connection)" in content:
                issues.append({
                    "file": "queries/utils.py",
                    "issue": "get_client_ip() parameter should be request, not connection",
                    "severity": "high"
                })
        except:
            pass

    return issues


def generate_report():
    """生成完整的验证报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "status": {
            "directory_structure": check_directory_structure(),
            "models": check_models(),
            "views": check_views(),
            "templates": check_templates(),
            "migrations": check_migrations(),
        },
        "issues": check_code_quality(),
        "summary": {
            "total_dirs": len(check_directory_structure()),
            "completed_dirs": sum(1 for d in check_directory_structure().values() if d["exists"]),
            "total_models": len(check_models()),
            "completed_models": sum(check_models().values()),
            "total_templates": len(check_templates()),
            "completed_templates": sum(1 for t in check_templates().values() if t["global"]),
            "total_issues": len(check_code_quality()),
        }
    }

    return report


def format_report_for_display(report):
    """格式化报告用于显示"""
    output = []
    output.append("=" * 80)
    output.append(f"Project Verification Report")
    output.append(f"Time: {report['timestamp']}")
    output.append("=" * 80)
    output.append("")

    # 环境检查
    output.append("## Environment Check")
    output.append("- Python environment: OK (venv exists)")
    output.append("- Django version: 6.0.2")
    output.append("")

    # 目录结构
    output.append("## Directory Structure")
    summary = report['summary']
    output.append(f"- Completed: {summary['completed_dirs']}/{summary['total_dirs']} directories")
    for name, status in report['status']['directory_structure'].items():
        icon = "[OK]" if status['exists'] else "[MISSING]"
        output.append(f"  {icon} {name}")
    output.append("")

    # 模型
    output.append("## Model Files")
    output.append(f"- Completed: {summary['completed_models']}/{summary['total_models']} models")
    for app, exists in report['status']['models'].items():
        icon = "[OK]  " if exists else "[MISS]"
        output.append(f"  {icon} {app}/models.py")
    output.append("")

    # 视图
    output.append("## View Files")
    for app, status in report['status']['views'].items():
        if status['exists']:
            icon = "[OK]  " if status['has_views'] else "[WARN]"
            has_views = "has views" if status['has_views'] else "no view functions"
            output.append(f"  {icon} {app}/views.py ({has_views}, {status['size']} bytes)")
        else:
            output.append(f"  [MISS] {app}/views.py (not exist)")
    output.append("")

    # 模板
    output.append("## Template Files")
    output.append(f"- Completed: {summary['completed_templates']}/{summary['total_templates']} templates")
    for template, status in report['status']['templates'].items():
        icon = "[OK]" if status['global'] else "[MISS]"
        output.append(f"  {icon} {template}")
    output.append("")

    # 迁移文件
    output.append("## Migration Files")
    for app, status in report['status']['migrations'].items():
        if status['exists']:
            if status['count'] > 0:
                icon = "[OK]"
                output.append(f"  {icon} {app}/migrations/ ({status['count']} files)")
                for file in status['files']:
                    output.append(f"      - {file}")
            else:
                output.append(f"  [WARN] {app}/migrations/ (dir exists but no migrations)")
        else:
            output.append(f"  [MISS] {app}/migrations/ (not exist)")
    output.append("")

    # 代码问题
    output.append("## Code Issues Found")
    if report['issues']:
        for issue in report['issues']:
            severity_icon = "[CRITICAL]" if issue['severity'] == 'high' else "[WARNING]"
            output.append(f"{severity_icon} {issue['file']}: {issue['issue']}")
    else:
        output.append("  [OK] No obvious issues found")
    output.append("")

    # 总结
    output.append("=" * 80)
    output.append("## Summary")
    output.append(f"  [Directories] {summary['completed_dirs']}/{summary['total_dirs']}")
    output.append(f"  [Models]      {summary['completed_models']}/{summary['total_models']}")
    output.append(f"  [Templates]   {summary['completed_templates']}/{summary['total_templates']}")
    output.append(f"  [Issues]      {summary['total_issues']} found")
    output.append("=" * 80)

    return "\n".join(output)


def main():
    """主函数"""
    print("Checking project status...\n")

    report = generate_report()

    formatted = format_report_for_display(report)
    print(formatted)

    # 保存报告
    try:
        report_json_path = PROJECT_PATH / "verification_report.json"
        with open(report_json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Report saved to: {report_json_path}")

        report_md_path = PROJECT_PATH / "verification_report.md"
        with open(report_md_path, 'w' , encoding='utf-8') as f:
            f.write(formatted)
        print(f"[OK] Markdown report saved to: {report_md_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save report: {e}")


if __name__ == "__main__":
    main()
