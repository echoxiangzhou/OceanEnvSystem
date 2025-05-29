from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.data_converter import DataConverter
import os
import shutil
from pathlib import Path

router = APIRouter(
    prefix="/data/convert",
    tags=["data-convert"]
)

# 获取基础目录
BASE_DATA_DIR = os.path.join("backend", "docker", "thredds", "data", "oceanenv")
RAW_DIR = os.path.join(BASE_DATA_DIR, "raw")
STANDARD_DIR = os.path.join(BASE_DATA_DIR, "standard") 
PROCESSING_DIR = os.path.join(BASE_DATA_DIR, "processing")

# 确保目录存在
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(STANDARD_DIR, exist_ok=True)
os.makedirs(PROCESSING_DIR, exist_ok=True)

converter = DataConverter(PROCESSING_DIR)  # 使用processing作为临时工作目录

@router.post("", summary="数据文件格式转换为NetCDF")
async def convert_data_file(
    file: UploadFile = File(...),
    file_type: str = Form(...)
):
    try:
        # 1. 保存上传文件到raw目录
        raw_file_path = os.path.join(RAW_DIR, file.filename)
        with open(raw_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. 转换文件，指定输出到standard目录
        output_filename = Path(file.filename).stem + ".nc"
        standard_file_path = os.path.join(STANDARD_DIR, output_filename)
        
        # 使用自定义转换逻辑
        nc_path = converter.convert_to_path(raw_file_path, standard_file_path, file_type)
        
        # 3. 转换成功后删除raw目录中的原文件
        if os.path.exists(nc_path) and os.path.exists(raw_file_path):
            os.remove(raw_file_path)
        
        # 返回相对于standard目录的路径
        relative_path = os.path.relpath(nc_path, STANDARD_DIR)
        
        return {
            "netcdf_path": f"standard/{relative_path}",
            "message": "转换成功，文件已保存到standard目录"
        }
        
    except Exception as e:
        # 转换失败时，保留raw目录中的文件供手动处理
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")
