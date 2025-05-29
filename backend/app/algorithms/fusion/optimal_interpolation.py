import numpy as np
from scipy.spatial.distance import cdist
from scipy.linalg import solve
from typing import Tuple

def exponential_covariance(d, sigma2, L):
    """
    指数型协方差函数
    d: 距离矩阵
    sigma2: 方差
    L: 相关长度
    """
    return sigma2 * np.exp(-d / L)

def optimal_interpolation(
    obs_coords: np.ndarray,
    obs_values: np.ndarray,
    interp_coords: np.ndarray,
    sigma2: float = 1.0,
    L: float = 1.0,
    noise: float = 1e-6
) -> Tuple[np.ndarray, np.ndarray]:
    """
    最优插值主函数
    obs_coords: 观测点坐标 (N, 2) 或 (N, 1)
    obs_values: 观测值 (N,)
    interp_coords: 插值点坐标 (M, 2) 或 (M, 1)
    sigma2: 信号方差
    L: 相关长度
    noise: 观测噪声
    返回: 插值值 (M,), 插值误差 (M,)
    """
    obs_coords = np.asarray(obs_coords)
    obs_values = np.asarray(obs_values)
    interp_coords = np.asarray(interp_coords)

    # 观测点之间的协方差矩阵
    D_obs = cdist(obs_coords, obs_coords)
    C_obs = exponential_covariance(D_obs, sigma2, L) + np.eye(len(obs_coords)) * noise

    # 插值点与观测点的协方差
    D_interp = cdist(interp_coords, obs_coords)
    C_interp = exponential_covariance(D_interp, sigma2, L)

    # 求解权重
    weights = solve(C_obs, C_interp.T, assume_a='pos').T  # (M, N)

    # 插值估计
    interp_values = weights @ obs_values

    # 插值误差估计
    C0 = sigma2  # 协方差函数在0处的值
    interp_error = np.sqrt(np.maximum(C0 - np.sum(weights * C_interp, axis=1), 0))

    return interp_values, interp_error

# FastAPI API 封装
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(
    prefix="/fusion/oi",
    tags=["fusion-optimal-interpolation"]
)

class OIRequest(BaseModel):
    obs_coords: List[List[float]]
    obs_values: List[float]
    interp_coords: List[List[float]]
    sigma2: Optional[float] = 1.0
    L: Optional[float] = 1.0
    noise: Optional[float] = 1e-6

class OIResponse(BaseModel):
    interp_values: List[float]
    interp_error: List[float]

from app.core.json import custom_jsonable_encoder

@router.post("/run", response_model=OIResponse, summary="最优插值计算")
def run_oi(req: OIRequest):
    interp_values, interp_error = optimal_interpolation(
        np.array(req.obs_coords),
        np.array(req.obs_values),
        np.array(req.interp_coords),
        sigma2=req.sigma2,
        L=req.L,
        noise=req.noise
    )
    
    # 使用自定义JSON编码器处理NumPy类型
    result = {
        "interp_values": interp_values,
        "interp_error": interp_error
    }
    result = custom_jsonable_encoder(result)
    
    return OIResponse(**result)
