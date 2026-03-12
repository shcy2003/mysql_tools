# 自动验证系统说明

## 检查间隔
- **检查频率**: 每 10 分钟检查一次

## 使用方法

### Linux/Mac
```bash
cd /mnt/d/git/sql_tools/mysql_query_platform
./auto_check.sh
```

### Windows
```cmd
cd D:\git\sql_tools\mysql_query_platform
auto_check.bat
```

### 单次检查
```bash
cd /mnt/d/git/sql_tools/mysql_query_platform
/mnt/d/git/sql_tools/venv/bin/python check_project.py
```

## 输出文件
- `verification_report.md` - Markdown 格式报告
- `verification_report.json` - JSON 格式报告
