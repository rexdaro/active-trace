from fastapi import FastAPI
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.asignaciones import router as asignaciones_router
from app.routers.carreras import router as carreras_router
from app.routers.cohortes import router as cohortes_router
from app.routers.materias import router as materias_router
from app.routers.equipos import router as equipos_router
from app.routers.padron import router as padron_router
from app.routers.calificaciones import router as calificaciones_router
from app.routers.analisis import router as analisis_router
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
app.include_router(carreras_router, prefix="/api/carreras")
app.include_router(cohortes_router, prefix="/api/cohortes")
app.include_router(materias_router, prefix="/api/materias")
app.include_router(equipos_router)
app.include_router(padron_router)
app.include_router(calificaciones_router)
app.include_router(analisis_router)

if FastAPIInstrumentor:
    FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}
