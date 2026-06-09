import pytest
from app.models.rbac import Role, Permission, RolePermission

def test_rbac_models_instantiation():
    # Test creation
    role = Role(name="admin")
    permission = Permission(name="read")
    
    assert role.name == "admin"
    assert permission.name == "read"
    
    # Test relationship linkage
    rp = RolePermission(role=role, permission=permission)
    assert rp.role == role
    assert rp.permission == permission
