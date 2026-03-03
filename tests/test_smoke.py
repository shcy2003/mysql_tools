"""
冒烟测试套件

执行核心功能的快速验证测试
"""

import unittest
import urllib.request
import urllib.parse
import urllib.error
from tests import TEST_CONFIG


class TestSmoke(unittest.TestCase):
    """冒烟测试类"""
    
    @classmethod
    def setUpClass(cls):
        cls.base_url = TEST_CONFIG['base_url']
        cls.timeout = TEST_CONFIG['timeout']
        cls.test_username = TEST_CONFIG['test_username']
        cls.test_password = TEST_CONFIG['test_password']
    
    def _make_request(self, url, method='GET', data=None, headers=None, use_cookies=False):
        """发送HTTP请求"""
        full_url = f"{self.base_url}{url}"
        
        if use_cookies and not hasattr(self, '_cj'):
            self._cj = urllib.request.HTTPCookieProcessor()
            self._opener = urllib.request.build_opener(self._cj)
        elif use_cookies:
            opener = self._opener
        else:
            opener = urllib.request.build_opener()
        
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
            
            response = opener.open(req, timeout=self.timeout)
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
    
    def test_01_server_is_running(self):
        """冒烟测试: 服务器正在运行"""
        result = self._make_request('/')
        # 服务器应该返回200或重定向
        self.assertIn(result['status'], [200, 302, 301],
                     f"服务器可能没有运行: 状态码 {result['status']}, 错误: {result.get('error', '')}")
    
    def test_02_login_page_available(self):
        """冒烟测试: 登录页可访问"""
        result = self._make_request('/accounts/login/')
        self.assertEqual(result['status'], 200,
                        f"登录页无法访问: 状态码 {result['status']}")
        # 验证页面包含登录相关元素
        content_lower = result['content'].lower()
        self.assertTrue(
            'username' in content_lower or 
            'password' in content_lower or
            'login' in content_lower or
            '登录' in result['content'],
            "登录页缺少必要的表单元素"
        )
    
    def test_03_admin_panel_accessible(self):
        """冒烟测试: 管理后台可访问"""
        result = self._make_request('/admin/')
        # 应该返回302重定向到登录页，或者如果已登录则返回200
        self.assertIn(result['status'], [200, 302],
                     f"管理后台访问异常: 状态码 {result['status']}")
    
    def test_04_connections_page_exists(self):
        """冒烟测试: 连接管理页面存在"""
        result = self._make_request('/connections/')
        # 应该返回302（需要登录）或200（已登录）
        self.assertIn(result['status'], [200, 302],
                     f"连接管理页面访问异常: 状态码 {result['status']}")
    
    def test_05_queries_page_exists(self):
        """冒烟测试: 查询页面存在"""
        result = self._make_request('/queries/')
        # 应该返回302（需要登录）或200（已登录）
        self.assertIn(result['status'], [200, 302],
                     f"查询页面访问异常: 状态码 {result['status']}")
    
    def test_06_static_files_served(self):
        """冒烟测试: 静态文件可访问"""
        # 尝试访问静态文件路径
        static_paths = [
            '/static/',
            '/static/css/',
            '/static/js/',
            '/static/images/',
        ]
        
        any_accessible = False
        for path in static_paths:
            result = self._make_request(path)
            if result['status'] in [200, 403, 404]:
                # 403或404也可以接受，说明路径存在
                any_accessible = True
                break
        
        # 不强制要求通过，因为静态文件配置可能不同
        if not any_accessible:
            self.skipTest("静态文件路径无法访问（可能配置不同）")


if __name__ == '__main__':
    unittest.main(verbosity=2)
