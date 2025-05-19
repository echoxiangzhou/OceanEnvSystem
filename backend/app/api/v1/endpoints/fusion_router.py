from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict
from app.services.task_manager import enqueue_task, get_task_status, cancel_task, list_tasks
import uuid

router = APIRouter(
    prefix="/fusion",
    tags=["fusion"]
)

@router.get("/algorithms", summary="获取可用融合算法列表")
def list_algorithms() -> List[Dict[str, str]]:
    return [
        {"name": "optimal_interpolation", "label": "最优插值", "path": "/fusion/oi/run"},
        {"name": "kalman_filter", "label": "卡尔曼滤波", "path": "/fusion/kalman/run"}
    ]

@router.post("/run_async", summary="融合算法异步任务入口")
async def fusion_run_async(request: Request):
    data = await request.json()
    algo = data.get("algorithm")
    if algo == "optimal_interpolation":
        from app.algorithms.fusion.optimal_interpolation import optimal_interpolation, OIRequest
        def task_func(data):
            req = OIRequest(**data)
            return optimal_interpolation(
                req.obs_coords, req.obs_values, req.interp_coords,
                req.sigma2, req.L, req.noise
            )
    elif algo == "kalman_filter":
        from app.algorithms.fusion.kalman_filter import kalman_filter, KFRequest
        def task_func(data):
            req = KFRequest(**data)
            return kalman_filter(
                req.observations, req.initial_state, req.initial_cov,
                req.transition_matrix, req.observation_matrix,
                req.process_noise, req.observation_noise
            )
    else:
        raise HTTPException(status_code=400, detail="不支持的算法类型")
    task_id = enqueue_task(task_func, data)
    return {"task_id": task_id, "status": "queued"}

@router.get("/task_status/{task_id}", summary="查询融合任务状态与结果")
def fusion_task_status(task_id: str):
    try:
        return get_task_status(task_id)
    except Exception:
        raise HTTPException(status_code=404, detail="任务不存在")

@router.post("/run", summary="融合算法统一入口")
async def fusion_run(request: Request):
    data = await request.json()
    algo = data.get("algorithm")
    if algo == "optimal_interpolation":
        from app.algorithms.fusion.optimal_interpolation import run_oi, OIRequest
        req = OIRequest(**data)
        return await run_oi(req)
    elif algo == "kalman_filter":
        from app.algorithms.fusion.kalman_filter import run_kf, KFRequest
        req = KFRequest(**data)
        return await run_kf(req)
    else:
        raise HTTPException(status_code=400, detail="不支持的算法类型")

@router.delete("/task/{task_id}", summary="取消/删除融合任务")
def fusion_cancel_task(task_id: str):
    if cancel_task(task_id):
        return {"task_id": task_id, "status": "cancelled"}
    else:
        raise HTTPException(status_code=404, detail="任务不存在或无法取消")

@router.get("/tasks", summary="获取融合任务列表")
def fusion_list_tasks(status: str = None, limit: int = 20):
    return list_tasks(status=status, limit=limit)
