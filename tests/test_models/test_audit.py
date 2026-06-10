def test_audit_log_fields():
    audit = AuditLog(
        action="test_action",
        actor_id="user1",
        impersonator_id="admin1",
        materia_id="mat1",
        detalle="{}",
        filas_afectadas=1,
        ip="127.0.0.1",
        user_agent="browser"
    )
    assert audit.actor_id == "user1"
    assert audit.impersonator_id == "admin1"
    assert audit.materia_id == "mat1"
    assert audit.detalle == "{}"
    assert audit.filas_afectadas == 1
    assert audit.ip == "127.0.0.1"
    assert audit.user_agent == "browser"
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
