import pytest
from app.models.audit import AuditLog

def test_audit_log_creation():
    audit = AuditLog(
        action="user_login",
        user_id="test_user_id",
        resource="auth",
        status="success"
    )
    assert audit.action == "user_login"
    assert audit.user_id == "test_user_id"
    assert audit.resource == "auth"
    assert audit.status == "success"
