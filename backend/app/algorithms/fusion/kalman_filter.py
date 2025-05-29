import numpy as np
from typing import Tuple

def kalman_filter(
    observations: np.ndarray,
    initial_state: np.ndarray,
    initial_cov: np.ndarray,
    transition_matrix: np.ndarray,
    observation_matrix: np.ndarray,
    process_noise: np.ndarray,
    observation_noise: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    标准卡尔曼滤波主函数
    observations: 观测序列 (T, m)
    initial_state: 初始状态 (n,)
    initial_cov: 初始协方差 (n, n)
    transition_matrix: 状态转移矩阵 (n, n)
    observation_matrix: 观测矩阵 (m, n)
    process_noise: 系统噪声协方差 (n, n)
    observation_noise: 观测噪声协方差 (m, m)
    返回: 状态估计序列 (T, n), 协方差序列 (T, n, n)
    """
    T = observations.shape[0]
    n = initial_state.shape[0]
    m = observations.shape[1]

    x = initial_state
    P = initial_cov
    xs = []
    Ps = []

    for t in range(T):
        # 预测
        x_pred = transition_matrix @ x
        P_pred = transition_matrix @ P @ transition_matrix.T + process_noise

        # 更新
        y = observations[t] - (observation_matrix @ x_pred)
        S = observation_matrix @ P_pred @ observation_matrix.T + observation_noise
        K = P_pred @ observation_matrix.T @ np.linalg.inv(S)
        x = x_pred + K @ y
        P = (np.eye(n) - K @ observation_matrix) @ P_pred

        xs.append(x.copy())
        Ps.append(P.copy())

    return np.array(xs), np.array(Ps)

# FastAPI API 封装
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List

router = APIRouter(
    prefix="/fusion/kalman",
    tags=["fusion-kalman-filter"]
)

class KFRequest(BaseModel):
    observations: List[List[float]]
    initial_state: List[float]
    initial_cov: List[List[float]]
    transition_matrix: List[List[float]]
    observation_matrix: List[List[float]]
    process_noise: List[List[float]]
    observation_noise: List[List[float]]

class KFResponse(BaseModel):
    state_estimates: List[List[float]]
    covariances: List[List[List[float]]]

from app.core.json import custom_jsonable_encoder

@router.post("/run", response_model=KFResponse, summary="卡尔曼滤波计算")
def run_kf(req: KFRequest):
    xs, Ps = kalman_filter(
        np.array(req.observations),
        np.array(req.initial_state),
        np.array(req.initial_cov),
        np.array(req.transition_matrix),
        np.array(req.observation_matrix),
        np.array(req.process_noise),
        np.array(req.observation_noise)
    )
    
    # 使用我们的自定义JSON编码器
    result = {
        "state_estimates": xs,
        "covariances": Ps
    }
    result = custom_jsonable_encoder(result)
    
    return KFResponse(**result)
