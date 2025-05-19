from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.data_converter import DataConverter
import os
import shutil

router = APIRouter(
    prefix="/data/convert",
    tags=["data-convert"]
)

# 假设NetCDF输出目录为thredds数据目录
NETCDF_OUTPUT_DIR = "backend/docker/thredds/oceanenv/converted"
os.makedirs(NETCDF_OUTPUT_DIR, exist_ok=True)

converter = DataConverter(NETCDF_OUTPUT_DIR)

@router.post("", summary="数据文件格式转换为NetCDF")
async def convert_data_file(
    file: UploadFile = File(...),
    file_type: str = Form(...)
):
    try:
        # 保存上传文件到临时路径
        temp_path = os.path.join(NETCDF_OUTPUT_DIR, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        # 转换
        nc_path = converter.convert(temp_path, file_type)
        # 删除临时文件
        os.remove(temp_path)
        return {"netcdf_path": nc_path, "message": "转换成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")
