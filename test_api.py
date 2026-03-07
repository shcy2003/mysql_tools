import requests
import json
import sys

# Set encoding to utf-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Login to get session cookie
login_url = 'http://127.0.0.1:8000/accounts/login/'
api_test_url = 'http://127.0.0.1:8000/api/connections/test/'

# First, get the login page to get CSRF token
session = requests.Session()
login_page = session.get(login_url)
csrf_token = login_page.cookies['csrftoken']

# Login with admin credentials
login_data = {
    'username': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': csrf_token,
    'next': '/desensitization/'
}

login_response = session.post(login_url, data=login_data, headers={'Referer': login_url})

# Check if login was successful
if '脱敏规则' in login_response.text or 'desensitization' in login_response.url:
    print('Login successful!')
else:
    print('Login failed! Status code:', login_response.status_code)
    # Try with another possible password
    print('Trying another password...')
    login_data2 = login_data.copy()
    login_data2['password'] = 'password'
    login_response2 = session.post(login_url, data=login_data2, headers={'Referer': login_url})
    print('Second login status:', login_response2.status_code)

# Test desensitization list page
desensitization_url = 'http://127.0.0.1:8000/desensitization/'
response = session.get(desensitization_url)
button_count = response.text.count('创建规则')
print(f"Desensitization page 'Create Rule' button count: {button_count}")

# Save HTML for inspection
with open('desensitization_page.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print('Saved desensitization page HTML to desensitization_page.html')

# Test connection API
test_data = {
    'host': 'localhost',
    'port': 3306,
    'database': 'mysql',
    'username': 'root',
    'password': ''
}

headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': session.cookies['csrftoken'],
    'Referer': 'http://127.0.0.1:8000/connections/create/'
}

print('Testing connection API...')
api_response = session.post(api_test_url, data=json.dumps(test_data), headers=headers)
print(f"Connection test API response status: {api_response.status_code}")
print(f"Connection test API response content: {api_response.text}")
