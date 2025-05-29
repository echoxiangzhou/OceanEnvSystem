"""
CF规范检查与转换API端点
提供NetCDF文件的CF-1.8规范验证和转换功能
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import List, Dict, Any, Optional
import os
import tempfile
import logging
from pathlib import Path
import asyncio
from pydantic import BaseModel

from app.services.cf_validator import validate_netcdf_file, ValidationResult, ValidationLevel
from app.services.cf_converter import convert_netcdf_to_cf
from app.services.cf_monitor import CFMonitorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cf", tags=["CF Compliance"])

# 全局CF监控服务实例
cf_monitor_service: Optional[CFMonitorService] = None


class ValidationRequest(BaseModel):
    """验证请求模型"""
    file_path: str


class ConversionRequest(BaseModel):
    """转换请求模型"""
    input_path: str
    output_path: Optional[str] = None
    auto_fix: bool = True
    backup: bool = True


class ValidationResponse(BaseModel):
    """验证响应模型"""
    is_valid: bool
    cf_version: Optional[str]
    critical_issues: int
    warning_issues: int
    info_issues: int
    issues: List[Dict[str, Any]]


class ConversionResponse(BaseModel):
    """转换响应模型"""
    success: bool
    message: str
    output_path: Optional[str] = None
    issues_fixed: List[Dict[str, Any]]
    remaining_issues: List[Dict[str, Any]]
    backup_path: Optional[str] = None


@router.post("/validate", response_model=ValidationResponse)
async def validate_netcdf_compliance(request: ValidationRequest):
    """
    验证NetCDF文件的CF-1.8规范符合性
    """
    try:
        file_path = request.file_path
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 验证文件
        validation_result = validate_netcdf_file(file_path)
        
        # 统计问题数量
        critical_count = len([i for i in validation_result.issues if i.level == ValidationLevel.CRITICAL])
        warning_count = len([i for i in validation_result.issues if i.level == ValidationLevel.WARNING])
        info_count = len([i for i in validation_result.issues if i.level == ValidationLevel.INFO])
        
        # 格式化问题列表
        issues = [
            {
                'level': issue.level.value,
                'code': issue.code,
                'message': issue.message,
                'location': issue.location,
                'suggestion': issue.suggestion
            }
            for issue in validation_result.issues
        ]
        
        return ValidationResponse(
            is_valid=validation_result.is_valid,
            cf_version=validation_result.cf_version,
            critical_issues=critical_count,
            warning_issues=warning_count,
            info_issues=info_count,
            issues=issues
        )
        
    except Exception as e:
        logger.error(f"验证文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证文件失败: {str(e)}")


@router.post("/validate-upload")
async def validate_uploaded_file(file: UploadFile = File(...)):
    """
    验证上传的NetCDF文件的CF-1.8规范符合性，并暂存文件
    """
    try:
        # 检查文件格式
        if not file.filename.lower().endswith(('.nc', '.netcdf', '.nc4')):
            raise HTTPException(status_code=400, detail="只支持NetCDF格式文件")
        
        logger.info(f"开始验证上传文件: {file.filename}")
        
        # 创建uploads目录
        uploads_dir = os.path.join(os.getcwd(), "data", "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        
        # 保存文件到uploads目录
        file_path = os.path.join(uploads_dir, file.filename)
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        logger.info(f"文件大小: {len(content)} bytes")
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"文件已暂存: {file_path}")
        
        # 验证文件
        validation_result = validate_netcdf_file(file_path)
        
        logger.info(f"验证完成，结果: {validation_result.is_valid}")
        
        # 统计问题数量
        critical_count = len([i for i in validation_result.issues if i.level == ValidationLevel.CRITICAL])
        warning_count = len([i for i in validation_result.issues if i.level == ValidationLevel.WARNING])
        info_count = len([i for i in validation_result.issues if i.level == ValidationLevel.INFO])
        
        # 格式化问题列表
        issues = [
            {
                'level': issue.level.value,
                'code': issue.code,
                'message': issue.message,
                'location': issue.location,
                'suggestion': issue.suggestion
            }
            for issue in validation_result.issues
        ]
        
        # 返回验证结果和文件路径
        response = ValidationResponse(
            is_valid=validation_result.is_valid,
            cf_version=validation_result.cf_version,
            critical_issues=critical_count,
            warning_issues=warning_count,
            info_issues=info_count,
            issues=issues
        )
        
        # 添加文件路径到响应中
        response_dict = response.dict()
        response_dict['file_path'] = file_path
        response_dict['file_name'] = file.filename
        
        return response_dict
        
    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        logger.error(f"验证上传文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"验证上传文件失败: {str(e)}")


@router.post("/convert", response_model=ConversionResponse)
async def convert_netcdf_to_cf_standard(request: ConversionRequest):
    """
    将NetCDF文件转换为CF-1.8标准格式
    """
    try:
        input_path = request.input_path
        output_path = request.output_path
        
        # 检查输入文件是否存在
        if not os.path.exists(input_path):
            raise HTTPException(status_code=404, detail=f"输入文件不存在: {input_path}")
        
        # 如果未指定输出路径，则在同目录下生成
        if not output_path:
            input_pathobj = Path(input_path)
            output_path = str(input_pathobj.parent / f"{input_pathobj.stem}_cf{input_pathobj.suffix}")
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 转换文件
        convert_result = convert_netcdf_to_cf(
            input_path=input_path,
            output_path=output_path,
            auto_fix=request.auto_fix,
            backup=request.backup
        )
        
        return ConversionResponse(
            success=convert_result['success'],
            message=convert_result['message'],
            output_path=output_path if convert_result['success'] else None,
            issues_fixed=convert_result.get('issues_fixed', []),
            remaining_issues=convert_result.get('remaining_issues', []),
            backup_path=convert_result.get('backup_path')
        )
        
    except Exception as e:
        logger.error(f"转换文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"转换文件失败: {str(e)}")


@router.post("/convert-upload")
async def convert_uploaded_file(
    file: UploadFile = File(...),
    auto_fix: bool = Query(True, description="是否自动修复问题"),
    data_dir: str = Query("/app/data", description="数据存储目录")
):
    """
    转换上传的NetCDF文件为CF-1.8标准格式
    """
    try:
        # 检查文件格式
        if not file.filename.lower().endswith(('.nc', '.netcdf', '.nc4')):
            raise HTTPException(status_code=400, detail="只支持NetCDF格式文件")
        
        # 保存上传的文件
        input_dir = os.path.join(data_dir, "uploads")
        os.makedirs(input_dir, exist_ok=True)
        
        input_path = os.path.join(input_dir, file.filename)
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 设置输出路径
        output_dir = os.path.join(data_dir, "standard")
        os.makedirs(output_dir, exist_ok=True)
        
        filename_without_ext = Path(file.filename).stem
        output_path = os.path.join(output_dir, f"{filename_without_ext}_cf.nc")
        
        # 转换文件
        convert_result = convert_netcdf_to_cf(
            input_path=input_path,
            output_path=output_path,
            auto_fix=auto_fix,
            backup=True
        )
        
        # 清理上传的临时文件（如果转换成功）
        if convert_result['success']:
            try:
                os.unlink(input_path)
            except:
                pass
        
        return ConversionResponse(
            success=convert_result['success'],
            message=convert_result['message'],
            output_path=output_path if convert_result['success'] else None,
            issues_fixed=convert_result.get('issues_fixed', []),
            remaining_issues=convert_result.get('remaining_issues', []),
            backup_path=convert_result.get('backup_path')
        )
        
    except Exception as e:
        logger.error(f"转换上传文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"转换上传文件失败: {str(e)}")


@router.get("/monitor/status")
async def get_monitor_status():
    """
    获取CF规范监控服务状态
    """
    global cf_monitor_service
    
    if not cf_monitor_service:
        return {"status": "stopped", "message": "监控服务未启动"}
    
    # 获取详细状态
    detailed_status = cf_monitor_service.get_monitor_status()
    
    return {
        "status": "running" if detailed_status.get("service_running") else "stopped",
        "data_dir": detailed_status.get("data_dir"),
        "processing_results_count": detailed_status.get("processing_results_count", 0),
        "monitoring_active": detailed_status.get("monitoring_active", False),
        "observer_running": detailed_status.get("observer_running", False),
        "pending_files_count": detailed_status.get("count", 0),
        "pending_files": detailed_status.get("pending_files", [])
    }


@router.post("/monitor/start")
async def start_cf_monitor(data_dir: str = Query(..., description="数据目录路径")):
    """
    启动CF规范监控服务
    """
    global cf_monitor_service
    
    try:
        if cf_monitor_service and cf_monitor_service.monitor:
            return {"message": "监控服务已经在运行"}
        
        # 检查数据目录是否存在
        if not os.path.exists(data_dir):
            raise HTTPException(status_code=404, detail=f"数据目录不存在: {data_dir}")
        
        # 创建并启动监控服务
        cf_monitor_service = CFMonitorService(data_dir)
        cf_monitor_service.start()
        
        return {"message": f"监控服务已启动，监控目录: {data_dir}"}
        
    except Exception as e:
        logger.error(f"启动监控服务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"启动监控服务失败: {str(e)}")


@router.post("/monitor/stop")
async def stop_cf_monitor():
    """
    停止CF规范监控服务
    """
    global cf_monitor_service
    
    try:
        if not cf_monitor_service:
            return {"message": "监控服务未启动"}
        
        cf_monitor_service.stop()
        cf_monitor_service = None
        
        return {"message": "监控服务已停止"}
        
    except Exception as e:
        logger.error(f"停止监控服务失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"停止监控服务失败: {str(e)}")


@router.get("/monitor/results")
async def get_processing_results(limit: int = Query(50, description="返回结果数量限制")):
    """
    获取文件处理结果
    """
    global cf_monitor_service
    
    if not cf_monitor_service:
        raise HTTPException(status_code=404, detail="监控服务未启动")
    
    results = cf_monitor_service.get_processing_results(limit)
    
    return {
        "total": len(results),
        "results": results
    }


@router.post("/monitor/scan")
async def scan_data_directory():
    """
    手动扫描数据目录中的NetCDF文件
    """
    global cf_monitor_service
    
    if not cf_monitor_service:
        raise HTTPException(status_code=404, detail="监控服务未启动")
    
    try:
        cf_monitor_service.scan_directory()
        return {"message": "目录扫描已启动"}
        
    except Exception as e:
        logger.error(f"扫描目录失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"扫描目录失败: {str(e)}")


@router.post("/monitor/process-file")
async def process_file_manually(file_path: str = Query(..., description="文件路径")):
    """
    手动处理指定的NetCDF文件
    """
    global cf_monitor_service
    
    if not cf_monitor_service:
        raise HTTPException(status_code=404, detail="监控服务未启动")
    
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        result = cf_monitor_service.process_file_manually(file_path)
        return result
        
    except Exception as e:
        logger.error(f"手动处理文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"手动处理文件失败: {str(e)}")


@router.get("/download/{file_path:path}")
async def download_converted_file(file_path: str):
    """
    下载转换后的CF标准文件
    """
    try:
        # 安全检查：确保文件路径在允许的目录内
        abs_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        # 检查文件是否为NetCDF格式
        if not abs_path.lower().endswith(('.nc', '.netcdf', '.nc4')):
            raise HTTPException(status_code=400, detail="只能下载NetCDF格式文件")
        
        filename = os.path.basename(abs_path)
        
        return FileResponse(
            path=abs_path,
            filename=filename,
            media_type='application/octet-stream'
        )
        
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")


@router.get("/directory/structure")
async def get_directory_structure(data_dir: str = Query(..., description="数据目录路径")):
    """
    获取数据目录的分层结构
    """
    try:
        if not os.path.exists(data_dir):
            raise HTTPException(status_code=404, detail=f"目录不存在: {data_dir}")
        
        data_path = Path(data_dir)
        structure = {
            "raw": [],
            "processing": [],
            "standard": []
        }
        
        # 扫描各个子目录
        for subdir in ["raw", "processing", "standard"]:
            subdir_path = data_path / subdir
            if subdir_path.exists():
                for pattern in ['**/*.nc', '**/*.netcdf', '**/*.nc4']:
                    files = list(subdir_path.glob(pattern))
                    for file_path in files:
                        rel_path = file_path.relative_to(subdir_path)
                        structure[subdir].append({
                            "name": file_path.name,
                            "path": str(rel_path),
                            "full_path": str(file_path),
                            "size": file_path.stat().st_size,
                            "modified": file_path.stat().st_mtime
                        })
        
        return structure
        
    except Exception as e:
        logger.error(f"获取目录结构失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取目录结构失败: {str(e)}")


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


# 应用启动时的初始化函数
def initialize_cf_monitor(data_dir: str):
    """
    初始化CF监控服务
    """
    global cf_monitor_service
    
    try:
        if os.path.exists(data_dir):
            cf_monitor_service = CFMonitorService(data_dir)
            cf_monitor_service.start()
            logger.info(f"CF监控服务已自动启动，监控目录: {data_dir}")
        else:
            logger.warning(f"数据目录不存在，跳过自动启动CF监控服务: {data_dir}")
    except Exception as e:
        logger.error(f"初始化CF监控服务失败: {str(e)}", exc_info=True)


# 应用关闭时的清理函数
def cleanup_cf_monitor():
    """
    清理CF监控服务
    """
    global cf_monitor_service
    
    if cf_monitor_service:
        try:
            cf_monitor_service.stop()
            logger.info("CF监控服务已停止")
        except Exception as e:
            logger.error(f"停止CF监控服务失败: {str(e)}", exc_info=True)
        finally:
            cf_monitor_service = None


@router.get("/monitor/pending")
async def get_pending_files():
    """
    获取待处理文件状态
    """
    global cf_monitor_service
    
    if not cf_monitor_service:
        raise HTTPException(status_code=404, detail="监控服务未启动")
    
    try:
        pending_status = cf_monitor_service.get_pending_files_status()
        return {
            "success": True,
            "pending_files": pending_status.get("pending_files", []),
            "count": pending_status.get("count", 0),
            "message": f"当前有 {pending_status.get('count', 0)} 个文件待处理"
        }
        
    except Exception as e:
        logger.error(f"获取待处理文件状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取待处理文件状态失败: {str(e)}")


@router.post("/convert-and-extract")
async def convert_file_and_extract_metadata(
    file_path: str = Query(..., description="uploads目录中的文件路径"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    转换文件为CF标准格式并提取元数据保存到数据库
    """
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        logger.info(f"开始转换文件并提取元数据: {file_path}")
        
        # 设置最终输出路径 - 直接保存到Thredds数据目录
        thredds_data_dir = os.path.join(os.getcwd(), "docker", "thredds", "data", "oceanenv", "standard")
        os.makedirs(thredds_data_dir, exist_ok=True)
        
        # 确保processing目录存在（用于备份文件）
        processing_dir = os.path.join(os.getcwd(), "data", "processing")
        os.makedirs(processing_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        filename_without_ext = Path(filename).stem
        
        # 直接转换到最终的Thredds目录
        output_path = os.path.join(thredds_data_dir, f"{filename_without_ext}_cf.nc")
        
        # 转换文件 - convert_netcdf_to_cf函数内部会：
        # 1. 将原始文件备份到processing目录
        # 2. 转换文件并直接保存到指定的output_path
        # 3. 提取元数据并保存到数据库
        convert_result = convert_netcdf_to_cf(
            input_path=file_path,
            output_path=output_path,
            auto_fix=True,
            backup=True
        )
        
        if not convert_result['success']:
            raise HTTPException(status_code=500, detail=f"文件转换失败: {convert_result['message']}")
        
        logger.info(f"文件已成功转换: {file_path} -> {output_path}")
        
        # 在后台任务中删除uploads文件
        background_tasks.add_task(delete_upload_file, file_path)
        
        # 查询已保存的元数据记录ID
        from app.db.session import SessionLocal
        from app.db.models import NetCDFMetadata
        
        session = SessionLocal()
        try:
            # 查找已保存的元数据记录
            metadata_record = session.query(NetCDFMetadata).filter(
                NetCDFMetadata.file_path == output_path
            ).first()
            
            metadata_id = metadata_record.id if metadata_record else None
            
            return {
                "success": True,
                "message": "文件转换成功，元数据已提取并保存",
                "output_path": output_path,
                "backup_path": convert_result.get('backup_path'),
                "metadata_id": metadata_id,
                "issues_fixed": convert_result.get('issues_fixed', []),
                "remaining_issues": convert_result.get('remaining_issues', [])
            }
            
        finally:
            session.close()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转换文件并提取元数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"转换文件并提取元数据失败: {str(e)}")


