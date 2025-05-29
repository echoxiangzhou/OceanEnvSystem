from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from app.core.json import NumpyEncoder
import json
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加NumPy序列化中间件
# 注意：中间件按照添加顺序反向执行，最后添加的先执行
from app.core.middleware import NumpySerializationMiddleware
app.add_middleware(NumpySerializationMiddleware)

# 添加GZip压缩，减少网络传输大小
# 必须在NumPy序列化之后添加，确保先序列化后压缩
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 设置全局JSON编码器
from app.core.json import custom_jsonable_encoder, NumpyEncoder
from fastapi.encoders import jsonable_encoder as original_jsonable_encoder

# 替换FastAPI的jsonable_encoder
from fastapi import encoders
encoders.jsonable_encoder = custom_jsonable_encoder

# 自定义JSON响应类
class NumpyJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            cls=NumpyEncoder,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# 设置默认响应类
app.json_response_class = NumpyJSONResponse

@app.get("/")
def root():
    return {
        "message": "Welcome to the Ocean Environment System API!",
        "features": [
            "多源海洋数据融合",
            "海洋环境诊断分析", 
            "CF-1.8规范检查与转换",
            "可视化产品生成",
            "元数据管理"
        ],
        "version": settings.VERSION
    }

from app.api.v1.endpoints import data_router, fusion_router, diagnostics_router, products_router, datasets_router, diagnostic_tasks_router, data_convert_router, opendap_client_router, metadata_router
# 使用完整版本的CF路由，包含监控功能
from app.api.v1.endpoints import cf_router
from app.algorithms.fusion import optimal_interpolation, kalman_filter
from app.algorithms.diagnostics import thermocline, eddy, front

# CF规范监控服务
from app.api.v1.endpoints.cf_router import initialize_cf_monitor, cleanup_cf_monitor
import os

# 应用启动事件
@app.on_event("startup")
async def startup_event():
    # 创建数据库表
    try:
        from app.db.session import engine
        from app.db.models import Base
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功")
    except Exception as e:
        print(f"创建数据库表失败: {e}")
    
    # 初始化CF监控服务
    data_dir = os.environ.get("DATA_DIR", "/Users/echo/codeProjects/OceanEnvSystem/OceanEnvSystem/backend/docker/thredds/data/oceanenv")
    initialize_cf_monitor(data_dir)

# 应用关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    # 清理CF监控服务
    cleanup_cf_monitor()

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
app.include_router(cf_router.router, prefix=settings.API_V1_STR, tags=["cf-compliance"])
app.include_router(metadata_router.router, prefix=settings.API_V1_STR, tags=["metadata-management"])
