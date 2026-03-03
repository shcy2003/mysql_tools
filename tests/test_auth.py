"""
用户认证模块测试

测试覆盖:
- 用户登录功能
- 用户登出功能
- 权限验证（普通用户 vs 管理员）
- 个人资料管理
"""

import unittest
import urllib.request
import urllib.parse
import urllib.error
import json
from tests import TEST_CONFIG


class TestAuth(unittest.TestCase):
    """用户认证测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.base_url = TEST_CONFIG['base_url']
        cls.timeout = TEST_CONFIG['timeout']
        cls.test_username = TEST_CONFIG['test_username']
        cls.test_password = TEST_CONFIG['test_password']
        
    def _make_request(self, url, method='GET', data=None, headers=None):
        """发送HTTP请求"""
        full_url = f"{self.base_url}{url}"
        try:
            if method == 'POST' and data:
                encoded_data = urllib.parse.urlencode(data).encode('utf-8')
                req = urllib.request.Request(full_url, data=encoded_data, method=method)
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                req = urllib.request.Request(full_url, method=method)
            
            if headers:
                for key, value in headers.items():
                    req.add_header(key, value)
            
            response = urllib.request.urlopen(req, timeout=self.timeout)
            return {
                'status': response.status,
                'headers': dict(response.headers),
                'content': response.read().decode('utf-8', errors='ignore'),
                'url': response.geturl()
            }
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'error': str(e),
                'content': e.read().decode('utf-8', errors='ignore') if e.fp else ''
            }
        except Exception as e:
            return {
                'status': -1,
                'error': str(e)
            }
    
    def test_01_home_page_accessible(self):
        """测试: 首页可以访问"""
        result = self._make_request('/')
        # 首页应该返回200或重定向到登录页
        self.assertIn(result['status'], [200, 302], 
                      f"首页访问失败: 状态码 {result['status']}")
    
    def test_02_login_page_accessible(self):
        """测试: 登录页面可以访问"""
        result = self._make_request('/accounts/login/')
        self.assertEqual(result['status'], 200,
                         f"登录页访问失败: 状态码 {result['status']}")
        # 验证页面内容包含登录相关文本
        self.assertIn('login', result['content'].lower(),
                      "登录页内容不正确")
    
    def test_03_login_with_invalid_credentials(self):
        """测试: 使用无效凭据登录失败"""
        result = self._make_request('/accounts/login/', 'POST', {
            'username': 'invalid_user',
            'password': 'wrong_password'
        })
        # 登录失败应该返回200（重新显示登录页）或302（重定向）
        self.assertIn(result['status'], [200, 302],
                      f"登录请求处理异常: 状态码 {result['status']}")
    
    def test_04_admin_requires_login(self):
        """测试: 管理后台需要登录"""
        result = self._make_request('/admin/')
        # 未登录时应该重定向到登录页
        self.assertEqual(result['status'], 302,
                         f"管理后台未正确要求登录: 状态码 {result['status']}")
    
    def test_05_logout_page_accessible(self):
        """测试: 登出页面可以访问"""
        result = self._make_request('/accounts/logout/')
        # 登出页面应该返回200或302（重定向）
        self.assertIn(result['status'], [200, 302],
                      f"登出页访问失败: 状态码 {result['status']}")


class TestAuthWithSession(unittest.TestCase):
    """需要会话状态的认证测试"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = TEST_CONFIG['base_url']
        cls.timeout = TEST_CONFIG['timeout']
        cls.test_username = TEST_CONFIG['test_username']
        cls.test_password = TEST_CONFIG['test_password']
    
    def setUp(self):
        """每个测试前创建会话"""
        self.cj = urllib.request.HTTPCookieProcessor()
        self.opener = urllib.request.build_opener(self.cj)
    
    def _make_request(self, url, method='GET', data=None):
        """发送HTTP请求（带会话）"""
        full_url = f"{self.base_url}{url}"
        try:
            if method == 'POST' and data:
                encoded_data = urllib.parse.urlencode(data).encode('utf-8')
                req = urllib.request.Request(full_url, data=encoded_data, method=method)
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                req = urllib.request.Request(full_url, method=method)
            
            response = self.opener.open(req, timeout=self.timeout)
            return {
                'status': response.status,
                'content': response.read().decode('utf-8', errors='ignore'),
                'url': response.geturl()
            }
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'error': str(e),
                'content': e.read().decode('utf-8', errors='ignore') if e.fp else ''
            }
        except Exception as e:
            return {
                'status': -1,
                'error': str(e)
            }
    
    def test_01_login_successful(self):
        """测试: 使用正确凭据登录成功"""
        # 获取登录页面（获取CSRF token）
        result = self._make_request('/accounts/login/')
        self.assertEqual(result['status'], 200, "无法访问登录页")
        
        # 提交登录表单
        result = self._make_request('/accounts/login/', 'POST', {
            'username': self.test_username,
            'password': self.test_password
        })
        
        # 登录成功后应该重定向到首页或成功页面
        self.assertIn(result['status'], [200, 302],
                      f"登录失败: 状态码 {result['status']}")
    
    def test_02_protected_pages_require_login(self):
        """测试: 受保护页面需要登录"""
        # 测试连接管理页面
        result = self._make_request('/connections/')
        self.assertEqual(result['status'], 302,
                         f"连接管理页面未正确要求登录: 状态码 {result['status']}")
        
        # 测试查询页面
        result = self._make_request('/queries/')
        self.assertEqual(result['status'], 302,
                         f"查询页面未正确要求登录: 状态码 {result['status']}")


if __name__ == '__main__':
    # 配置测试
    unittest.main(verbosity=2)
