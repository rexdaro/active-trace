from sqlalchemy.orm import validates
import pytest
from app.models.rbac import Role, Permission, RolePermission

def test_rbac_models_instantiation():
    # Test creation
    role = Role(name="admin")
    permission = Permission(name="mod:read")
    
    assert role.name == "admin"
    assert permission.name == "mod:read"
    
    # Test relationship linkage
    rp = RolePermission(role=role, permission=permission)
    assert rp.role == role
    assert rp.permission == permission

def test_role_description_exists():
    role = Role(name="admin", description="Administrator")
    assert role.description == "Administrator"

def test_permission_name_format_validation():
    with pytest.raises(ValueError, match="Invalid permission format"):
        Permission(name="invalid_format")
