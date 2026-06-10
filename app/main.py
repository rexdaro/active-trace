from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.asignaciones import router as asignaciones_router
from app.middleware.audit import AuditLogMiddleware

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    FastAPIInstrumentor = None

app = FastAPI()
app.add_middleware(AuditLogMiddleware)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(admin_router)
app.include_router(asignaciones_router)

if FastAPIInstrumentor:
    FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}
