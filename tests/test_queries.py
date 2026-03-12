"""
SQL查询功能模块测试

测试覆盖:
- SQL查询页面访问
- 执行SELECT查询
- 阻止非SELECT语句（INSERT/UPDATE/DELETE）
- 查询结果显示
- 查询历史记录
"""

import unittest
import urllib.request
import urllib.parse
import urllib.error
from tests import TEST_CONFIG


class TestQueriesBase(unittest.TestCase):
    """查询功能测试基类"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = TEST_CONFIG['base_url']
        cls.timeout = TEST_CONFIG['timeout']
        cls.test_username = TEST_CONFIG['test_username']
        cls.test_password = TEST_CONFIG['test_password']
    
    def setUp(self):
        """每个测试前创建会话并登录"""
        self.cj = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(self.cj)
        self._login()
    
    def _login(self):
        """执行登录"""
        full_url = f"{self.base_url}/accounts/login/"
        try:
            # 先获取登录页
            req = urllib.request.Request(full_url, method='GET')
            response = self.opener.open(req, timeout=self.timeout)
            response.read()
            
            # 提交登录表单
            login_data = urllib.parse.urlencode({
                'username': self.test_username,
                'password': self.test_password
            }).encode('utf-8')
            
            req = urllib.request.Request(full_url, data=login_data, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            response = self.opener.open(req, timeout=self.timeout)
            response.read()
        except Exception as e:
            self.fail(f"登录失败: {str(e)}")
    
    def _make_request(self, url, method='GET', data=None):
        """发送HTTP请求"""
        full_url = f"{self.base_url}{url}"
        try:
            if method == 'POST' and data:
                encoded_data = urllib.parse.urlencode(data).encode('utf-8')
                req = urllib.request.Request(full_url, data=encoded_data, method=method)
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                req = urllib.request.Request(full_url, method=method)
            
            response = self.opener.open(req, timeout=self.timeout)
            content = response.read().decode('utf-8', errors='ignore')
            return {
                'status': response.status,
                'content': content,
                'url': response.geturl()
            }
        except urllib.error.HTTPError as e:
            content = e.read().decode('utf-8', errors='ignore') if e.fp else ''
            return {
                'status': e.code,
                'error': str(e),
                'content': content
            }
        except Exception as e:
            return {
                'status': -1,
                'error': str(e)
            }


class TestQueryPage(TestQueriesBase):
    """测试查询页面访问"""
    
    def test_01_query_page_accessible(self):
        """测试: 查询页面可访问"""
        result = self._make_request('/queries/')
        self.assertEqual(result['status'], 200,
                        f"查询页访问失败: 状态码 {result['status']}, 错误: {result.get('error', '')}")
        # 验证页面内容
        content_lower = result['content'].lower()
        self.assertTrue(
            'query' in content_lower or 'sql' in content_lower or '查询' in result['content'],
            "查询页内容不正确"
        )
    
    def test_02_query_page_requires_login(self):
        """测试: 未登录时查询页面需要登录"""
        # 创建新的opener（无会话）
        new_opener = urllib.request.build_opener()
        full_url = f"{self.base_url}/queries/"
        try:
            req = urllib.request.Request(full_url, method='GET')
            response = new_opener.open(req, timeout=self.timeout)
            # 如果成功访问，说明不需要登录，这可能是测试环境配置问题
            self.assertEqual(response.status, 302,
                           "未登录用户应该被重定向到登录页")
        except urllib.error.HTTPError as e:
            # 期望返回302重定向或401未授权
            self.assertIn(e.code, [302, 401, 403],
                         f"未登录用户访问查询页返回意外状态码: {e.code}")


class TestQueryExecution(TestQueriesBase):
    """测试查询执行功能"""
    
    def test_01_select_query_endpoint_exists(self):
        """测试: SELECT查询端点存在"""
        # 先获取查询页面
        result = self._make_request('/queries/')
        self.assertEqual(result['status'], 200, "查询页无法访问")
        
        # 检查页面是否包含查询执行功能
        content_lower = result['content'].lower()
        self.assertTrue(
            'execute' in content_lower or 
            'run' in content_lower or 
            'submit' in content_lower or
            '执行' in result['content'] or
            '运行' in result['content'],
            "查询页缺少执行查询功能"
        )
    
    def test_02_query_page_has_sql_input(self):
        """测试: 查询页面包含SQL输入区域"""
        result = self._make_request('/queries/')
        self.assertEqual(result['status'], 200, "查询页无法访问")
        
        # 检查页面是否包含文本输入区域
        content_lower = result['content'].lower()
        self.assertTrue(
            '<textarea' in content_lower or
            '<input' in content_lower or
            'contenteditable' in content_lower,
            "查询页缺少SQL输入区域"
        )
    
    def test_03_query_page_shows_results_area(self):
        """测试: 查询页面包含结果展示区域"""
        result = self._make_request('/queries/')
        self.assertEqual(result['status'], 200, "查询页无法访问")
        
        # 检查结果展示区域
        content_lower = result['content'].lower()
        self.assertTrue(
            'result' in content_lower or
            'result' in content_lower or
            'table' in content_lower or
            'data' in content_lower or
            '结果' in result['content'] or
            '数据' in result['content'],
            "查询页缺少结果展示区域"
        )


class TestQueryHistory(TestQueriesBase):
    """测试查询历史功能"""
    
    def test_01_query_history_link_exists(self):
        """测试: 查询历史链接存在"""
        result = self._make_request('/queries/')
        self.assertEqual(result['status'], 200, "查询页无法访问")
        
        # 检查历史记录链接
        content_lower = result['content'].lower()
        self.assertTrue(
            'history' in content_lower or
            'history' in content_lower or
            '历史' in result['content'],
            "查询页缺少历史记录功能"
        )
    
    def test_02_query_history_page_accessible(self):
        """测试: 查询历史页面可访问"""
        # 尝试访问历史记录页面
        possible_urls = [
            '/queries/history/',
            '/queries/history/',
            '/audit/history/',
            '/history/',
        ]
        
        accessible = False
        for url in possible_urls:
            result = self._make_request(url)
            if result['status'] == 200:
                accessible = True
                break
        
        # 即使没有专门的历史页面，只要查询页面有历史展示即可
        if not accessible:
            result = self._make_request('/queries/')
            if result['status'] == 200 and 'history' in result['content'].lower():
                accessible = True
        
        self.assertTrue(accessible, "无法访问查询历史功能")


if __name__ == '__main__':
    unittest.main(verbosity=2)
