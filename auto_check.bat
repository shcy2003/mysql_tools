@echo off
REM Windows 批处理脚本 - 每2分钟检查一次项目状态

cd /d D:\git\sql_tools\mysql_query_platform

echo ================================================================================
echo Auto Verification Started
echo Check interval: 10 minutes
echo Press Ctrl+C to stop
echo ================================================================================
echo.

:loop
D:\git\sql_tools\venv\Scripts\python.exe check_project.py
echo.
echo Waiting 10 minutes until next check...
echo Press Ctrl+C to stop
echo.

timeout /t 600 /nobreak
goto loop
