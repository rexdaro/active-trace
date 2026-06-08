import pytest
import uuid
from app.models.tenant import Tenant

def test_tenant_fields():
    tenant = Tenant(id=uuid.uuid4(), name="Test Tenant")
    assert tenant.name == "Test Tenant"
    assert isinstance(tenant.id, uuid.UUID)

def test_tenant_timestamp_defaults():
    tenant = Tenant(name="Test Tenant")
    # In reality, these are set by the DB. 
    # For unit tests, they might be None until flushed/committed.
    # Let's just check if they are accessible.
    assert hasattr(tenant, "created_at")
    assert hasattr(tenant, "updated_at")
    assert hasattr(tenant, "deleted_at")
