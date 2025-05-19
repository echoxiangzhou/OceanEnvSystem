from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

@app.get("/")
def root():
    return {"message": "Welcome to the Ocean Environment System API!"}

from app.api.v1.endpoints import data_router, fusion_router, diagnostics_router, products_router, datasets_router, diagnostic_tasks_router, data_convert_router, opendap_client_router
from app.algorithms.fusion import optimal_interpolation, kalman_filter
from app.algorithms.diagnostics import thermocline, eddy, front

app.include_router(data_router.router, prefix=settings.API_V1_STR, tags=["data"])
app.include_router(optimal_interpolation.router, prefix=settings.API_V1_STR, tags=["fusion-optimal-interpolation"])
app.include_router(kalman_filter.router, prefix=settings.API_V1_STR, tags=["fusion-kalman-filter"])
app.include_router(fusion_router.router, prefix=settings.API_V1_STR, tags=["fusion"])
app.include_router(thermocline.router, prefix=settings.API_V1_STR, tags=["diagnostics-cline"])
app.include_router(eddy.router, prefix=settings.API_V1_STR, tags=["diagnostics-eddy"])
app.include_router(front.router, prefix=settings.API_V1_STR, tags=["diagnostics-front"])
app.include_router(diagnostics_router.router, prefix=settings.API_V1_STR, tags=["diagnostics"])
app.include_router(products_router.router, prefix=settings.API_V1_STR, tags=["products"])
app.include_router(datasets_router.router, prefix=settings.API_V1_STR, tags=["datasets"])
app.include_router(diagnostic_tasks_router.router, prefix=settings.API_V1_STR, tags=["diagnostic-tasks"])
app.include_router(data_convert_router.router, prefix=settings.API_V1_STR, tags=["data-convert"])
app.include_router(opendap_client_router.router, prefix=settings.API_V1_STR, tags=["opendap-client"])
