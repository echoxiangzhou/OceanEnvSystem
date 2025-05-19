import numpy as np
from typing import Tuple

def detect_eddy(ssh: np.ndarray, lat: np.ndarray, lon: np.ndarray, threshold: float = 0.1) -> dict:
    """
    基于海表高度异常（SSH）检测涡旋区域
    返回：涡旋中心坐标及像元索引
    """
    mask = np.abs(ssh) > threshold
    eddy_indices = np.argwhere(mask)
    if eddy_indices.size == 0:
        return {"centers": [], "indices": []}
    centers = []
    for idx in eddy_indices:
        centers.append({"lat": float(lat[idx[0]]), "lon": float(lon[idx[1]])})
    return {"centers": centers, "indices": eddy_indices.tolist()}

# FastAPI API 封装
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/diagnostics/eddy",
    tags=["diagnostics-eddy"]
)

class EddyRequest(BaseModel):
    ssh: List[List[float]]
    lat: List[float]
    lon: List[float]
    threshold: float = 0.1

class EddyResponse(BaseModel):
    centers: List[dict]
    indices: List[List[int]]

@router.post("/detect", response_model=EddyResponse, summary="涡旋检测")
def detect_eddy_api(req: EddyRequest):
    ssh = np.array(req.ssh)
    lat = np.array(req.lat)
    lon = np.array(req.lon)
    result = detect_eddy(ssh, lat, lon, req.threshold)
    return EddyResponse(**result)
