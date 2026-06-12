import pytest
from sqlalchemy.exc import SQLAlchemyError
from app.models.audit import AuditLog
from app.core.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_audit_log_append_only():
    async with AsyncSessionLocal() as db:
        # Create
        audit = AuditLog(
            action="test_action",
            user_id="user1",
            resource="res1",
            status="status1",
            actor_id="actor1",
            detalle={},
            filas_afectadas=1
        )
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        
        # Attempt to Update (Should fail)
        audit.action = "changed_action"
        with pytest.raises(SQLAlchemyError):
            await db.commit()
        
        # Attempt to Delete (Should fail)
        # Note: Need to reload to clear the failed state if needed, 
        # but the test should fail before that anyway if it wasn't append-only
        await db.delete(audit)
        with pytest.raises(SQLAlchemyError):
            await db.commit()
