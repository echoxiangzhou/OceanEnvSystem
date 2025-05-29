"""
元数据管理API端点
提供NetCDF文件元数据的查询、列表、统计等功能
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_
import logging

from app.db.session import get_db
from app.db.models import NetCDFMetadata
from app.services.metadata_extractor import extract_and_save_metadata
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metadata", tags=["Metadata Management"])


class MetadataResponse(BaseModel):
    """元数据响应模型"""
    id: int
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    cf_version: Optional[str] = None
    is_cf_compliant: bool = False
    title: Optional[str] = None
    summary: Optional[str] = None
    institution: Optional[str] = None
    source: Optional[str] = None
    time_coverage_start: Optional[str] = None
    time_coverage_end: Optional[str] = None
    geospatial_lat_min: Optional[float] = None
    geospatial_lat_max: Optional[float] = None
    geospatial_lon_min: Optional[float] = None
    geospatial_lon_max: Optional[float] = None
    geospatial_vertical_min: Optional[float] = None
    geospatial_vertical_max: Optional[float] = None
    variables: Optional[dict] = None
    dimensions: Optional[dict] = None
    processing_status: str = "standard"
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class MetadataListResponse(BaseModel):
    """元数据列表响应模型"""
    total: int
    items: List[MetadataResponse]
    page: int
    size: int


class MetadataStatsResponse(BaseModel):
    """元数据统计响应模型"""
    total_files: int
    cf_compliant_files: int
    processing_status_counts: Dict[str, int]
    file_size_stats: Dict[str, float]
    institution_counts: Dict[str, int]


@router.get("/list", response_model=MetadataListResponse)
async def get_metadata_list(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    processing_status: Optional[str] = Query(None, description="处理状态过滤"),
    is_cf_compliant: Optional[bool] = Query(None, description="CF规范符合性过滤"),
    institution: Optional[str] = Query(None, description="机构过滤"),
    search: Optional[str] = Query(None, description="搜索关键词（文件名或标题）"),
    sort_by: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序顺序 (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    获取元数据列表，支持分页、过滤和搜索
    """
    try:
        # 构建查询
        query = db.query(NetCDFMetadata)
        
        # 应用过滤条件
        if processing_status:
            query = query.filter(NetCDFMetadata.processing_status == processing_status)
        
        if is_cf_compliant is not None:
            query = query.filter(NetCDFMetadata.is_cf_compliant == is_cf_compliant)
        
        if institution:
            query = query.filter(NetCDFMetadata.institution.ilike(f"%{institution}%"))
        
        if search:
            query = query.filter(
                or_(
                    NetCDFMetadata.file_name.ilike(f"%{search}%"),
                    NetCDFMetadata.title.ilike(f"%{search}%")
                )
            )
        
        # 计算总数
        total = query.count()
        
        # 应用排序
        if hasattr(NetCDFMetadata, sort_by):
            sort_column = getattr(NetCDFMetadata, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        # 应用分页
        offset = (page - 1) * size
        items = query.offset(offset).limit(size).all()
        
        # 转换为响应格式
        response_items = []
        for item in items:
            response_item = MetadataResponse(
                id=item.id,
                file_name=item.file_name,
                file_path=item.file_path,
                file_size=item.file_size,
                cf_version=item.cf_version,
                is_cf_compliant=item.is_cf_compliant,
                title=item.title,
                summary=item.summary,
                institution=item.institution,
                source=item.source,
                time_coverage_start=item.time_coverage_start.isoformat() if item.time_coverage_start else None,
                time_coverage_end=item.time_coverage_end.isoformat() if item.time_coverage_end else None,
                geospatial_lat_min=item.geospatial_lat_min,
                geospatial_lat_max=item.geospatial_lat_max,
                geospatial_lon_min=item.geospatial_lon_min,
                geospatial_lon_max=item.geospatial_lon_max,
                geospatial_vertical_min=item.geospatial_vertical_min,
                geospatial_vertical_max=item.geospatial_vertical_max,
                variables=item.variables,
                dimensions=item.dimensions,
                processing_status=item.processing_status,
                created_at=item.created_at.isoformat(),
                updated_at=item.updated_at.isoformat()
            )
            response_items.append(response_item)
        
        return MetadataListResponse(
            total=total,
            items=response_items,
            page=page,
            size=size
        )
        
    except Exception as e:
        logger.error(f"获取元数据列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取元数据列表失败: {str(e)}")


@router.get("/detail/{metadata_id}", response_model=MetadataResponse)
async def get_metadata_detail(
    metadata_id: int,
    db: Session = Depends(get_db)
):
    """
    获取单个元数据的详细信息
    """
    try:
        metadata = db.query(NetCDFMetadata).filter(NetCDFMetadata.id == metadata_id).first()
        
        if not metadata:
            raise HTTPException(status_code=404, detail="元数据记录不存在")
        
        return MetadataResponse(
            id=metadata.id,
            file_name=metadata.file_name,
            file_path=metadata.file_path,
            file_size=metadata.file_size,
            cf_version=metadata.cf_version,
            is_cf_compliant=metadata.is_cf_compliant,
            title=metadata.title,
            summary=metadata.summary,
            institution=metadata.institution,
            source=metadata.source,
            time_coverage_start=metadata.time_coverage_start.isoformat() if metadata.time_coverage_start else None,
            time_coverage_end=metadata.time_coverage_end.isoformat() if metadata.time_coverage_end else None,
            geospatial_lat_min=metadata.geospatial_lat_min,
            geospatial_lat_max=metadata.geospatial_lat_max,
            geospatial_lon_min=metadata.geospatial_lon_min,
            geospatial_lon_max=metadata.geospatial_lon_max,
            geospatial_vertical_min=metadata.geospatial_vertical_min,
            geospatial_vertical_max=metadata.geospatial_vertical_max,
            variables=metadata.variables,
            dimensions=metadata.dimensions,
            processing_status=metadata.processing_status,
            created_at=metadata.created_at.isoformat(),
            updated_at=metadata.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取元数据详情失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取元数据详情失败: {str(e)}")


@router.get("/stats", response_model=MetadataStatsResponse)
async def get_metadata_stats(db: Session = Depends(get_db)):
    """
    获取元数据统计信息
    """
    try:
        # 总文件数
        total_files = db.query(NetCDFMetadata).count()
        
        # CF规范符合的文件数
        cf_compliant_files = db.query(NetCDFMetadata).filter(
            NetCDFMetadata.is_cf_compliant == True
        ).count()
        
        # 按处理状态统计
        processing_status_counts = {}
        status_results = db.query(
            NetCDFMetadata.processing_status,
            func.count(NetCDFMetadata.id)
        ).group_by(NetCDFMetadata.processing_status).all()
        
        for status, count in status_results:
            processing_status_counts[status or "unknown"] = count
        
        # 文件大小统计
        size_stats = db.query(
            func.avg(NetCDFMetadata.file_size),
            func.sum(NetCDFMetadata.file_size),
            func.min(NetCDFMetadata.file_size),
            func.max(NetCDFMetadata.file_size)
        ).filter(NetCDFMetadata.file_size.isnot(None)).first()
        
        file_size_stats = {
            "average": float(size_stats[0]) if size_stats[0] else 0,
            "total": float(size_stats[1]) if size_stats[1] else 0,
            "minimum": float(size_stats[2]) if size_stats[2] else 0,
            "maximum": float(size_stats[3]) if size_stats[3] else 0
        }
        
        # 按机构统计
        institution_counts = {}
        institution_results = db.query(
            NetCDFMetadata.institution,
            func.count(NetCDFMetadata.id)
        ).filter(NetCDFMetadata.institution.isnot(None)).group_by(
            NetCDFMetadata.institution
        ).limit(10).all()  # 只返回前10个机构
        
        for institution, count in institution_results:
            institution_counts[institution] = count
        
        return MetadataStatsResponse(
            total_files=total_files,
            cf_compliant_files=cf_compliant_files,
            processing_status_counts=processing_status_counts,
            file_size_stats=file_size_stats,
            institution_counts=institution_counts
        )
        
    except Exception as e:
        logger.error(f"获取元数据统计失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取元数据统计失败: {str(e)}")


@router.post("/extract/{file_path:path}")
async def extract_metadata_from_file(
    file_path: str,
    processing_status: str = Query("standard", description="处理状态"),
    db: Session = Depends(get_db)
):
    """
    手动从指定文件提取元数据
    """
    try:
        # 检查文件是否存在
        import os
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {file_path}")
        
        # 提取并保存元数据
        metadata = extract_and_save_metadata(file_path, processing_status)
        
        return {
            "success": True,
            "message": "元数据提取成功",
            "metadata_id": metadata.id,
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"提取元数据失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"提取元数据失败: {str(e)}")


@router.delete("/delete/{metadata_id}")
async def delete_metadata(
    metadata_id: int,
    db: Session = Depends(get_db)
):
    """
    删除指定的元数据记录
    """
    try:
        metadata = db.query(NetCDFMetadata).filter(NetCDFMetadata.id == metadata_id).first()
        
        if not metadata:
            raise HTTPException(status_code=404, detail="元数据记录不存在")
        
        file_path = metadata.file_path
        db.delete(metadata)
        db.commit()
        
        return {
            "success": True,
            "message": "元数据记录已删除",
            "file_path": file_path
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除元数据失败: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除元数据失败: {str(e)}")


@router.get("/variables")
async def get_unique_variables(db: Session = Depends(get_db)):
    """
    获取所有唯一的变量名列表
    """
    try:
        # 获取所有非空的变量信息
        metadatas = db.query(NetCDFMetadata.variables).filter(
            NetCDFMetadata.variables.isnot(None)
        ).all()
        
        unique_variables = set()
        for metadata in metadatas:
            if metadata.variables and isinstance(metadata.variables, dict):
                unique_variables.update(metadata.variables.keys())
        
        return {
            "variables": sorted(list(unique_variables))
        }
        
    except Exception as e:
        logger.error(f"获取变量列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取变量列表失败: {str(e)}")


@router.get("/institutions")
async def get_unique_institutions(db: Session = Depends(get_db)):
    """
    获取所有唯一的机构名列表
    """
    try:
        institutions = db.query(NetCDFMetadata.institution).filter(
            NetCDFMetadata.institution.isnot(None)
        ).distinct().all()
        
        institution_list = [inst[0] for inst in institutions if inst[0]]
        
        return {
            "institutions": sorted(institution_list)
        }
        
    except Exception as e:
        logger.error(f"获取机构列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取机构列表失败: {str(e)}")


@router.post("/batch-extract", 
            summary="批量扫描并提取文件元数据",
            description="扫描指定目录下的所有NetCDF文件并提取元数据到数据库")
async def batch_extract_metadata(
    scan_dir: str = Query(default="/app/data/oceanenv", description="扫描目录路径"),
    force_update: bool = Query(default=False, description="是否强制更新已存在的元数据"),
    check_duplicates: bool = Query(default=True, description="是否执行严格的重复检查"),
    clean_duplicates: bool = Query(default=True, description="是否自动清理重复的raw状态记录"),
    db: Session = Depends(get_db)
):
    """批量扫描并提取文件元数据"""
    try:
        import os
        from pathlib import Path
        from app.services.metadata_extractor import metadata_extractor
        
        results = {
            "total_files": 0,
            "processed_files": 0,
            "skipped_files": 0,
            "duplicate_files": 0,
            "cleaned_duplicates": 0,
            "error_files": 0,
            "details": []
        }
        
        # 扫描目录
        scan_path = Path(scan_dir)
        if not scan_path.exists():
            raise HTTPException(status_code=404, detail=f"扫描目录不存在: {scan_dir}")
        
        # 查找所有NetCDF文件
        netcdf_files = []
        for pattern in ['**/*.nc', '**/*.netcdf', '**/*.nc4']:
            netcdf_files.extend(scan_path.glob(pattern))
        
        results["total_files"] = len(netcdf_files)
        
        for file_path in netcdf_files:
            try:
                # 确定处理状态
                file_str = str(file_path)
                if 'raw' in file_str:
                    # 根据需求1：删除原始数据文件元数据提取功能，跳过raw文件
                    results["skipped_files"] += 1
                    results["details"].append({
                        "file_path": file_str,
                        "status": "skipped",
                        "message": "根据系统配置，跳过raw状态文件的元数据提取"
                    })
                    continue
                elif 'processing' in file_str:
                    processing_status = 'processing' 
                elif 'standard' in file_str:
                    processing_status = 'standard'
                else:
                    # 默认情况下，如果不在明确的raw目录下，视为standard处理
                    processing_status = 'standard'
                
                # 严格的重复检查
                if check_duplicates and not force_update:
                    # 检查文件路径重复
                    existing_by_path = db.query(NetCDFMetadata).filter(
                        NetCDFMetadata.file_path == file_str
                    ).first()
                    
                    # 检查文件名+大小重复
                    existing_by_name_size = None
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_name = file_path.name
                        existing_by_name_size = db.query(NetCDFMetadata).filter(
                            NetCDFMetadata.file_name == file_name,
                            NetCDFMetadata.file_size == file_size
                        ).first()
                    
                    if existing_by_path or existing_by_name_size:
                        results["duplicate_files"] += 1
                        duplicate_info = {
                            "file_path": file_str,
                            "status": "duplicate",
                            "message": "检测到重复文件，跳过提取"
                        }
                        
                        if existing_by_path:
                            duplicate_info["existing_record_id"] = existing_by_path.id
                            duplicate_info["duplicate_type"] = "same_path"
                        elif existing_by_name_size:
                            duplicate_info["existing_record_id"] = existing_by_name_size.id
                            duplicate_info["duplicate_type"] = "same_name_size"
                        
                        results["details"].append(duplicate_info)
                        continue
                
                # 提取元数据
                metadata_record = metadata_extractor.extract_and_save(
                    file_str, 
                    processing_status, 
                    db,
                    force_update=force_update
                )
                
                results["processed_files"] += 1
                
                # *** 新增：如果是standard状态的文件，清理可能存在的raw状态重复记录 ***
                if clean_duplicates and processing_status == 'standard':
                    file_name = file_path.name
                    raw_duplicate = db.query(NetCDFMetadata).filter(
                        NetCDFMetadata.file_name == file_name,
                        NetCDFMetadata.processing_status == "raw",
                        NetCDFMetadata.id != metadata_record.id
                    ).first()
                    
                    if raw_duplicate:
                        db.delete(raw_duplicate)
                        db.commit()
                        results["cleaned_duplicates"] += 1
                        logger.info(f"清理raw状态的重复元数据记录: {raw_duplicate.id}")
                
                results["details"].append({
                    "file_path": file_str,
                    "status": "processed",
                    "processing_status": processing_status,
                    "metadata_id": metadata_record.id
                })
                
            except Exception as e:
                results["error_files"] += 1
                results["details"].append({
                    "file_path": str(file_path),
                    "status": "error",
                    "message": str(e)
                })
                logger.error(f"处理文件失败 {file_path}: {str(e)}")
        
        return results
        
    except Exception as e:
        logger.error(f"批量提取元数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"批量提取元数据失败: {str(e)}")


@router.post("/scan-standard-files",
            summary="扫描standard目录并补充元数据",
            description="专门扫描standard目录下已符合CF规范的文件并补充元数据")
async def scan_standard_files(
    data_dir: str = Query(default="/app/data/oceanenv", description="数据根目录"),
    db: Session = Depends(get_db)
):
    """扫描standard目录并补充元数据"""
    try:
        import os
        from pathlib import Path
        from app.services.metadata_extractor import metadata_extractor
        
        standard_dir = Path(data_dir) / "standard"
        if not standard_dir.exists():
            raise HTTPException(status_code=404, detail=f"Standard目录不存在: {standard_dir}")
        
        results = {
            "scanned_files": 0,
            "new_metadata": 0,
            "updated_metadata": 0,
            "error_files": 0,
            "details": []
        }
        
        # 查找所有标准目录下的NetCDF文件
        netcdf_files = []
        for pattern in ['**/*.nc', '**/*.netcdf', '**/*.nc4']:
            netcdf_files.extend(standard_dir.glob(pattern))
        
        results["scanned_files"] = len(netcdf_files)
        
        for file_path in netcdf_files:
            try:
                # 检查是否已存在
                existing = db.query(NetCDFMetadata).filter(
                    NetCDFMetadata.file_path == str(file_path)
                ).first()
                
                if existing:
                    # 更新现有记录
                    metadata_record = metadata_extractor.extract_and_save(
                        str(file_path), 
                        "standard", 
                        db
                    )
                    results["updated_metadata"] += 1
                    results["details"].append({
                        "file_path": str(file_path),
                        "status": "updated",
                        "metadata_id": metadata_record.id
                    })
                else:
                    # 创建新记录
                    metadata_record = metadata_extractor.extract_and_save(
                        str(file_path), 
                        "standard", 
                        db
                    )
                    results["new_metadata"] += 1
                    results["details"].append({
                        "file_path": str(file_path),
                        "status": "created",
                        "metadata_id": metadata_record.id
                    })
                
            except Exception as e:
                results["error_files"] += 1
                results["details"].append({
                    "file_path": str(file_path),
                    "status": "error",
                    "message": str(e)
                })
                logger.error(f"处理standard文件失败 {file_path}: {str(e)}")
        
        return results
        
    except Exception as e:
        logger.error(f"扫描standard文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"扫描standard文件失败: {str(e)}")


@router.post("/process-raw-files",
            summary="处理raw目录文件并提取元数据",
            description="检查raw目录中的文件是否符合CF1.8标准，进行转换（如需要）并提取元数据")
async def process_raw_files(
    data_dir: str = Query(default="/app/data/oceanenv", description="数据根目录"),
    force_reprocess: bool = Query(default=False, description="是否强制重新处理已有元数据的文件"),
    check_duplicates: bool = Query(default=True, description="是否执行严格的重复检查"),
    db: Session = Depends(get_db)
):
    """处理raw目录中的文件，进行CF标准检查、转换和元数据提取"""
    try:
        import os
        from pathlib import Path
        from app.services.metadata_extractor import metadata_extractor
        from app.services.cf_validator import validate_netcdf_file
        from app.services.cf_converter import convert_netcdf_to_cf
        
        # 设置目录路径
        raw_dir = Path(data_dir) / "raw"
        processing_dir = Path(data_dir) / "processing"
        standard_dir = Path(data_dir) / "standard"
        
        # 确保目录存在
        for directory in [raw_dir, processing_dir, standard_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        if not raw_dir.exists():
            raise HTTPException(status_code=404, detail=f"Raw目录不存在: {raw_dir}")
        
        results = {
            "total_files": 0,
            "cf_compliant_files": 0,
            "converted_files": 0,
            "failed_conversions": 0,
            "metadata_extracted": 0,
            "skipped_files": 0,
            "duplicate_files": 0,
            "cleaned_duplicates": 0,
            "error_files": 0,
            "details": []
        }
        
        # 查找所有raw目录下的NetCDF文件
        netcdf_files = []
        for pattern in ['**/*.nc', '**/*.netcdf', '**/*.nc4']:
            netcdf_files.extend(raw_dir.glob(pattern))
        
        results["total_files"] = len(netcdf_files)
        logger.info(f"在raw目录发现 {len(netcdf_files)} 个NetCDF文件")
        
        for file_path in netcdf_files:
            try:
                file_str = str(file_path)
                file_name = file_path.name
                
                # 严格的重复检查
                if check_duplicates and not force_reprocess:
                    # 检查是否已经处理过（多种方式检查）
                    existing_by_path = db.query(NetCDFMetadata).filter(
                        NetCDFMetadata.file_path == file_str
                    ).first()
                    
                    existing_by_name_size = None
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        existing_by_name_size = db.query(NetCDFMetadata).filter(
                            NetCDFMetadata.file_name == file_name,
                            NetCDFMetadata.file_size == file_size
                        ).first()
                    
                    # 检查是否存在相同标准目录中的文件
                    standard_file_path = standard_dir / file_name
                    existing_standard = None
                    if standard_file_path.exists():
                        existing_standard = db.query(NetCDFMetadata).filter(
                            NetCDFMetadata.file_path == str(standard_file_path)
                        ).first()
                    
                    if existing_by_path or existing_by_name_size or existing_standard:
                        results["duplicate_files"] += 1
                        duplicate_info = {
                            "file_path": file_str,
                            "file_name": file_name,
                            "status": "duplicate",
                            "message": "检测到重复文件，跳过处理"
                        }
                        
                        if existing_by_path:
                            duplicate_info["existing_record_id"] = existing_by_path.id
                            duplicate_info["duplicate_type"] = "same_path"
                        elif existing_by_name_size:
                            duplicate_info["existing_record_id"] = existing_by_name_size.id
                            duplicate_info["duplicate_type"] = "same_name_size"
                        elif existing_standard:
                            duplicate_info["existing_record_id"] = existing_standard.id
                            duplicate_info["duplicate_type"] = "exists_in_standard"
                        
                        results["details"].append(duplicate_info)
                        
                        # 如果raw文件与standard文件重复，删除raw文件
                        if existing_standard:
                            file_path.unlink()
                            logger.info(f"删除与standard目录重复的raw文件: {file_path}")
                            duplicate_info["action"] = "deleted_raw_duplicate"
                        
                        continue
                
                logger.info(f"开始处理文件: {file_path}")
                
                # 步骤1: 验证CF1.8标准符合性
                validation_result = validate_netcdf_file(file_str)
                
                if validation_result.is_valid:
                    # 文件已符合CF1.8标准
                    results["cf_compliant_files"] += 1
                    
                    # 直接移动到standard目录
                    standard_path = standard_dir / file_name
                    
                    # 如果standard目录中已存在同名文件，进行更详细的检查
                    if standard_path.exists():
                        if not force_reprocess:
                            logger.warning(f"Standard目录中已存在同名文件，跳过: {standard_path}")
                            results["skipped_files"] += 1
                            results["details"].append({
                                "file_path": file_str,
                                "file_name": file_name,
                                "status": "skipped",
                                "message": "Standard目录中已存在同名文件"
                            })
                            continue
                        else:
                            standard_path.unlink()
                            logger.info(f"强制模式：删除已存在的standard文件: {standard_path}")
                    
                    import shutil
                    shutil.copy2(file_path, standard_path)
                    
                    # 提取标准文件的元数据
                    try:
                        standard_metadata = metadata_extractor.extract_and_save(
                            str(standard_path), "standard", db, force_update=force_reprocess
                        )
                        results["metadata_extracted"] += 1
                        
                        # *** 新增：清理可能存在的raw状态重复记录 ***
                        raw_duplicate = db.query(NetCDFMetadata).filter(
                            NetCDFMetadata.file_name == file_name,
                            NetCDFMetadata.processing_status == "raw",
                            NetCDFMetadata.id != standard_metadata.id
                        ).first()
                        
                        if raw_duplicate:
                            db.delete(raw_duplicate)
                            db.commit()
                            results["cleaned_duplicates"] += 1
                            logger.info(f"清理raw状态的重复元数据记录: {raw_duplicate.id}")
                        
                        results["details"].append({
                            "file_path": file_str,
                            "file_name": file_name,
                            "status": "cf_compliant",
                            "message": "文件已符合CF1.8标准，已移动到standard目录",
                            "standard_path": str(standard_path),
                            "metadata_id": standard_metadata.id,
                            "validation_issues": len(validation_result.issues)
                        })
                        
                        # 删除raw目录中的原文件
                        file_path.unlink()
                        logger.info(f"CF标准文件处理完成，已删除原文件: {file_path}")
                        
                    except Exception as e:
                        logger.error(f"提取标准文件元数据失败: {str(e)}")
                        results["error_files"] += 1
                        results["details"].append({
                            "file_path": file_str,
                            "file_name": file_name,
                            "status": "error",
                            "message": f"提取标准文件元数据失败: {str(e)}"
                        })
                
                else:
                    # 文件不符合CF1.8标准，需要转换
                    logger.info(f"文件不符合CF1.8标准，开始转换: {file_path}")
                    
                    # 先复制到processing目录
                    processing_path = processing_dir / file_name
                    processing_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    import shutil
                    shutil.copy2(file_path, processing_path)
                    
                    # 设置转换后的文件路径
                    standard_path = standard_dir / file_name
                    standard_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 如果standard目录中已存在同名文件，进行检查
                    if standard_path.exists():
                        if not force_reprocess:
                            logger.warning(f"Standard目录中已存在同名文件，跳过转换: {standard_path}")
                            results["skipped_files"] += 1
                            results["details"].append({
                                "file_path": file_str,
                                "file_name": file_name,
                                "status": "skipped",
                                "message": "Standard目录中已存在同名文件，跳过转换"
                            })
                            continue
                        else:
                            standard_path.unlink()
                            logger.info(f"强制模式：删除已存在的standard文件: {standard_path}")
                    
                    # 执行CF转换
                    convert_result = convert_netcdf_to_cf(
                        str(processing_path),
                        str(standard_path),
                        auto_fix=True,
                        backup=True
                    )
                    
                    if convert_result['success']:
                        results["converted_files"] += 1
                        
                        # 转换成功，提取标准文件的元数据
                        try:
                            standard_metadata = metadata_extractor.extract_and_save(
                                str(standard_path), "standard", db, force_update=force_reprocess
                            )
                            results["metadata_extracted"] += 1
                            
                            # *** 新增：清理可能存在的raw状态重复记录 ***
                            raw_duplicate = db.query(NetCDFMetadata).filter(
                                NetCDFMetadata.file_name == file_name,
                                NetCDFMetadata.processing_status == "raw",
                                NetCDFMetadata.id != standard_metadata.id
                            ).first()
                            
                            if raw_duplicate:
                                db.delete(raw_duplicate)
                                db.commit()
                                results["cleaned_duplicates"] += 1
                                logger.info(f"清理raw状态的重复元数据记录: {raw_duplicate.id}")
                            
                            results["details"].append({
                                "file_path": file_str,
                                "file_name": file_name,
                                "status": "converted",
                                "message": "文件转换成功并提取元数据",
                                "standard_path": str(standard_path),
                                "processing_path": str(processing_path),
                                "metadata_id": standard_metadata.id,
                                "issues_fixed": len(convert_result.get('issues_fixed', [])),
                                "remaining_issues": len(convert_result.get('remaining_issues', []))
                            })
                            
                            # 删除raw目录中的原文件
                            file_path.unlink()
                            logger.info(f"转换成功，已删除原文件: {file_path}")
                            
                        except Exception as e:
                            logger.error(f"提取转换后文件元数据失败: {str(e)}")
                            results["error_files"] += 1
                            results["details"].append({
                                "file_path": file_str,
                                "file_name": file_name,
                                "status": "conversion_success_metadata_error", 
                                "message": f"文件转换成功但提取元数据失败: {str(e)}",
                                "standard_path": str(standard_path)
                            })
                    
                    else:
                        # 转换失败
                        results["failed_conversions"] += 1
                        results["details"].append({
                            "file_path": file_str,
                            "file_name": file_name,
                            "status": "conversion_failed",
                            "message": f"文件转换失败: {convert_result['message']}",
                            "processing_path": str(processing_path),
                            "validation_issues": len(validation_result.issues)
                        })
                        logger.error(f"文件转换失败: {file_path} - {convert_result['message']}")
                
            except Exception as e:
                results["error_files"] += 1
                results["details"].append({
                    "file_path": str(file_path),
                    "file_name": file_path.name,
                    "status": "error",
                    "message": str(e)
                })
                logger.error(f"处理文件时出错 {file_path}: {str(e)}")
        
        # 生成处理摘要
        summary = {
            "processing_summary": {
                "total_files_found": results["total_files"],
                "successfully_processed": results["cf_compliant_files"] + results["converted_files"],
                "cf_compliant_files": results["cf_compliant_files"],
                "files_converted": results["converted_files"],
                "conversion_failures": results["failed_conversions"],
                "metadata_records_created": results["metadata_extracted"],
                "duplicate_files_detected": results["duplicate_files"],
                "duplicate_records_cleaned": results["cleaned_duplicates"],
                "skipped_files": results["skipped_files"],
                "error_files": results["error_files"]
            }
        }
        
        results.update(summary)
        
        logger.info(f"Raw目录处理完成: 总文件数={results['total_files']}, "
                   f"成功处理={results['cf_compliant_files'] + results['converted_files']}, "
                   f"CF标准文件={results['cf_compliant_files']}, "
                   f"转换成功={results['converted_files']}, "
                   f"重复文件={results['duplicate_files']}, "
                   f"清理重复记录={results['cleaned_duplicates']}, "
                   f"元数据提取={results['metadata_extracted']}")
        
        return results
        
    except Exception as e:
        logger.error(f"处理raw目录文件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理raw目录文件失败: {str(e)}")


@router.get("/processing-status")
async def get_processing_status(
    data_dir: str = Query(default="/app/data/oceanenv", description="数据根目录"),
    db: Session = Depends(get_db)
):
    """获取数据处理状态概览"""
    try:
        import os
        from pathlib import Path
        
        # 目录路径
        raw_dir = Path(data_dir) / "raw"
        processing_dir = Path(data_dir) / "processing"
        standard_dir = Path(data_dir) / "standard"
        
        status = {
            "directories": {
                "raw": {
                    "path": str(raw_dir),
                    "exists": raw_dir.exists(),
                    "file_count": 0
                },
                "processing": {
                    "path": str(processing_dir),
                    "exists": processing_dir.exists(),
                    "file_count": 0
                },
                "standard": {
                    "path": str(standard_dir),
                    "exists": standard_dir.exists(),
                    "file_count": 0
                }
            },
            "database": {
                "total_metadata_records": 0,
                "by_status": {}
            }
        }
        
        # 统计各目录文件数量
        for dir_name, dir_info in status["directories"].items():
            if dir_info["exists"]:
                dir_path = Path(dir_info["path"])
                netcdf_files = []
                for pattern in ['**/*.nc', '**/*.netcdf', '**/*.nc4']:
                    netcdf_files.extend(dir_path.glob(pattern))
                dir_info["file_count"] = len(netcdf_files)
        
        # 统计数据库中的元数据记录
        total_records = db.query(NetCDFMetadata).count()
        status["database"]["total_metadata_records"] = total_records
        
        # 按处理状态统计
        status_counts = db.query(
            NetCDFMetadata.processing_status,
            func.count(NetCDFMetadata.id)
        ).group_by(NetCDFMetadata.processing_status).all()
        
        for processing_status, count in status_counts:
            status["database"]["by_status"][processing_status or "unknown"] = count
        
        return status
        
    except Exception as e:
        logger.error(f"获取处理状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取处理状态失败: {str(e)}")


@router.post("/clean-duplicates",
            summary="清理重复的元数据记录",
            description="检测并清理数据库中重复的元数据记录，优先保留standard状态的记录")
async def clean_duplicate_metadata(
    dry_run: bool = Query(default=True, description="是否为试运行模式（不实际删除）"),
    db: Session = Depends(get_db)
):
    """清理重复的元数据记录"""
    try:
        results = {
            "total_records": 0,
            "duplicate_groups": 0,
            "records_to_clean": 0,
            "records_cleaned": 0,
            "dry_run": dry_run,
            "details": []
        }
        
        # 统计总记录数
        total_records = db.query(NetCDFMetadata).count()
        results["total_records"] = total_records
        
        # 按文件名分组查找重复记录
        duplicate_groups = db.query(
            NetCDFMetadata.file_name,
            func.count(NetCDFMetadata.id).label('count')
        ).group_by(NetCDFMetadata.file_name).having(
            func.count(NetCDFMetadata.id) > 1
        ).all()
        
        results["duplicate_groups"] = len(duplicate_groups)
        
        for file_name, count in duplicate_groups:
            # 获取该文件名的所有记录
            records = db.query(NetCDFMetadata).filter(
                NetCDFMetadata.file_name == file_name
            ).order_by(
                # 优先级：standard > processing > raw
                NetCDFMetadata.processing_status.desc(),
                NetCDFMetadata.updated_at.desc()
            ).all()
            
            if len(records) <= 1:
                continue
            
            # 保留第一个（优先级最高的）记录，删除其他的
            keep_record = records[0]
            duplicate_records = records[1:]
            
            group_detail = {
                "file_name": file_name,
                "total_duplicates": len(records),
                "keep_record": {
                    "id": keep_record.id,
                    "processing_status": keep_record.processing_status,
                    "file_path": keep_record.file_path
                },
                "records_to_remove": []
            }
            
            for dup_record in duplicate_records:
                results["records_to_clean"] += 1
                
                remove_info = {
                    "id": dup_record.id,
                    "processing_status": dup_record.processing_status,
                    "file_path": dup_record.file_path
                }
                group_detail["records_to_remove"].append(remove_info)
                
                if not dry_run:
                    # 实际删除重复记录
                    db.delete(dup_record)
                    results["records_cleaned"] += 1
                    logger.info(f"删除重复元数据记录: ID={dup_record.id}, 文件={file_name}")
            
            results["details"].append(group_detail)
        
        if not dry_run and results["records_cleaned"] > 0:
            db.commit()
            logger.info(f"清理完成：删除了 {results['records_cleaned']} 条重复记录")
        
        return results
        
    except Exception as e:
        if not dry_run:
            db.rollback()
        logger.error(f"清理重复记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理重复记录失败: {str(e)}") 