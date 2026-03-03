"""
MySQL查询平台自动化测试套件

测试覆盖范围:
- 用户认证（登录、登出、权限）
- 数据库连接管理（创建、编辑、删除、测试连接）
- SQL查询（执行SELECT、阻止非SELECT、显示结果）
- 可视化查询（表/字段选择、条件设置、执行）
- 脱敏功能（规则CRUD、完全/部分/正则脱敏验证）
- 审计日志（日志查看、记录准确性）
"""

import os
import sys

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 测试配置
TEST_CONFIG = {
    'base_url': os.getenv('TEST_BASE_URL', 'http://localhost:8000'),
    'test_username': os.getenv('TEST_USERNAME', 'admin'),
    'test_password': os.getenv('TEST_PASSWORD', 'admin123'),
    'test_db_host': os.getenv('TEST_DB_HOST', 'localhost'),
    'test_db_port': os.getenv('TEST_DB_PORT', '3306'),
    'test_db_name': os.getenv('TEST_DB_NAME', 'test_db'),
    'test_db_user': os.getenv('TEST_DB_USER', 'root'),
    'test_db_password': os.getenv('TEST_DB_PASSWORD', ''),
    'timeout': int(os.getenv('TEST_TIMEOUT', '30')),
    'headless': os.getenv('TEST_HEADLESS', 'true').lower() == 'true',
}
