from fastapi import APIRouter
from app.algorithms.diagnostics import thermocline, eddy, front

router = APIRouter(
    prefix="/diagnostics",
    tags=["diagnostics"]
)

# 跃层检测（温度/密度/声速）
router.include_router(thermocline.router, prefix="/cline", tags=["diagnostics-cline"])

# 涡旋检测
router.include_router(eddy.router, prefix="/eddy", tags=["diagnostics-eddy"])

# 锋面检测
router.include_router(front.router, prefix="/front", tags=["diagnostics-front"])
