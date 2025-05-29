"""
CF规范检查与转换API端点 - 简化版本
提供NetCDF文件的CF-1.8规范验证和转换功能
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import os
import tempfile
import logging
from pathlib import Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cf", tags=["CF Compliance"])

# 全局CF监控服务实例 - 先设为None，后续实现
cf_monitor_service: Optional[Any] = None


class ValidationRequest(BaseModel):
    """验证请求模型"""
    file_path: str


class ValidationResponse(BaseModel):
    """验证响应模型"""
    is_valid: bool
    cf_version: Optional[str] = None
    critical_issues: int = 0
    warning_issues: int = 0
    info_issues: int = 0
    issues: List[Dict[str, Any]] = []


@router.get("/standards/info")
async def get_cf_standards_info():
    """
    获取CF标准信息
    """
    return {
        "cf_version": "CF-1.8",
        "description": "Climate and Forecast Metadata Conventions",
        "url": "http://cfconventions.org/",
        "required_global_attributes": [
            "Conventions",
            "title", 
            "institution",
            "source",
            "history"
        ],
        "standard_coordinate_names": {
            "longitude": ["longitude", "lon", "x"],
            "latitude": ["latitude", "lat", "y"],
            "time": ["time", "t"],
            "depth": ["depth", "z", "level"]
        },
        "common_units": {
            "temperature": "degree_C",
            "salinity": "psu", 
            "pressure": "dbar",
            "longitude": "degrees_east",
            "latitude": "degrees_north",
            "depth": "m"
        }
    }


@router.get("/monitor/status")
async def get_monitor_status():
    """
    获取CF规范监控服务状态
    """
    if not cf_monitor_service:
        return {"status": "stopped", "message": "监控服务未启动"}
    
    return {
        "status": "running",
        "message": "CF规范监控服务运行中"
    }


@router.post("/validate")
async def validate_netcdf_compliance(request: ValidationRequest):
    """
    验证NetCDF文件的CF-1.8规范符合性 - 基础版本
    """
    try:
        file_path = request.file_path
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 基础验证 - 检查文件是否为NetCDF格式
        if not file_path.lower().endswith(('.nc', '.netcdf', '.nc4')):
            return ValidationResponse(
                is_valid=False,
                critical_issues=1,
                issues=[{
                    'level': 'critical',
                    'code': 'INVALID_FORMAT',
                    'message': '文件格式不是NetCDF格式',
                    'location': 'file',
                    'suggestion': '请提供.nc, .netcdf或.nc4格式的文件'
                }]
            )
        
        # 尝试打开文件进行基础验证
        try:
            import xarray as xr
            with xr.open_dataset(file_path, decode_times=False) as ds:
                issues = []
                critical_count = 0
                warning_count = 0
                
                # 检查Conventions属性
                conventions = ds.attrs.get('Conventions', '')
                if not conventions:
                    issues.append({
                        'level': 'critical',
                        'code': 'MISSING_CONVENTIONS',
                        'message': '缺少Conventions属性',
                        'location': 'global',
                        'suggestion': "添加 Conventions = 'CF-1.8'"
                    })
                    critical_count += 1
                elif 'CF' not in str(conventions):
                    issues.append({
                        'level': 'warning',
                        'code': 'INVALID_CONVENTIONS',
                        'message': f'Conventions属性可能无效: {conventions}',
                        'location': 'global',
                        'suggestion': "建议设置 Conventions = 'CF-1.8'"
                    })
                    warning_count += 1
                
                # 检查基本全局属性
                recommended_attrs = ['title', 'institution', 'source']
                for attr in recommended_attrs:
                    if attr not in ds.attrs:
                        issues.append({
                            'level': 'warning',
                            'code': f'MISSING_{attr.upper()}',
                            'message': f'缺少推荐的全局属性: {attr}',
                            'location': 'global',
                            'suggestion': f'添加 {attr} 属性'
                        })
                        warning_count += 1
                
                is_valid = critical_count == 0
                cf_version = conventions if 'CF' in str(conventions) else None
                
                return ValidationResponse(
                    is_valid=is_valid,
                    cf_version=cf_version,
                    critical_issues=critical_count,
                    warning_issues=warning_count,
                    issues=issues
                )
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"无法读取NetCDF文件: {str(e)}")
            
    except Exception as e:
        logger.error(f"验证文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证文件失败: {str(e)}")


@router.post("/validate-upload")
async def validate_uploaded_file(file: UploadFile = File(...)):
    """
    验证上传的NetCDF文件的CF-1.8规范符合性 - 基础版本
    """
    try:
        # 检查文件格式
        if not file.filename.lower().endswith(('.nc', '.netcdf', '.nc4')):
            raise HTTPException(status_code=400, detail="只支持NetCDF格式文件")
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.nc') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # 调用验证接口
            result = await validate_netcdf_compliance(ValidationRequest(file_path=temp_path))
            return result
            
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            
    except Exception as e:
        logger.error(f"验证上传文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证上传文件失败: {str(e)}")


# 应用启动时的初始化函数
def initialize_cf_monitor(data_dir: str):
    """
    初始化CF监控服务 - 基础版本
    """
    global cf_monitor_service
    
    try:
        if os.path.exists(data_dir):
            logger.info(f"CF监控服务初始化完成，数据目录: {data_dir}")
            # 这里可以后续实现真正的监控服务
            cf_monitor_service = {"data_dir": data_dir, "status": "initialized"}  
        else:
            logger.warning(f"数据目录不存在，跳过CF监控服务初始化: {data_dir}")
    except Exception as e:
        logger.error(f"初始化CF监控服务失败: {str(e)}", exc_info=True)


# 应用关闭时的清理函数
def cleanup_cf_monitor():
    """
    清理CF监控服务 - 基础版本
    """
    global cf_monitor_service
    
    if cf_monitor_service:
        try:
            logger.info("CF监控服务清理完成")
        except Exception as e:
            logger.error(f"清理CF监控服务失败: {str(e)}", exc_info=True)
        finally:
            cf_monitor_service = None
