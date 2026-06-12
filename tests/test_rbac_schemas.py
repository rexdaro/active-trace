import pytest
from pydantic import ValidationError
from app.schemas.rbac import RoleCreate, PermissionCreate

def test_role_schema_creation():
    role = RoleCreate(name="admin", description="Administrator")
    assert role.name == "admin"
    assert role.description == "Administrator"

def test_permission_schema_creation():
    permission = PermissionCreate(name="mod:read")
    assert permission.name == "mod:read"

def test_permission_schema_validation():
    with pytest.raises(ValidationError):
        PermissionCreate(name="invalid_format")
