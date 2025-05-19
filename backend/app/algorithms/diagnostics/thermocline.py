import numpy as np
from typing import Tuple, List, Dict, Literal
from enum import Enum
from pydantic import BaseModel, Field

class ClineType(str, Enum):
    """跃层类型枚举"""
    TEMPERATURE = "temperature"  # 温度跃层
    DENSITY = "density"          # 密度跃层
    SOUND_SPEED = "sound_speed"  # 声速跃层

def detect_cline(
    depth: np.ndarray,
    profile: np.ndarray,
    cline_type: ClineType,
    window_size: int = 5
) -> Dict[str, float]:
    """
    通用跃层检测函数
    
    Args:
        depth: 深度数组
        profile: 剖面数据（温度/密度/声速）
        cline_type: 跃层类型
        window_size: 平滑窗口大小
    
    Returns:
        Dict包含：
        - cline_depth: 跃层深度
        - max_gradient: 最大梯度
        - upper_value: 跃层上层平均值
        - lower_value: 跃层下层平均值
    """
    # 使用滑动平均平滑数据，减少噪声影响
    kernel = np.ones(window_size) / window_size
    profile_smooth = np.convolve(profile, kernel, mode='valid')
    depth_smooth = depth[window_size-1:]
    
    # 计算梯度
    gradient = np.gradient(profile_smooth, depth_smooth)
    
    if cline_type == ClineType.TEMPERATURE:
        # 温度跃层：寻找最大负梯度
        idx = np.argmin(gradient)
    elif cline_type == ClineType.DENSITY:
        # 密度跃层：寻找最大正梯度
        idx = np.argmax(gradient)
    else:  # ClineType.SOUND_SPEED
        # 声速跃层：寻找最大负梯度（类似温度跃层）
        idx = np.argmin(gradient)
    
    # 计算跃层上下层的平均值
    upper_idx = max(0, idx - window_size)
    lower_idx = min(len(profile_smooth), idx + window_size)
    upper_value = np.mean(profile_smooth[upper_idx:idx])
    lower_value = np.mean(profile_smooth[idx:lower_idx])
    
    return {
        "cline_depth": float(depth_smooth[idx]),
        "max_gradient": float(gradient[idx]),
        "upper_value": float(upper_value),
        "lower_value": float(lower_value)
    }

# FastAPI API 封装
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/diagnostics/cline",
    tags=["diagnostics-cline"]
)

class ClineRequest(BaseModel):
    depth: List[float] = Field(..., description="深度数组（米）")
    profile: List[float] = Field(..., description="剖面数据（温度/密度/声速）")
    cline_type: ClineType = Field(..., description="跃层类型：temperature/density/sound_speed")
    window_size: int = Field(default=5, description="平滑窗口大小", ge=3, le=11)

class ClineResponse(BaseModel):
    cline_depth: float = Field(..., description="跃层深度（米）")
    max_gradient: float = Field(..., description="最大梯度")
    upper_value: float = Field(..., description="跃层上层平均值")
    lower_value: float = Field(..., description="跃层下层平均值")

@router.post("/detect", response_model=ClineResponse, summary="跃层检测（支持温度/密度/声速）")
def detect_cline_api(req: ClineRequest):
    """
    跃层检测API，支持：
    1. 温度跃层 (thermocline)
    2. 密度跃层 (pycnocline)
    3. 声速跃层 (sound speed cline)
    
    输入参数：
    - depth: 深度数组
    - profile: 对应的剖面数据（温度/密度/声速）
    - cline_type: 跃层类型（temperature/density/sound_speed）
    - window_size: 平滑窗口大小（默认5）
    
    返回：
    - cline_depth: 跃层深度
    - max_gradient: 最大梯度
    - upper_value: 跃层上层平均值
    - lower_value: 跃层下层平均值
    """
    try:
        depth = np.array(req.depth)
        profile = np.array(req.profile)
        
        if len(depth) != len(profile):
            raise HTTPException(
                status_code=400,
                detail="深度数组与剖面数据长度不匹配"
            )
            
        result = detect_cline(
            depth=depth,
            profile=profile,
            cline_type=req.cline_type,
            window_size=req.window_size
        )
        return ClineResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"跃层检测失败: {str(e)}"
        )

# 使用示例
"""
# 温度跃层检测
data = {
    "depth": [0, 10, 20, 30, 40, 50],
    "profile": [25, 24, 20, 15, 12, 10],
    "cline_type": "temperature",
    "window_size": 5
}

# 密度跃层检测
data = {
    "depth": [0, 10, 20, 30, 40, 50],
    "profile": [1020, 1021, 1024, 1026, 1027, 1028],
    "cline_type": "density",
    "window_size": 5
}

# 声速跃层检测
data = {
    "depth": [0, 10, 20, 30, 40, 50],
    "profile": [1500, 1498, 1490, 1485, 1482, 1480],
    "cline_type": "sound_speed",
    "window_size": 5
}
"""