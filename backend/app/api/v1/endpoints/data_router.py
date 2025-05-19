from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict
import os
from fastapi.responses import FileResponse

# 实际数据目录
DATA_ROOT = "backend/docker/thredds/oceanenv"

router = APIRouter(
    prefix="/data",
    tags=["data"]
)

def find_files_by_ext(root: str, ext: str) -> List[str]:
    """
    递归查找所有指定扩展名的文件，返回相对路径列表
    """
    result = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith(ext):
                rel_path = os.path.relpath(os.path.join(dirpath, f), root)
                result.append(rel_path)
    return result

@router.get("/list", summary="获取所有 NetCDF 数据集文件（递归子目录）")
def list_datasets(ext: str = "nc") -> List[str]:
    """
    获取所有指定类型的数据文件（默认.nc），返回相对路径
    """
    return find_files_by_ext(DATA_ROOT, f".{ext}")

@router.get("/metadata", summary="获取指定数据集的元数据")
def get_metadata(relpath: str):
    """
    relpath: 数据文件的相对路径（相对于 DATA_ROOT）
    """
    import xarray as xr
    file_path = os.path.join(DATA_ROOT, relpath)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    ds = xr.open_dataset(file_path)
    metadata = {
        "variables": list(ds.variables),
        "dims": dict(ds.dims),
        "attrs": dict(ds.attrs),
    }
    ds.close()
    return metadata

@router.get("/download", summary="下载指定数据集文件")
def download_dataset(relpath: str):
    """
    relpath: 数据文件的相对路径（相对于 DATA_ROOT）
    """
    file_path = os.path.join(DATA_ROOT, relpath)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    filename = os.path.basename(file_path)
    # 可根据实际类型设置 media_type
    return FileResponse(file_path, filename=filename, media_type="application/octet-stream")
