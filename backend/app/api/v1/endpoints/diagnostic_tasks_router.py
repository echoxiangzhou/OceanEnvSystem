from fastapi import APIRouter, HTTPException, Request
from app.services import diagnostic_task_manager

router = APIRouter(
    prefix="/diagnostics/tasks",
    tags=["diagnostic-tasks"]
)

@router.post("", summary="提交诊断异步任务")
async def submit_diagnostic_task(request: Request):
    data = await request.json()
    diag_type = data.get("diagnostic_type")
    if diag_type == "cline":
        from app.algorithms.diagnostics.thermocline import detect_cline_api, ClineRequest
        def task_func(data):
            req = ClineRequest(**data)
            return detect_cline_api(req)
    elif diag_type == "eddy":
        from app.algorithms.diagnostics.eddy import detect_eddy_api, EddyRequest
        def task_func(data):
            req = EddyRequest(**data)
            return detect_eddy_api(req)
    elif diag_type == "front":
        from app.algorithms.diagnostics.front import detect_front_api, FrontRequest
        def task_func(data):
            req = FrontRequest(**data)
            return detect_front_api(req)
    else:
        raise HTTPException(status_code=400, detail="不支持的诊断类型")
    task_id = diagnostic_task_manager.enqueue_task(task_func, data)
    return {"task_id": task_id, "status": "queued"}

@router.get("/{task_id}", summary="查询诊断任务状态与结果")
def get_diagnostic_task_status(task_id: str):
    try:
        return diagnostic_task_manager.get_task_status(task_id)
    except Exception:
        raise HTTPException(status_code=404, detail="任务不存在")

@router.delete("/{task_id}", summary="取消/删除诊断任务")
def cancel_diagnostic_task(task_id: str):
    if diagnostic_task_manager.cancel_task(task_id):
        return {"task_id": task_id, "status": "cancelled"}
    else:
        raise HTTPException(status_code=404, detail="任务不存在或无法取消")

@router.get("", summary="获取诊断任务列表")
def list_diagnostic_tasks(status: str = None, limit: int = 20):
    return diagnostic_task_manager.list_tasks(status=status, limit=limit)
