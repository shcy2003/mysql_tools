"""
测试API接口是否正确应用脱敏规则
"""
import requests
import json


def test_api_masking():
    print("=" * 60)
    print("测试API查询脱敏功能")
    print("=" * 60)

    # 1. 登录获取session和CSRF token
    login_url = "http://127.0.0.1:8000/accounts/login/"

    try:
        login_response = requests.get(login_url)
        print(f"登录页面响应: {login_response.status_code}")

        # 提取CSRF token
        csrf_token = None
        cookies = login_response.cookies.get_dict()
        for cookie in login_response.headers.get('Set-Cookie', '').split(';'):
            if 'csrftoken' in cookie:
                csrf_token = cookie.split('=')[1].split(';')[0]
                print(f"获取到CSRF Token: {csrf_token}")

    except Exception as e:
        print(f"登录页面访问失败: {e}")
        return False

    # 2. 执行登录（需要使用真实的登录信息）
    # 这里使用默认的测试用户
    login_data = {
        'csrfmiddlewaretoken': csrf_token,
        'username': 'admin',
        'password': 'admin123'
    }

    headers = {
        'Referer': login_url,
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        # 使用会话保持登录状态
        with requests.Session() as session:
            login_result = session.post(
                login_url,
                data=login_data,
                headers=headers,
                cookies=cookies
            )

            print(f"登录响应状态: {login_result.status_code}")
            if login_result.status_code == 302:  # 重定向说明成功
                print("✅ 登录成功")
            else:
                print(f"登录响应: {login_result.text}")
                return False

            # 3. 测试API查询
            api_url = "http://127.0.0.1:8000/api/queries/execute/"
            api_headers = {
                'X-CSRFToken': csrf_token,
                'Content-Type': 'application/json',
                'Referer': 'http://127.0.0.1:8000/queries/sql/'
            }

            query_data = {
                'connection_id': 1,  # 需要确保这个ID存在
                'sql': 'SELECT * FROM users LIMIT 3'
            }

            query_response = session.post(
                api_url,
                data=json.dumps(query_data),
                headers=api_headers
            )

            print(f"查询响应状态: {query_response.status_code}")

            if query_response.status_code == 200:
                try:
                    result = query_response.json()
                    print(f"查询结果: {json.dumps(result, ensure_ascii=False, indent=2)}")

                    # 检查email字段是否被脱敏
                    if 'data' in result and 'rows' in result['data']:
                        emails = []
                        for row in result['data']['rows']:
                            if 'email' in row:
                                emails.append(row['email'])

                        print(f"\n提取到email字段: {emails}")

                        if emails:
                            # 检查email是否被脱敏
                            all_masked = True
                            for email in emails:
                                if '****' in email and len(email) > 8:
                                    print(f"✅ {email} 已被正确脱敏")
                                else:
                                    print(f"❌ {email} 未被脱敏")
                                    all_masked = False

                            print(f"\n所有email字段脱敏状态: {'✅' if all_masked else '❌'}")

                except Exception as e:
                    print(f"解析响应失败: {e}")
                    print(f"原始响应: {query_response.text}")
            else:
                print(f"查询失败: {query_response.text}")

    except Exception as e:
        print(f"请求失败: {e}")
        return False

    print()
    print("=" * 60)
    return True


def main():
    print("MySQL查询平台 - API接口脱敏测试")

    try:
        test_api_masking()

        print("\n测试完成")

    except Exception as e:
        print(f"\n测试出错: {e}")
        import traceback
        print(traceback.format_exc())

    print()


if __name__ == "__main__":
    main()
