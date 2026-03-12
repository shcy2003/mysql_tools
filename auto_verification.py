#!/usr/bin/env python3
"""
自动验证脚本 - 定期检查项目状态并生成验证报告
"""
import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_PATH = Path("/mnt/d/git/sql_tools/mysql_query_platform")
REPORT_PATH = PROJECT_PATH / "verification_report.json"
VENV_PYTHON = "/mnt/d/git/sql_tools/venv/Scripts/python.exe" if os.name == 'nt' else "/mnt/d/git/sql_tools/venv/bin/python"


def run_command(cmd, cwd=None):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)


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
        "desensitization": "desensitization/models.pykt",
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
            content = filepath_full.read_text()
            # 简单检查是否有视图函数
            has_views = "def " in content and "request" in content
            status[app] = {
                "exists": True,
                "has_views": has_views,
                "size": len(content)
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
        # 检查全局模板目录和 app 模板目录
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
            migration_files = list(migrations_dir.glob("*.py"))
            # 排除 __init__.py
            actual_migrations = [f for f in migration_files if f.name != "__init__.py"]
            migrations_status[app] = {
                "exists": True,
                "count": len(actual_migrations),
                "files": [f.name for f in actual_migrations]
            }
        else:
            migrations_status[app] = {
                "exists": False,
                "count": 0,
                "files": []
            }
    return migrations_status


def check_dependencies():
    """检查依赖"""
    success, stdout, stderr = run_command(f"{VENV_PYTHON} -m pip list")
    if not success:
        return {}

    packages = {}
    for line in stdout.split('\n')[2:]:  # 跳过前两行
        parts = line.split()
        if len(parts) >= 2:
            packages[parts[0]] = parts[1]
    return packages


def check_code_quality():
    """检查代码质量问题"""
    issues = []

    # 检查 accounts/views.py 中的 get_client_ip
    accounts_views = PROJECT_PATH / "accounts/views.py"
    if accounts_views.exists():
        content = accounts_views.read_text()
        if "get_client_ip(request)" in content and "def get_client_ip" not in content:
            issues.append({
                "file": "accounts/views.py",
                "issue": "get_client_ip() 函数被调用但未定义",
                "severity": "high"
            })

    # 检查 queries/utils.py 中的参数错误
    queries_utils = PROJECT_PATH / "queries/utils.py"
    if queries_utils.exists():
        content = queries_utils.read_text()
        if "get_client_ip(connection)" in content:
            issues.append({
                "file": "queries/utils.py",
                "issue": "get_client_ip() 参数应该是 request 而不是 connection",
                "severity": "high"
            })

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
        "environment": {
            "dependencies": check_dependencies(),
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


def save_report(report):
    """保存报告到文件"""
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def format_report_for_display(report):
    """格式化报告用于显示"""
    output = []
    output.append("=" * 80)
    output.append(f"📊 MySQL 查询平台 - 自动验证报告")
    output.append(f"⏰ 生成时间: {report['timestamp']}")
    output.append("=" * 80)
    output.append("")

    # 环境检查
    output.append("## ✅ 环境检查")
    output.append(f"- Python 依赖包数量: {len(report['environment']['dependencies'])}")
    deps = report['environment']['dependencies']
    if 'Django' in deps:
        output.append(f"- Django 版本: {deps['Django']}")
    if 'mysqlclient' in deps:
        output.append(f"- mysqlclient 版本: {deps['mysqlclient']}")
    output.append("")

    # 目录结构
    output.append("## 📁 目录结构")
    summary = report['summary']
    output.append(f"- 完成: {summary['completed_dirs']}/{summary['total_dirs']} 个目录")
    for name, status in report['status']['directory_structure'].items():
        icon = "✅" if status['exists'] else "❌"
        output.append(f"  {icon} {name}")
    output.append("")

    # 模型
    output.append("## 📊 模型文件")
    output.append(f"- 完成: {summary['completed_models']}/{summary['total_models']} 个模型")
    for app, exists in report['status']['models'].items():
        icon = "✅" if exists else "❌"
        output.append(f"  {icon} {app}/models.py")
    output.append("")

    # 视图
    output.append("## 👁️  视图文件")
    for app, status in report['status']['views'].items():
        if status['exists']:
            icon = "✅" if status['has_views'] else "⚠️"
            has_views = "有视图" if status['has_views'] else "无视图函数"
            output.append(f"  {icon} {app}/views.py ({has_views}, {status['size']} 字节)")
        else:
            output.append(f"  ❌ {app}/views.py (不存在)")
    output.append("")

    # 模板
    output.append("## 📄 模板文件")
    output.append(f"- 完成: {summary['completed_templates']}/{summary['total_templates']} 个模板")
    for template, status in report['status']['templates'].items():
        icon = "✅" if status['global'] else "❌"
        output.append(f"  {icon} {template}")
    output.append("")

    # 迁移文件
    output.append("## 🔄 迁移文件")
    for app, status in report['status']['migrations'].items():
        if status['exists']:
            if status['count'] > 0:
                icon = "✅"
                output.append(f"  {icon} {app}/migrations/ ({status['count']} 个迁移文件)")
                for file in status['files']:
                    output.append(f"      - {file}")
            else:
                output.append(f"  ⚠️  {app}/migrations/ (目录存在但无迁移文件)")
        else:
            output.append(f"  ❌ {app}/migrations/ (不存在)")
    output.append("")

    # 代码问题
    output.append("## 🐛 发现的代码问题")
    if report['issues']:
        for issue in report['issues']:
            severity_icon = "🔴" if issue['severity'] == 'high' else "🟡"
            output.append(f"{severity_icon} {issue['file']}: {issue['issue']}")
    else:
        output.append("  ✅ 未发现明显问题")
    output.append("")

    # 总结
    output.append("=" * 80)
    output.append("## 📝 总结")
    output.append(f"  📁 目录结构: {summary['completed_dirs']}/{summary['total_dirs']}")
    output.append(f"  📊 模型文件: {summary['completed_models']}/{summary['total_models']}")
    output.append(f"  📄 模板文件: {summary['completed_templates']}/{summary['total_templates']}")
    output.append(f"  🐛 代码问题: {summary['total_issues']} 个")
    output.append("=" * 80)

    return "\n".join(output)


def main():
    """主函数"""
    print("🔍 开始检查项目状态...")

    report = generate_report()
    save_report(report)

    formatted = format_report_for_display(report)
    print(formatted)

    # 同时保存到 markdown 文件
    with open(PROJECT_PATH / "verification_report.md", 'w', encoding='utf-8') as f:
        f.write(formatted)

    print(f"\n✅ 报告已保存到: {REPORT_PATH}")
    print(f"✅ Markdown 报告已保存到: {PROJECT_PATH / 'verification_report.md'}")


if __name__ == "__main__":
    main()
