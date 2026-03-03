#!/bin/bash
# MySQL查询平台自动化测试脚本
# 用于定时执行完整测试套件

# 配置
PROJECT_DIR="/mnt/c/git/mysql_query_platform"
REPORT_DIR="/home/kimi/.openclaw/workspace/agents/SHARED/test_reports"
DATE=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="test_report_${DATE}.html"
LOG_FILE="test_log_${DATE}.txt"

# 确保目录存在
mkdir -p "$REPORT_DIR"

# 切换到项目目录
cd "$PROJECT_DIR" || exit 1

# 记录开始时间
echo "========================================" >> "$REPORT_DIR/$LOG_FILE"
echo "测试开始时间: $(date)" >> "$REPORT_DIR/$LOG_FILE"
echo "========================================" >> "$REPORT_DIR/$LOG_FILE"

# 运行测试
echo "运行自动化测试..."
python3 run_tests.py --html -v >> "$REPORT_DIR/$LOG_FILE" 2>&1

# 记录结束时间
echo "" >> "$REPORT_DIR/$LOG_FILE"
echo "========================================" >> "$REPORT_DIR/$LOG_FILE"
echo "测试结束时间: $(date)" >> "$REPORT_DIR/$LOG_FILE"
echo "========================================" >> "$REPORT_DIR/$LOG_FILE"

# 移动生成的报告（如果有）
if [ -f "test_report.html" ]; then
    mv "test_report.html" "$REPORT_DIR/$REPORT_FILE"
    echo "测试报告已生成: $REPORT_FILE"
fi

# 输出测试摘要
echo ""
echo "========================================"
echo "测试执行完成"
echo "日志文件: $REPORT_DIR/$LOG_FILE"
if [ -f "$REPORT_DIR/$REPORT_FILE" ]; then
    echo "报告文件: $REPORT_DIR/$REPORT_FILE"
fi
echo "========================================"

# 返回测试结果
exit ${PIPESTATUS[0]}
