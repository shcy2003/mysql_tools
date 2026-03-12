#!/bin/bash
# Linux/Mac 脚本 - 每2分钟检查一次项目状态

cd /mnt/d/git/sql_tools/mysql_query_platform

echo "================================================================================"
echo "Auto Verification Started"
echo "Check interval: 10 minutes"
echo "Press Ctrl+C to stop"
echo "================================================================================"
echo ""

while true; do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running check..."
    /mnt/d/git/sql_tools/venv/bin/python check_project.py
    echo ""
    echo "Waiting 2 minutes until next check..."
    echo "Press Ctrl+C to stop"
    echo ""

    sleep 600
done
