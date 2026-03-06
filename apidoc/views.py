"""
API Documentation Views
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def api_doc_index(request):
    """
    API 文档首页
    显示所有 API 接口的列表
    """
    api_endpoints = [
        # Connections API
        {
            'group': '连接管理 API',
            'endpoints': [
                {
                    'name': '获取连接树',
                    'method': 'GET',
                    'path': '/api/connections/tree/',
                    'description': '获取当前用户的所有数据库连接及其下的数据库和表结构',
                    'auth_required': True,
                    'request_params': [],
                    'response_example': '''{
    "code": 0,
    "message": "success",
    "data": [
        {
            "id": 1,
            "name": "本地MySQL",
            "host": "localhost",
            "port": 3306,
            "databases": [
                {
                    "name": "test_db",
                    "tables": ["users", "orders", "products"]
                }
            ]
        }
    ]
}'''
                },
                {
                    'name': '获取数据库列表',
                    'method': 'GET',
                    'path': '/api/connections/{connection_id}/databases/',
                    'description': '获取指定连接下的所有数据库列表',
                    'auth_required': True,
                    'request_params': [
                        {'name': 'connection_id', 'type': 'int', 'required': True, 'description': '数据库连接ID（URL参数）'}
                    ],
                    'response_example': '''{
    "code": 0,
    "message": "success",
    "data": ["test_db", "production"]
}'''
                },
                {
                    'name': '获取表列表',
                    'method': 'GET',
                    'path': '/api/connections/{connection_id}/tables/',
                    'description': '获取指定数据库下的所有表列表',
                    'auth_required': True,
                    'request_params': [
                        {'name': 'connection_id', 'type': 'int', 'required': True, 'description': '数据库连接ID（URL参数）'},
                        {'name': 'database', 'type': 'string', 'required': True, 'description': '数据库名称（查询参数）'}
                    ],
                    'response_example': '''{
    "code": 0,
    "message": "success",
    "data": ["users", "orders", "products"]
}'''
                },
                {
                    'name': '测试连接',
                    'method': 'POST',
                    'path': '/api/connections/test/',
                    'description': '测试数据库连接配置',
                    'auth_required': True,
                    'request_params': [
                        {'name': 'host', 'type': 'string', 'required': True, 'description': '数据库主机'},
                        {'name': 'port', 'type': 'int', 'required': True, 'description': '数据库端口'},
                        {'name': 'database', 'type': 'string', 'required': True, 'description': '数据库名'},
                        {'name': 'username', 'type': 'string', 'required': True, 'description': '用户名'},
                        {'name': 'password', 'type': 'string', 'required': True, 'description': '密码'}
                    ],
                    'response_example': '''{
    "code": 0,
    "message": "success",
    "data": {"status": "success"}
}'''
                }
            ]
        },
        # Queries API
        {
            'group': '查询执行 API',
            'endpoints': [
                {
                    'name': '通用数据查询',
                    'method': 'GET/POST',
                    'path': '/api/queries/data/',
                    'description': '通用数据查询API，支持分页、排序、筛选',
                    'auth_required': True,
                    'request_params': [
                        {'name': 'connection_id', 'type': 'int', 'required': True, 'description': '数据库连接ID'},
                        {'name': 'table', 'type': 'string', 'required': True, 'description': '表名'},
                        {'name': 'columns', 'type': 'string', 'required': False, 'description': '列名列表，逗号分隔，默认*'},
                        {'name': 'page', 'type': 'int', 'required': False, 'description': '页码，默认1'},
                        {'name': 'page_size', 'type': 'int', 'required': False, 'description': '每页大小，默认20，最大100'},
                        {'name': 'sort_column', 'type': 'string', 'required': False, 'description': '排序列'},
                        {'name': 'sort_order', 'type': 'string', 'required': False, 'description': '排序方向 asc/desc，默认asc'},
                        {'name': 'filters', 'type': 'array', 'required': False, 'description': '筛选条件 (POST)'},
                        {'name': 'filter_logic', 'type': 'string', 'required': False, 'description': 'AND/OR，默认AND'}
                    ],
                    'response_example': '''{
    "code": 0,
    "message": "success",
    "data": {
        "list": [...],
        "pagination": {
            "page": 1,
            "page_size": 20,
            "total": 100,
            "total_pages": 5
        }
    }
}'''
                },
                {
                    'name': '执行 SQL 查询',
                    'method': 'POST',
                    'path': '/api/queries/execute/',
                    'description': '执行自定义 SQL 查询（仅支持 SELECT 语句）',
                    'auth_required': True,
                    'request_params': [
                        {'name': 'connection_id', 'type': 'int', 'required': True, 'description': '数据库连接ID'},
                        {'name': 'sql', 'type': 'string', 'required': True, 'description': 'SQL 查询语句（仅 SELECT）'}
                    ],
                    'response_example': '''{
    "code": 0,
    "message": "success",
    "data": {
        "columns": ["id", "name", "email"],
        "rows": [...],
        "row_count": 2,
        "execution_time_ms": 15.23,
        "limited": false
    }
}'''
                }
            ]
        },
        # Monitoring API
        {
            'group': '健康检查 API',
            'endpoints': [
                {
                    'name': '所有连接健康检查',
                    'method': 'GET',
                    'path': '/api/health/',
                    'description': '检查所有数据库连接的健康状态',
                    'auth_required': False,
                    'request_params': [],
                    'response_example': '''{
    "overall_status": "healthy",
    "connections": [...]
}'''
                },
                {
                    'name': '数据库健康检查',
                    'method': 'GET',
                    'path': '/api/health/db/',
                    'description': '检查默认数据库连接的健康状态',
                    'auth_required': False,
                    'request_params': [],
                    'response_example': '''{
    "status": "healthy",
    "database": "default"
}'''
                },
                {
                    'name': '数据库统计信息',
                    'method': 'GET',
                    'path': '/api/health/db/stats/',
                    'description': '获取数据库连接的详细统计信息',
                    'auth_required': False,
                    'request_params': [],
                    'response_example': '''{
    "status": "healthy",
    "stats": {...}
}'''
                }
            ]
        }
    ]

    return render(request, 'apidoc/index.html', {
        'api_endpoints': api_endpoints
    })
