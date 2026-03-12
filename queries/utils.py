import time
from connections.utils import execute_query
from desensitization.utils import apply_masking_rules


def run_query(connection, sql, user, request=None, database=None):
    """执行查询并记录查询历史和审计日志"""
    # 检查是否是 SELECT 查询
    if not sql.strip().lower().startswith('select'):
        return False, '只允许执行 SELECT 查询！', 0

    start_time = time.time()

    # 执行查询 - 支持使用指定的数据库（如果提供）
    connection_params = connection.get_connection_params()
    if database:
        connection_params['database'] = database

    success, result = execute_query(connection_params, sql)
    execution_time = (time.time() - start_time) * 1000

    if success:
        # 应用脱敏规则
        masked_result = apply_masking_rules(
            connection, sql, result, user)

        # 获取连接的环境
        environment = connection.environment

        # 记录查询历史
        from queries.models import QueryHistory
        QueryHistory.objects.create(
            user=user,
            connection=connection,
            environment=environment,
            sql=sql,
            execution_time=execution_time
        )

        # 添加审计日志（不记录 sql，因为查询历史已有）
        from audit.utils import create_audit_log
        if request:
            from accounts.views import get_client_ip
            create_audit_log(
                user=user,
                action='query',
                ip_address=get_client_ip(request),
                connection=connection,
                environment=environment,
                execution_time=execution_time
            )
        else:
            create_audit_log(
                user=user,
                action='query',
                connection=connection,
                environment=environment,
                ip_address=None,
                execution_time=execution_time
            )

        return True, masked_result, execution_time
    else:
        return False, result, execution_time