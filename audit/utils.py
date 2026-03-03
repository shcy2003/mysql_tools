from .models import AuditLog


def create_audit_log(user, action, ip_address, connection=None, sql=None, execution_time=None):
    """创建审计日志"""
    log = AuditLog.objects.create(
        user=user,
        action=action,
        connection=connection,
        sql=sql,
        execution_time=execution_time,
        ip_address=ip_address
    )
    return log