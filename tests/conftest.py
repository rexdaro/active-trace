"""
Shared pytest configuration for activia-trace tests.

Importing all models here ensures Base.metadata knows about every table
before any test calls Base.metadata.create_all(). This prevents
ForeignKey constraint failures when models like Carrera reference
tenants.id but Tenant hasn't been imported yet.

Also creates all tables in test.db (used by HTTP endpoint tests via
TestClient) so the audit middleware can log to audit_logs.
"""
import app.models  # noqa: F401 — registers ALL models on Base.metadata

from sqlalchemy import create_engine
from app.models.base import Base

_sync_engine = create_engine("sqlite:///./test.db")
Base.metadata.create_all(_sync_engine)
_sync_engine.dispose()
