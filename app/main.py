import asyncio
from contextlib import asynccontextmanager

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
from app.routers.comunicaciones import router as comunicaciones_router
from app.routers.encuentros import router as encuentros_router
from app.routers.guardias import router as guardias_router
from app.routers.coloquios import router as coloquios_router
from app.routers.avisos import router as avisos_router
from app.routers.tareas import router as tareas_router
from app.routers.programas import router as programas_router
from app.routers.fechas_academicas import router as fechas_academicas_router
from app.routers.salarios import router as salarios_router
from app.routers.liquidaciones import router as liquidaciones_router
from app.routers.facturas import router as facturas_router
from app.routers.auditoria import router as auditoria_router
from app.routers.perfil import router as perfil_router
from app.routers.inbox import router as inbox_router
from app.middleware.audit import AuditLogMiddleware
from app.workers.comunicaciones import start_worker

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:
    FastAPIInstrumentor = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker_task = start_worker(app)
    yield
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)
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
app.include_router(comunicaciones_router)
app.include_router(encuentros_router)
app.include_router(guardias_router)
app.include_router(coloquios_router)
app.include_router(avisos_router)
app.include_router(tareas_router)
app.include_router(programas_router)
app.include_router(fechas_academicas_router)
app.include_router(salarios_router)
app.include_router(liquidaciones_router)
app.include_router(facturas_router)
app.include_router(auditoria_router)
app.include_router(perfil_router)
app.include_router(inbox_router)

if FastAPIInstrumentor:
    FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}
