from .models import AuditLog
from connections.models import MySQLConnection


def create_audit_log(user, action, ip_address, connection=None, connection_id=None, sql=None, execution_time=None):
    """创建审计日志

    Args:
        user: 用户对象
        action: 操作类型
        ip_address: IP地址
        connection: MySQLConnection对象（可选）
        connection_id: 连接ID（可选，如果传了connection_id会自动获取connection对象）
        sql: SQL语句（可选）
        execution_time: 执行时间（可选）
    """
    # 如果传了connection_id但没有传connection，自动获取connection对象
    if connection is None and connection_id is not None:
        try:
            connection = MySQLConnection.objects.get(id=connection_id)
        except MySQLConnection.DoesNotExist:
            connection = None

    log = AuditLog.objects.create(
        user=user,
        action=action,
        connection=connection,
        sql=sql,
        execution_time=execution_time,
        ip_address=ip_address
    )
    return log