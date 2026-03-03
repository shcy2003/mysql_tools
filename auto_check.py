#!/usr/bin/env python3
"""
定时验证脚本 - 每2分钟检查一次项目状态
"""
import time
import subprocess
import sys
from pathlib import Path

# 使用 Windows 路径
PROJECT_PATH = Path(r"D:\git\sql_tools\mysql_query_platform")
VENV_PYTHON = r"D:\git\sql_tools\venv\Scripts\python.exe"
CHECK_INTERVAL = 600  # 10分钟（秒）


def run_check():
    """运行一次检查"""
    print(f"\n{'='*80}")
    print(f"Running check at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    try:
        result = subprocess.run(
            [VENV_PYTHON, "check_project.py"],
            cwd=PROJECT_PATH,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        print(result.stdout)
        if result.stderr:
            print(f"[ERROR] {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Failed to run check: {e}")
        return False


def main():
    """主函数 - 定时检查"""
    print("\n" + "="*80)
    print("Auto Verification Started")
    print(f"Check interval: {CHECK_INTERVAL} seconds")
    print("Press Ctrl+C to stop")
    print("="*80 + "\n")

    check_count = 0

    try:
        while True:
            check_count += 1
            print(f"\n[Check #{check_count}]")
            run_check()

            print(f"\nWaiting {CHECK_INTERVAL} seconds until next check...")
            print("Press Ctrl+C to stop\n")

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n" + "="*80)
        print("Auto Verification Stopped")
        print(f"Total checks performed: {check_count}")
        print("="*80)
        sys.exit(0)


if __name__ == "__main__":
    main()
