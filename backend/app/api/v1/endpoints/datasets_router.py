from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.dataset import Dataset, DatasetCreate, DatasetListItem
from app.services import dataset_service

router = APIRouter(
    prefix="/datasets",
    tags=["datasets"]
)

@router.get("", response_model=List[DatasetListItem], summary="获取数据集列表")
def list_datasets():
    return dataset_service.list_datasets()

@router.get("/{dataset_id}", response_model=Dataset, summary="获取数据集详情")
def get_dataset(dataset_id: str):
    ds = dataset_service.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")
    return ds

@router.post("", response_model=Dataset, summary="注册新数据集")
def create_dataset(data: DatasetCreate):
    return dataset_service.create_dataset(data)

@router.delete("/{dataset_id}", summary="删除数据集")
def delete_dataset(dataset_id: str):
    if dataset_service.delete_dataset(dataset_id):
        return {"id": dataset_id, "message": "数据集已删除"}
    else:
        raise HTTPException(status_code=404, detail="数据集不存在")
