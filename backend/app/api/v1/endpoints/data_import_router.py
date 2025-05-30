"""
数据导入管理API路由
提供数据导入相关的高级管理功能
"""

from fastapi import APIRouter, HTTPException, Query, Path, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.db.session import get_db
from app.services.data_import_service import DataImportService
from app.schemas.dataset import (
    DataImportRecord, DataImportRecordCreate, DataImportRecordUpdate,
    ImportProgress, ImportSummary, FileOperation,
    DatasetTemplate, DatasetTemplateCreate,
    CFStandardName, CFStandardNameCreate,
    UserPreference, UserPreferenceCreate, UserPreferenceUpdate,
    TemplateMatch, SmartSuggestion, ImportStatus, FileType,
    ValidationLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/import",
    tags=["data-import-management"]
)

# ===============================================================================
# 导入记录管理
# ===============================================================================

@router.get("/records", response_model=List[DataImportRecord], summary="获取导入记录列表")
def list_import_records(
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    status: Optional[ImportStatus] = Query(None, description="状态过滤"),
    limit: int = Query(50, description="返回数量限制"),
    offset: int = Query(0, description="偏移量"),
    db: Session = Depends(get_db)
):
    """
    获取数据导入记录列表
    支持按用户ID和状态过滤
    """
    try:
        records = DataImportService.list_import_records(
            db, user_id=user_id, status=status, limit=limit, offset=offset
        )
        return records
    except Exception as e:
        logger.error(f"获取导入记录列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取导入记录列表失败: {str(e)}")

@router.get("/records/{temp_id}", response_model=DataImportRecord, summary="获取单个导入记录")
def get_import_record(
    temp_id: str = Path(..., description="临时文件ID"),
    db: Session = Depends(get_db)
):
    """
    根据临时ID获取导入记录详情
    """
    try:
        record = DataImportService.get_import_record(db, temp_id)
        if not record:
            raise HTTPException(status_code=404, detail="导入记录不存在")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取导入记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取导入记录失败: {str(e)}")

@router.put("/records/{temp_id}", response_model=DataImportRecord, summary="更新导入记录")
def update_import_record(
    temp_id: str = Path(..., description="临时文件ID"),
    update_data: DataImportRecordUpdate = None,
    db: Session = Depends(get_db)
):
    """
    更新导入记录信息
    """
    try:
        record = DataImportService.update_import_record(db, temp_id, update_data)
        if not record:
            raise HTTPException(status_code=404, detail="导入记录不存在")
        return record
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新导入记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新导入记录失败: {str(e)}")

@router.get("/progress/{temp_id}", response_model=ImportProgress, summary="获取导入进度")
def get_import_progress(
    temp_id: str = Path(..., description="临时文件ID"),
    db: Session = Depends(get_db)
):
    """
    获取数据导入的实时进度信息
    """
    try:
        progress = DataImportService.get_import_progress(db, temp_id)
        if not progress:
            raise HTTPException(status_code=404, detail="导入记录不存在")
        return progress
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取导入进度失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取导入进度失败: {str(e)}")

@router.get("/summary", response_model=ImportSummary, summary="获取导入摘要统计")
def get_import_summary(
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    db: Session = Depends(get_db)
):
    """
    获取导入活动的统计摘要
    """
    try:
        summary = DataImportService.get_import_summary(db, user_id=user_id)
        return summary
    except Exception as e:
        logger.error(f"获取导入摘要失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取导入摘要失败: {str(e)}")

# ===============================================================================
# 数据集模板管理
# ===============================================================================

@router.get("/templates", response_model=List[DatasetTemplate], summary="获取数据集模板列表")
def list_dataset_templates(
    category: Optional[str] = Query(None, description="模板分类过滤"),
    file_type: Optional[FileType] = Query(None, description="文件类型过滤"),
    is_active: bool = Query(True, description="是否仅返回激活的模板"),
    db: Session = Depends(get_db)
):
    """
    获取数据集模板列表
    """
    try:
        from app.db.models import DatasetTemplate as DatasetTemplateModel
        
        query = db.query(DatasetTemplateModel)
        
        if category:
            query = query.filter(DatasetTemplateModel.category == category)
        if file_type:
            query = query.filter(DatasetTemplateModel.file_types.contains([file_type]))
        if is_active:
            query = query.filter(DatasetTemplateModel.is_active == True)
            
        templates = query.order_by(DatasetTemplateModel.usage_count.desc()).all()
        return templates
    except Exception as e:
        logger.error(f"获取模板列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")

