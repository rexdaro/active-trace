from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.audit import AuditService
from app.core.database import AsyncSessionLocal

class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Extract headers (simulating auth context)
        user_id = request.headers.get("X-User-ID", "anonymous")
        impersonator_id = request.headers.get("X-Impersonator-ID", None)
        
        # Process the request
        response = await call_next(request)
        
        # Log action
        async with AsyncSessionLocal() as db:
            await AuditService.log_action(
                db=db,
                action=request.method + " " + request.url.path,
                user_id=user_id,
                resource=request.url.path,
                status=str(response.status_code),
                actor_id=user_id,
                impersonator_id=impersonator_id,
                detalle={"headers": dict(request.headers)},
                filas_afectadas=0
            )
        
        return response
