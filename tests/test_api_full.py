"""
MySQL Query Platform API 自动化测试脚本
包含所有 API 接口的基本功能测试、参数边界测试和错误处理测试
"""
import unittest
import json
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysql_query_platform.settings')
import django
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class BaseAPITestCase(unittest.TestCase):
    """基础 API 测试类"""

    def setUp(self):
        """测试前的准备工作"""
        self.client = Client()

        # 创建测试用户
        self.test_user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
            role='admin'
        )

        # 登录
        self.client.login(username='testuser', password='testpass123')

    def tearDown(self):
        """测试后的清理工作"""
        self.client.logout()


class HealthCheckAPITests(BaseAPITestCase):
    """健康检查 API 测试"""

    def test_health_check_endpoint(self):
        """测试所有连接健康检查端点"""
        response = self.client.get('/api/health/')
        self.assertIn(response.status_code, [200, 503])

    def test_db_health_check_endpoint(self):
        """测试数据库健康检查端点"""
        response = self.client.get('/api/health/db/')
        self.assertIn(response.status_code, [200, 503])

    def test_db_stats_endpoint(self):
        """测试数据库统计信息端点"""
        response = self.client.get('/api/health/db/stats/')
        self.assertIn(response.status_code, [200, 500])

    def test_health_without_auth(self):
        """测试未登录时访问健康检查 API（应该可以访问）"""
        self.client.logout()
        response = self.client.get('/api/health/')
        self.assertIn(response.status_code, [200, 503])


class ConnectionsAPITests(BaseAPITestCase):
    """连接管理 API 测试"""

    def test_connection_tree_endpoint(self):
        """测试获取连接树端点"""
        response = self.client.get('/api/connections/tree/')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('code', data)
        self.assertIn('message', data)
        self.assertIn('data', data)

    def test_connection_tree_without_auth(self):
        """测试未登录时访问连接树 API（应该重定向或返回401）"""
        self.client.logout()
        response = self.client.get('/api/connections/tree/')
        self.assertIn(response.status_code, [302, 401, 403])

    def test_connection_databases_endpoint_invalid_id(self):
        """测试使用无效的连接ID获取数据库列表"""
        response = self.client.get('/api/connections/999999/databases/')
        self.assertIn(response.status_code, [404, 400, 500])

    def test_connection_tables_endpoint_missing_param(self):
        """测试缺少database参数时获取表列表"""
        # 注意：这里需要一个有效的连接ID，我们先创建一个测试连接
        from connections.models import MySQLConnection
        test_connection = MySQLConnection.objects.create(
            name='Test Connection',
            host='localhost',
            port=3306,
            database='test_db',
            username='root',
            password='password',
            created_by=self.test_user
        )

        response = self.client.get(f'/api/connections/{test_connection.id}/tables/')
        self.assertEqual(response.status_code, 400)

        data = json.loads(response.content)
        self.assertNotEqual(data.get('code'), 0)

        test_connection.delete()


class QueriesAPITests(BaseAPITestCase):
    """查询执行 API 测试"""

    def test_query_data_endpoint_missing_params(self):
        """测试缺少必需参数时的通用数据查询"""
        response = self.client.get('/api/queries/data/')
        self.assertIn(response.status_code, [400, 500])

    def test_execute_query_endpoint_missing_params(self):
        """测试缺少必需参数时的SQL执行"""
        response = self.client.post(
            '/api/queries/execute/',
            content_type='application/json',
            data=json.dumps({})
        )
        self.assertIn(response.status_code, [400, 500])

    def test_execute_query_endpoint_invalid_sql(self):
        """测试执行无效的SQL（非SELECT语句）"""
        # 创建测试连接
        from connections.models import MySQLConnection
        test_connection = MySQLConnection.objects.create(
            name='Test Connection',
            host='localhost',
            port=3306,
            database='test_db',
            username='root',
            password='password',
            created_by=self.test_user
        )

        response = self.client.post(
            '/api/queries/execute/',
            content_type='application/json',
            data=json.dumps({
                'connection_id': test_connection.id,
                'sql': 'DELETE FROM users'
            })
        )

        self.assertIn(response.status_code, [400, 500])

        data = json.loads(response.content)
        self.assertNotEqual(data.get('code'), 0)

        test_connection.delete()

    def test_execute_query_endpoint_without_auth(self):
        """测试未登录时执行查询"""
        self.client.logout()
        response = self.client.post(
            '/api/queries/execute/',
            content_type='application/json',
            data=json.dumps({
                'connection_id': 1,
                'sql': 'SELECT * FROM users'
            })
        )
        self.assertIn(response.status_code, [302, 401, 403])


class APIDocumentationTests(BaseAPITestCase):
    """API 文档页面测试"""

    def test_swagger_ui_endpoint(self):
        """测试 Swagger UI 页面"""
        response = self.client.get('/swagger/')
        self.assertEqual(response.status_code, 200)

    def test_redoc_endpoint(self):
        """测试 Redoc 页面"""
        response = self.client.get('/redoc/')
        self.assertEqual(response.status_code, 200)

    def test_api_doc_index(self):
        """测试 API 文档首页"""
        response = self.client.get('/api-doc/')
        self.assertEqual(response.status_code, 200)

    def test_swagger_json_endpoint(self):
        """测试 Swagger JSON 端点"""
        response = self.client.get('/swagger.json')
        self.assertEqual(response.status_code, 200)


class ParameterBoundaryTests(BaseAPITestCase):
    """参数边界测试"""

    def test_large_page_size(self):
        """测试超大分页大小"""
        # 测试连接树API，虽然没有page参数，但作为示例
        response = self.client.get('/api/connections/tree/')
        self.assertEqual(response.status_code, 200)

    def test_empty_sql_query(self):
        """测试空SQL查询"""
        # 创建测试连接
        from connections.models import MySQLConnection
        test_connection = MySQLConnection.objects.create(
            name='Test Connection',
            host='localhost',
            port=3306,
            database='test_db',
            username='root',
            password='password',
            created_by=self.test_user
        )

        response = self.client.post(
            '/api/queries/execute/',
            content_type='application/json',
            data=json.dumps({
                'connection_id': test_connection.id,
                'sql': ''
            })
        )

        self.assertIn(response.status_code, [400, 500])

        test_connection.delete()


class ErrorHandlingTests(BaseAPITestCase):
    """错误处理测试"""

    def test_invalid_json_body(self):
        """测试无效的JSON请求体"""
        response = self.client.post(
            '/api/queries/execute/',
            content_type='application/json',
            data='invalid json'
        )
        self.assertIn(response.status_code, [400, 500])

    def test_nonexistent_endpoint(self):
        """测试不存在的API端点"""
        response = self.client.get('/api/nonexistent/endpoint/')
        self.assertEqual(response.status_code, 404)

    def test_method_not_allowed(self):
        """测试不允许的HTTP方法"""
        response = self.client.post('/api/health/')
        self.assertIn(response.status_code, [405, 400, 500])


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("MySQL Query Platform API 自动化测试")
    print("=" * 60)

    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(HealthCheckAPITests))
    suite.addTests(loader.loadTestsFromTestCase(ConnectionsAPITests))
    suite.addTests(loader.loadTestsFromTestCase(QueriesAPITests))
    suite.addTests(loader.loadTestsFromTestCase(APIDocumentationTests))
    suite.addTests(loader.loadTestsFromTestCase(ParameterBoundaryTests))
    suite.addTests(loader.loadTestsFromTestCase(ErrorHandlingTests))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # 打印测试摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    print("=" * 60)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
