from fastapi import FastAPI
from app.routers.health import router as health_router
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

app = FastAPI()

app.include_router(health_router, prefix="/health", tags=["health"])

FastAPIInstrumentor.instrument_app(app)

@app.get("/")
async def root():
    return {"message": "Hello World"}
