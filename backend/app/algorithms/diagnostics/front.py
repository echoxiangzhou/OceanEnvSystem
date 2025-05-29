import numpy as np
from typing import Tuple

def detect_front(sst: np.ndarray, lat: np.ndarray, lon: np.ndarray, gradient_threshold: float = 0.5) -> dict:
    """
    基于海表温度（SST）梯度检测锋面
    返回：锋面像元索引及中心坐标
    """
    dTdy, dTdx = np.gradient(sst, lat, lon)
    grad_mag = np.sqrt(dTdx**2 + dTdy**2)
    mask = grad_mag > gradient_threshold
    front_indices = np.argwhere(mask)
    centers = []
    for idx in front_indices:
        centers.append({"lat": float(lat[idx[0]]), "lon": float(lon[idx[1]])})
    return {"centers": centers, "indices": front_indices.tolist()}

# FastAPI API 封装
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/diagnostics/front",
    tags=["diagnostics-front"]
)

class FrontRequest(BaseModel):
    sst: List[List[float]]
    lat: List[float]
    lon: List[float]
    gradient_threshold: float = 0.5

class FrontResponse(BaseModel):
    centers: List[dict]
    indices: List[List[int]]

from app.core.json import custom_jsonable_encoder

@router.post("/detect", response_model=FrontResponse, summary="锋面检测")
def detect_front_api(req: FrontRequest):
    sst = np.array(req.sst)
    lat = np.array(req.lat)
    lon = np.array(req.lon)
    result = detect_front(sst, lat, lon, req.gradient_threshold)
    # 确保结果中的NumPy类型被转换为Python原生类型
    return FrontResponse(**custom_jsonable_encoder(result))