@router.post("/extract-metadata")
async def extract_metadata_only(
    file_path: str = Query(..., description="uploads目录中的文件路径"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    直接从符合规范的文件中提取元数据保存到数据库
    """
    try:
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        logger.info(f"开始提取元数据: {file_path}")
        
        # 将文件保存到Thredds数据目录
        thredds_data_dir = os.path.join(os.getcwd(), "docker", "thredds", "data", "oceanenv", "standard")
        os.makedirs(thredds_data_dir, exist_ok=True)
        
        filename = os.path.basename(file_path)
        standard_path = os.path.join(thredds_data_dir, filename)
        
        # 复制文件到standard目录
        import shutil
        shutil.copy2(file_path, standard_path)
        
        # 导入元数据提取器
        from app.services.metadata_extractor import MetadataExtractor
        
        # 提取元数据
        extractor = MetadataExtractor()
        metadata = extractor.extract_metadata(standard_path, processing_status="standard")
        
        # 保存到数据库
        from app.db.session import SessionLocal
        from app.db.models import NetCDFMetadata
        
        # 创建数据库会话
        session = SessionLocal()
        
        try:
            # 创建元数据记录
            metadata_record = NetCDFMetadata(**metadata)
            session.add(metadata_record)
            session.commit()
            logger.info(f"元数据已保存到数据库: {standard_path}")
            
            # 在后台任务中删除uploads文件
            background_tasks.add_task(delete_upload_file, file_path)
            
            return {
                "success": True,
                "message": "元数据提取成功并已保存",
                "file_path": standard_path,
                "metadata_id": metadata_record.id
            }
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提取元数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提取元数据失败: {str(e)}")


@router.delete("/delete-upload")
async def delete_upload_file_endpoint(
    file_path: str = Query(..., description="要删除的文件路径")
):
    """
    删除uploads目录中的文件
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"文件已删除: {file_path}")
            return {"success": True, "message": "文件已删除"}
        else:
            return {"success": True, "message": "文件不存在或已删除"}
            
    except Exception as e:
        logger.error(f"删除文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")


def delete_upload_file(file_path: str):
    """
    后台任务：删除uploads文件
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"后台任务已删除文件: {file_path}")
    except Exception as e:
        logger.error(f"后台删除文件失败: {file_path}, 错误: {str(e)}")
