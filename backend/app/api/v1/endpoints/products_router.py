from fastapi import APIRouter, HTTPException
from app.services.product_service import ProductService
from pydantic import BaseModel
from typing import Dict, Any
import os

router = APIRouter(
    prefix="/products",
    tags=["products"]
)

# 假设产品输出目录
PRODUCT_OUTPUT_DIR = "backend/docker/products"
if not os.path.exists(PRODUCT_OUTPUT_DIR):
    os.makedirs(PRODUCT_OUTPUT_DIR)

service = ProductService(PRODUCT_OUTPUT_DIR)

class ReportConfig(BaseModel):
    config: Dict[str, Any]

@router.post("/generate", summary="生成分析报告")
def generate_report_api(cfg: ReportConfig):
    try:
        report_path = service.generate_report(cfg.config)
        return {"report_path": report_path, "message": "报告生成成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
