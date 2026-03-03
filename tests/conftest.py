"""
pytest配置和共享fixture

提供测试所需的共享资源和配置
"""

import pytest
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
    'timeout': int(os.getenv('TEST_TIMEOUT', '30')),
}


@pytest.fixture(scope='session')
def base_url():
    """提供基础URL"""
    return TEST_CONFIG['base_url']


@pytest.fixture(scope='session')
def test_credentials():
    """提供测试账号密码"""
    return {
        'username': TEST_CONFIG['test_username'],
        'password': TEST_CONFIG['test_password']
    }


@pytest.fixture(scope='session')
def timeout():
    """提供请求超时时间"""
    return TEST_CONFIG['timeout']


def pytest_collection_modifyitems(config, items):
    """自定义测试收集"""
    # 按测试名称排序
    items.sort(key=lambda x: x.nodeid)


def pytest_configure(config):
    """配置pytest"""
    # 添加自定义标记
    config.addinivalue_line("markers", "smoke: 冒烟测试")
    config.addinivalue_line("markers", "auth: 认证相关测试")
    config.addinivalue_line("markers", "connection: 数据库连接测试")
    config.addinivalue_line("markers", "query: SQL查询测试")
    config.addinivalue_line("markers", "slow: 慢速测试")
    config.addinivalue_line("markers", "desensitization: 脱敏功能测试")
    config.addinivalue_line("markers", "audit: 审计日志测试")