@router.get("/templates/{template_id}", response_model=DatasetTemplate, summary="获取模板详情")
def get_dataset_template(
    template_id: int = Path(..., description="模板ID"),
    db: Session = Depends(get_db)
):
    """
    获取指定模板的详细信息
    """
    try:
        from app.db.models import DatasetTemplate as DatasetTemplateModel
        
        template = db.query(DatasetTemplateModel).filter(DatasetTemplateModel.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取模板详情失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")

@router.post("/templates", response_model=DatasetTemplate, summary="创建数据集模板")
def create_dataset_template(
    template_data: DatasetTemplateCreate = None,
    db: Session = Depends(get_db)
):
    """
    创建新的数据集模板
    """
    try:
        from app.db.models import DatasetTemplate as DatasetTemplateModel
        
        template = DatasetTemplateModel(**template_data.dict())
        db.add(template)
        db.commit()
        db.refresh(template)
        return template
    except Exception as e:
        logger.error(f"创建模板失败: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")

@router.get("/templates/match/{file_type}", response_model=List[TemplateMatch], summary="查找匹配模板")
def find_matching_templates(
    file_type: FileType = Path(..., description="文件类型"),
    data_sample: Optional[Dict[str, Any]] = None,
    db: Session = Depends(get_db)
):
    """
    根据文件类型和数据样本查找匹配的模板
    """
    try:
        from app.db.models import FileTypeEnum
        
        # 转换为数据库枚举类型
        db_file_type = FileTypeEnum(file_type)
        matches = DataImportService.find_matching_templates(db, db_file_type, data_sample)
        return matches
    except Exception as e:
        logger.error(f"查找匹配模板失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查找匹配模板失败: {str(e)}")

# ===============================================================================
# CF标准名称管理
# ===============================================================================

@router.get("/cf-standards", response_model=List[CFStandardName], summary="获取CF标准名称列表")
def list_cf_standard_names(
    category: Optional[str] = Query(None, description="分类过滤"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(100, description="返回数量限制"),
    db: Session = Depends(get_db)
):
    """
    获取CF标准名称列表
    """
    try:
        from app.db.models import CFStandardName as CFStandardNameModel
        
        query = db.query(CFStandardNameModel)
        
        if category:
            query = query.filter(CFStandardNameModel.category == category)
        if search:
            query = query.filter(
                CFStandardNameModel.standard_name.contains(search) |
                CFStandardNameModel.description.contains(search)
            )
            
        cf_names = query.order_by(CFStandardNameModel.usage_count.desc()).limit(limit).all()
        return cf_names
    except Exception as e:
        logger.error(f"获取CF标准名称列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取CF标准名称列表失败: {str(e)}")

@router.get("/cf-standards/search/{variable_name}", response_model=List[CFStandardName], summary="搜索CF标准名称")
def search_cf_standard_names(
    variable_name: str = Path(..., description="变量名称"),
    db: Session = Depends(get_db)
):
    """
    根据变量名称搜索相关的CF标准名称
    """
    try:
        from app.db.models import CFStandardName as CFStandardNameModel
        
        # 搜索标准名称、别名和描述
        cf_names = db.query(CFStandardNameModel).filter(
            CFStandardNameModel.standard_name.contains(variable_name.lower()) |
            CFStandardNameModel.aliases.contains([variable_name.lower()]) |
            CFStandardNameModel.description.contains(variable_name.lower())
        ).order_by(CFStandardNameModel.usage_count.desc()).limit(10).all()
        
        return cf_names
    except Exception as e:
        logger.error(f"搜索CF标准名称失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"搜索CF标准名称失败: {str(e)}")

# ===============================================================================
# 用户偏好管理
# ===============================================================================

@router.get("/preferences/{user_id}", response_model=UserPreference, summary="获取用户偏好")
def get_user_preferences(
    user_id: str = Path(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """
    获取用户的偏好设置
    """
    try:
        preference = DataImportService.get_user_preference(db, user_id)
        if not preference:
            # 返回默认偏好
            preference = DataImportService.get_user_preference(db, "default")
            if not preference:
                raise HTTPException(status_code=404, detail="用户偏好不存在且无默认配置")
        return preference
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户偏好失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取用户偏好失败: {str(e)}")

@router.put("/preferences/{user_id}", response_model=UserPreference, summary="更新用户偏好")
def update_user_preferences(
    user_id: str = Path(..., description="用户ID"),
    preferences: UserPreferenceUpdate = None,
    db: Session = Depends(get_db)
):
    """
    更新用户偏好设置
    """
    try:
        preference = DataImportService.create_or_update_user_preference(
            db, user_id, preferences.dict(exclude_unset=True)
        )
        return preference
    except Exception as e:
        logger.error(f"更新用户偏好失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新用户偏好失败: {str(e)}")

# ===============================================================================
# 智能建议功能
# ===============================================================================

@router.get("/suggestions/{temp_id}", response_model=List[SmartSuggestion], summary="获取智能建议")
def get_smart_suggestions(
    temp_id: str = Path(..., description="临时文件ID"),
    db: Session = Depends(get_db)
):
    """
    为指定的导入记录生成智能建议
    """
    try:
        suggestions = DataImportService.generate_smart_suggestions(db, temp_id)
        return suggestions
    except Exception as e:
        logger.error(f"生成智能建议失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成智能建议失败: {str(e)}")

# ===============================================================================
# 验证问题管理
# ===============================================================================

@router.get("/validation-issues/{temp_id}", summary="获取验证问题")
def get_validation_issues(
    temp_id: str = Path(..., description="临时文件ID"),
    level: Optional[ValidationLevel] = Query(None, description="问题级别过滤"),
    db: Session = Depends(get_db)
):
    """
    获取导入记录的验证问题列表
    """
    try:
        # 先获取导入记录
        record = DataImportService.get_import_record(db, temp_id)
        if not record:
            raise HTTPException(status_code=404, detail="导入记录不存在")
        
        # 获取验证问题
        issues = DataImportService.get_validation_issues(db, record.id)
        
        # 按级别过滤
        if level:
            issues = [issue for issue in issues if issue.level == level]
            
        return issues
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取验证问题失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取验证问题失败: {str(e)}")

@router.put("/validation-issues/{issue_id}/fix", summary="修复验证问题")
def fix_validation_issue(
    issue_id: int = Path(..., description="问题ID"),
    fix_action: str = Query(..., description="修复操作描述"),
    db: Session = Depends(get_db)
):
    """
    标记验证问题为已修复
    """
    try:
        issue = DataImportService.fix_validation_issue(db, issue_id, fix_action)
        if not issue:
            raise HTTPException(status_code=404, detail="验证问题不存在")
        return {"message": "问题修复成功", "issue_id": issue_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修复验证问题失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"修复验证问题失败: {str(e)}")

# ===============================================================================
# 文件操作记录
# ===============================================================================

@router.get("/file-operations/{temp_id}", response_model=List[FileOperation], summary="获取文件操作记录")
def get_file_operations(
    temp_id: str = Path(..., description="临时文件ID"),
    db: Session = Depends(get_db)
):
    """
    获取导入记录的文件操作历史
    """
    try:
        from app.db.models import FileOperation as FileOperationModel
        
        # 先获取导入记录
        record = DataImportService.get_import_record(db, temp_id)
        if not record:
            raise HTTPException(status_code=404, detail="导入记录不存在")
        
        # 获取文件操作记录
        operations = db.query(FileOperationModel).filter(
            FileOperationModel.import_record_id == record.id
        ).order_by(FileOperationModel.created_at).all()
        
        return operations
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件操作记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取文件操作记录失败: {str(e)}")

# ===============================================================================
# 系统维护功能
# ===============================================================================

@router.delete("/cleanup", summary="清理旧记录")
def cleanup_old_records(
    days: int = Query(30, description="清理多少天前的记录"),
    db: Session = Depends(get_db)
):
    """
    清理旧的失败和取消的导入记录
    """
    try:
        cleaned_count = DataImportService.cleanup_old_records(db, days)
        return {
            "message": f"清理完成",
            "cleaned_records": cleaned_count,
            "days_threshold": days
        }
    except Exception as e:
        logger.error(f"清理旧记录失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"清理旧记录失败: {str(e)}")

@router.get("/statistics", summary="获取系统统计信息")
def get_system_statistics(db: Session = Depends(get_db)):
    """
    获取数据导入系统的整体统计信息
    """
    try:
        from app.db.models import DataImportRecord, CFStandardName, DatasetTemplate
        
        # 基础统计
        total_imports = db.query(DataImportRecord).count()
        total_cf_names = db.query(CFStandardName).count()
        total_templates = db.query(DatasetTemplate).count()
        active_templates = db.query(DatasetTemplate).filter(DatasetTemplate.is_active == True).count()
        
        # 文件类型统计
        from sqlalchemy import func
        file_type_stats = db.query(
            DataImportRecord.file_type,
            func.count(DataImportRecord.id).label('count')
        ).group_by(DataImportRecord.file_type).all()
        
        # 状态统计
        status_stats = db.query(
            DataImportRecord.import_status,
            func.count(DataImportRecord.id).label('count')
        ).group_by(DataImportRecord.import_status).all()
        
        return {
            "total_imports": total_imports,
            "total_cf_standard_names": total_cf_names,
            "total_templates": total_templates,
            "active_templates": active_templates,
            "file_type_distribution": [{"type": stat[0], "count": stat[1]} for stat in file_type_stats],
            "status_distribution": [{"status": stat[0], "count": stat[1]} for stat in status_stats]
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}") 