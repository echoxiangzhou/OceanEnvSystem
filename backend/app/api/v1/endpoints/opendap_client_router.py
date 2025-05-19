from fastapi import APIRouter, HTTPException, Query
from app.services.data_client import OpendapClient
from typing import List, Optional
import os

router = APIRouter(
    prefix="/opendap",
    tags=["opendap-client"]
)

# 假设TDS服务基础URL
TDS_BASE_URL = os.environ.get("TDS_BASE_URL", "http://localhost:8080")
client = OpendapClient(TDS_BASE_URL)

@router.get("/open", summary="通过OPeNDAP打开远程数据集，返回变量名和维度")
def open_dataset(dataset_path: str):
    try:
        ds = client.open_dataset(dataset_path)
        info = {
            "variables": list(ds.variables),
            "dims": dict(ds.dims),
            "attrs": dict(ds.attrs)
        }
        ds.close()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OPeNDAP访问失败: {str(e)}")

@router.get("/metadata", summary="获取OPeNDAP数据集元数据")
def get_metadata(dataset_path: str):
    try:
        return client.get_metadata(dataset_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OPeNDAP元数据获取失败: {str(e)}")
