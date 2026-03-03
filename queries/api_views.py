"""
查询模块API视图 - 分页查询、筛选功能
"""
import json
import re
import mysql.connector
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from connections.models import MySQLConnection


def validate_identifier(name):
    """验证标识符（表名、列名）是否合法"""
    if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        return False
    return True


def parse_sort_param(sort_column, sort_order='asc'):
    """解析排序参数"""
    if not validate_identifier(sort_column):
        return None
    
    sort_order = sort_order.lower()
    if sort_order not in ['asc', 'desc']:
        sort_order = 'asc'
    
    return f"`{sort_column}` {sort_order.upper()}"


def build_where_clause(filters, filter_logic='AND'):
    """
    构建WHERE子句
    
    Args:
        filters: 筛选条件列表 [{"column": "age", "operator": ">=", "value": 18}, ...]
        filter_logic: 条件组合逻辑 AND/OR
    
    Returns:
        tuple: (where_clause, params)
    """
    if not filters:
        return "", []
    
    conditions = []
    params = []
    
    allowed_operators = {
        'eq': '=', 'neq': '!=', 'gt': '>', 'lt': '<', 'gte': '>=', 'lte': '<=',
        'contains': 'LIKE', 'startswith': 'LIKE', 'endswith': 'LIKE', 'in': 'IN'
    }
    
    for f in filters:
        column = f.get('column')
        operator = f.get('operator', 'eq').lower()
        value = f.get('value')
        
        # 验证字段名
        if not validate_identifier(column):
            continue
        
        # 验证操作符
        if operator not in allowed_operators:
            continue
        
        sql_operator = allowed_operators[operator]
        
        # 根据操作符构建条件
        if operator == 'contains':
            conditions.append(f"`{column}` {sql_operator} %s")
            params.append(f"%{value}%")
        elif operator == 'startswith':
            conditions.append(f"`{column}` {sql_operator} %s")
            params.append(f"%{value}")
        elif operator == 'endswith':
            conditions.append(f"`{column}` {sql_operator} %s")
            params.append(f"{value}%")
        elif operator == 'in':
            if isinstance(value, list):
                placeholders = ', '.join(['%s'] * len(value))
                conditions.append(f"`{column}` {sql_operator} ({placeholders})")
                params.extend(value)
        else:
            conditions.append(f"`{column}` {sql_operator} %s")
            params.append(value)
    
    if not conditions:
        return "", []
    
    filter_logic = filter_logic.upper()
    if filter_logic not in ['AND', 'OR']:
        filter_logic = 'AND'
    
    where_clause = f" WHERE {' ' + filter_logic + ' '.join(conditions)}"
    return where_clause, params


@login_required
@require_http_methods(["GET", "POST"])
def api_query_data(request):
    """
    通用数据查询API - 支持分页、排序、筛选
    
    GET /api/queries/data/?connection_id=1&table=users&page=1&page_size=20
    POST /api/queries/data/ (复杂筛选条件)
    
    请求参数:
        - connection_id: 数据库连接ID (必需)
        - table: 表名 (必需)
        - columns: 列名列表，逗号分隔，默认*
        - page: 页码，默认1
        - page_size: 每页大小，默认20，最大100
        - sort_column: 排序列
        - sort_order: 排序方向 asc/desc，默认asc
        - filters: JSON格式的筛选条件 (POST)
        - filter_logic: AND/OR，默认AND
    
    响应:
        {
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
        }
    """
    try:
        # 获取参数
        if request.method == "GET":
            connection_id = request.GET.get('connection_id')
            table = request.GET.get('table')
            columns = request.GET.get('columns', '*')
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 20))
            sort_column = request.GET.get('sort_column')
            sort_order = request.GET.get('sort_order', 'asc')
            filters = None
            filter_logic = request.GET.get('filter_logic', 'AND')
        else:  # POST
            data = json.loads(request.body)
            connection_id = data.get('connection_id')
            table = data.get('table')
            columns = data.get('columns', '*')
            page = int(data.get('page', 1))
            page_size = int(data.get('page_size', 20))
            sort_column = data.get('sort_column')
            sort_order = data.get('sort_order', 'asc')
            filters = data.get('filters')
            filter_logic = data.get('filter_logic', 'AND')
        
        # 验证必需参数
        if not connection_id or not table:
            return JsonResponse({
                "code": 400,
                "message": "缺少必需参数: connection_id 和 table"
            }, status=400)
        
        # 验证表名
        if not validate_identifier(table):
            return JsonResponse({
                "code": 400,
                "message": f"非法的表名: {table}"
            }, status=400)
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20
        elif page_size > 100:
            page_size = 100  # 最大限制
        
        # 获取连接
        try:
            connection = MySQLConnection.objects.get(
                id=connection_id,
                created_by=request.user
            )
        except MySQLConnection.DoesNotExist:
            return JsonResponse({
                "code": 404,
                "message": "数据库连接不存在或无权限访问"
            }, status=404)
        
        # 构建查询
        connection_params = connection.get_connection_params()
        
        # 处理列
        if columns == '*':
            select_clause = '*'
        else:
            col_list = [c.strip() for c in columns.split(',')]
            # 验证所有列名
            for col in col_list:
                if not validate_identifier(col):
                    return JsonResponse({
                        "code": 400,
                        "message": f"非法的列名: {col}"
                    }, status=400)
            select_clause = ', '.join([f'`{c}`' for c in col_list])
        
        # 构建WHERE子句
        where_clause, query_params = build_where_clause(filters, filter_logic)
        
        # 构建ORDER BY子句
        order_clause = ""
        if sort_column:
            order_by = parse_sort_param(sort_column, sort_order)
            if order_by:
                order_clause = f" ORDER BY {order_by}"
        
        # 先查询总数
        count_sql = f"SELECT COUNT(*) as total FROM `{table}`{where_clause}"
        
        # 再查询数据
        offset = (page - 1) * page_size
        data_sql = f"SELECT {select_clause} FROM `{table}`{where_clause}{order_clause} LIMIT %s OFFSET %s"
        
        # 执行查询
        try:
            conn = mysql.connector.connect(**connection_params)
            cursor = conn.cursor(dictionary=True)
            
            # 查询总数
            if query_params:
                cursor.execute(count_sql, query_params)
            else:
                cursor.execute(count_sql)
            total = cursor.fetchone()['total']
            
            # 查询数据
            query_params_with_limit = query_params + [page_size, offset] if query_params else [page_size, offset]
            cursor.execute(data_sql, query_params_with_limit)
            data = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            # 计算总页数
            total_pages = (total + page_size - 1) // page_size if total > 0 else 0
            
            return JsonResponse({
                "code": 0,
                "message": "success",
                "data": {
                    "list": data,
                    "pagination": {
                        "page": page,
                        "page_size": page_size,
                        "total": total,
                        "total_pages": total_pages
                    }
                }
            })
            
        except mysql.connector.Error as e:
            return JsonResponse({
                "code": 500,
                "message": f"数据库查询错误: {str(e)}"
            }, status=500)
        
    except json.JSONDecodeError:
        return JsonResponse({
            "code": 400,
            "message": "JSON格式错误"
        }, status=400)
    except Exception as e:
        return JsonResponse({
            "code": 500,
            "message": f"服务器内部错误: {str(e)}"
        }, status=500)
