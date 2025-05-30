"""
数据导入服务模块
提供数据导入过程中的数据库操作和业务逻辑
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from datetime import datetime, timedelta
import json
import hashlib
import os
import uuid

from app.db.models import (
    DataImportRecord, ValidationIssue, FileOperation, 
    DatasetTemplate, CFStandardName, UserPreference,
    ImportStatusEnum, FileTypeEnum, ValidationLevelEnum
)
from app.schemas.dataset import (
    DataImportRecordCreate, DataImportRecordUpdate,
    FileOperationCreate, ImportProgress, ImportSummary,
    TemplateMatch, SmartSuggestion, ValidationIssue as ValidationIssueSchema
)
from app.db.session import get_db

class DataImportService:
    """数据导入服务类"""
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """计算文件MD5哈希值"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def create_import_record(
        db: Session, 
        record_data: DataImportRecordCreate,
        file_path: Optional[str] = None
    ) -> DataImportRecord:
        """创建数据导入记录"""
        
        # 计算文件哈希值
        file_hash = None
        if file_path and os.path.exists(file_path):
            file_hash = DataImportService.calculate_file_hash(file_path)
        
        db_record = DataImportRecord(
            temp_id=record_data.temp_id,
            original_filename=record_data.original_filename,
            file_type=record_data.file_type,
            file_size=record_data.file_size,
            file_hash=file_hash,
            upload_path=file_path,
            import_status=record_data.import_status,
            progress_percentage=record_data.progress_percentage,
            user_id=record_data.user_id,
            user_name=record_data.user_name,
            user_email=record_data.user_email
        )
        
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        # 创建初始文件操作记录
        DataImportService.create_file_operation(
            db, db_record.id, "upload", "completed", 
            input_path=file_path, success=True,
            operation_log="文件上传成功"
        )
        
        return db_record
    
    @staticmethod
    def get_import_record(db: Session, temp_id: str) -> Optional[DataImportRecord]:
        """根据临时ID获取导入记录"""
        return db.query(DataImportRecord).filter(
            DataImportRecord.temp_id == temp_id
        ).first()
    
    @staticmethod
    def get_import_record_by_id(db: Session, record_id: int) -> Optional[DataImportRecord]:
        """根据ID获取导入记录"""
        return db.query(DataImportRecord).filter(
            DataImportRecord.id == record_id
        ).first()
    
    @staticmethod
    def update_import_record(
        db: Session, 
        temp_id: str, 
        update_data: DataImportRecordUpdate
    ) -> Optional[DataImportRecord]:
        """更新导入记录"""
        db_record = DataImportService.get_import_record(db, temp_id)
        if not db_record:
            return None
        
        # 更新字段
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_record, field, value)
        
        # 更新时间戳
        if update_data.import_status:
            if update_data.import_status == ImportStatusEnum.PARSING:
                db_record.start_processing_time = datetime.utcnow()
            elif update_data.import_status in [ImportStatusEnum.COMPLETED, ImportStatusEnum.FAILED]:
                db_record.completion_time = datetime.utcnow()
        
        db.commit()
        db.refresh(db_record)
        return db_record
    
    @staticmethod
    def list_import_records(
        db: Session, 
        user_id: Optional[str] = None,
        status: Optional[ImportStatusEnum] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[DataImportRecord]:
        """获取导入记录列表"""
        query = db.query(DataImportRecord)
        
        if user_id:
            query = query.filter(DataImportRecord.user_id == user_id)
        if status:
            query = query.filter(DataImportRecord.import_status == status)
        
        return query.order_by(desc(DataImportRecord.created_at)).offset(offset).limit(limit).all()
    
    @staticmethod
    def create_validation_issue(
        db: Session,
        import_record_id: int,
        level: ValidationLevelEnum,
        issue_code: str,
        message: str,
        location: Optional[str] = None,
        suggestion: Optional[str] = None,
        auto_fixable: bool = False
    ) -> ValidationIssue:
        """创建验证问题记录"""
        db_issue = ValidationIssue(
            import_record_id=import_record_id,
            level=level,
            issue_code=issue_code,
            message=message,
            location=location,
            suggestion=suggestion,
            auto_fixable=auto_fixable
        )
        
        db.add(db_issue)
        db.commit()
        db.refresh(db_issue)
        return db_issue
    
    @staticmethod
    def get_validation_issues(
        db: Session, 
        import_record_id: int
    ) -> List[ValidationIssue]:
        """获取导入记录的验证问题"""
        return db.query(ValidationIssue).filter(
            ValidationIssue.import_record_id == import_record_id
        ).order_by(ValidationIssue.created_at).all()
    
    @staticmethod
    def fix_validation_issue(
        db: Session,
        issue_id: int,
        fix_action: str
    ) -> Optional[ValidationIssue]:
        """标记验证问题为已修复"""
        db_issue = db.query(ValidationIssue).filter(ValidationIssue.id == issue_id).first()
        if db_issue:
            db_issue.fixed = True
            db_issue.fix_action = fix_action
            db_issue.fixed_at = datetime.utcnow()
            db.commit()
            db.refresh(db_issue)
        return db_issue
    
    @staticmethod
    def create_file_operation(
        db: Session,
        import_record_id: int,
        operation_type: str,
        operation_status: str,
        input_path: Optional[str] = None,
        output_path: Optional[str] = None,
        success: bool = False,
        error_message: Optional[str] = None,
        operation_log: Optional[str] = None,
        operation_metadata: Optional[Dict[str, Any]] = None
    ) -> FileOperation:
        """创建文件操作记录"""
        db_operation = FileOperation(
            import_record_id=import_record_id,
            operation_type=operation_type,
            operation_status=operation_status,
            input_path=input_path,
            output_path=output_path,
            success=success,
            error_message=error_message,
            operation_log=operation_log,
            operation_metadata=operation_metadata,
            start_time=datetime.utcnow() if operation_status in ["running", "completed"] else None
        )
        
        if operation_status == "completed":
            db_operation.end_time = datetime.utcnow()
            if db_operation.start_time:
                db_operation.duration = (db_operation.end_time - db_operation.start_time).total_seconds()
        
        db.add(db_operation)
        db.commit()
        db.refresh(db_operation)
        return db_operation
    
    @staticmethod
    def update_file_operation(
        db: Session,
        operation_id: int,
        operation_status: str,
        success: Optional[bool] = None,
        error_message: Optional[str] = None,
        operation_log: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[FileOperation]:
        """更新文件操作记录"""
        db_operation = db.query(FileOperation).filter(FileOperation.id == operation_id).first()
        if not db_operation:
            return None
        
        db_operation.operation_status = operation_status
        if success is not None:
            db_operation.success = success
        if error_message:
            db_operation.error_message = error_message
        if operation_log:
            db_operation.operation_log = operation_log
        if output_path:
            db_operation.output_path = output_path
        
        if operation_status == "completed":
            db_operation.end_time = datetime.utcnow()
            if db_operation.start_time:
                db_operation.duration = (db_operation.end_time - db_operation.start_time).total_seconds()
        
        db.commit()
        db.refresh(db_operation)
        return db_operation
    
    @staticmethod
    def get_import_progress(db: Session, temp_id: str) -> Optional[ImportProgress]:
        """获取导入进度"""
        db_record = DataImportService.get_import_record(db, temp_id)
        if not db_record:
            return None
        
        # 计算步骤进度
        step_mapping = {
            ImportStatusEnum.UPLOADED: (1, "文件已上传"),
            ImportStatusEnum.PARSING: (2, "解析数据中"),
            ImportStatusEnum.PARSED: (3, "数据解析完成"),
            ImportStatusEnum.VALIDATING: (4, "验证数据中"),
            ImportStatusEnum.VALIDATED: (5, "数据验证完成"),
            ImportStatusEnum.CONVERTING: (6, "转换为NetCDF中"),
            ImportStatusEnum.COMPLETED: (7, "转换完成"),
            ImportStatusEnum.FAILED: (0, "处理失败"),
            ImportStatusEnum.CANCELLED: (0, "已取消")
        }
        
        steps_completed, current_step = step_mapping.get(db_record.import_status, (0, "未知状态"))
        total_steps = 7
        
        # 估算剩余时间
        estimated_time_remaining = None
        if db_record.start_processing_time and steps_completed > 1 and steps_completed < total_steps:
            elapsed_time = (datetime.utcnow() - db_record.start_processing_time).total_seconds()
            estimated_total_time = elapsed_time * total_steps / (steps_completed - 1)
            estimated_time_remaining = max(0, estimated_total_time - elapsed_time)
        
        return ImportProgress(
            temp_id=temp_id,
            import_status=db_record.import_status,
            progress_percentage=db_record.progress_percentage,
            current_step=current_step,
            steps_completed=steps_completed,
            total_steps=total_steps,
            estimated_time_remaining=estimated_time_remaining,
            error_message=db_record.error_message
        )
    
    @staticmethod
    def get_import_summary(db: Session, user_id: Optional[str] = None) -> ImportSummary:
        """获取导入摘要统计"""
        query = db.query(DataImportRecord)
        if user_id:
            query = query.filter(DataImportRecord.user_id == user_id)
        
        # 基础统计
        total_imports = query.count()
        successful_imports = query.filter(DataImportRecord.import_status == ImportStatusEnum.COMPLETED).count()
        failed_imports = query.filter(DataImportRecord.import_status == ImportStatusEnum.FAILED).count()
        in_progress_imports = query.filter(
            DataImportRecord.import_status.in_([
                ImportStatusEnum.UPLOADED, ImportStatusEnum.PARSING, ImportStatusEnum.PARSED,
                ImportStatusEnum.VALIDATING, ImportStatusEnum.VALIDATED, ImportStatusEnum.CONVERTING
            ])
        ).count()
        
        # 平均处理时间（仅包括已完成的）
        completed_records = query.filter(
            and_(
                DataImportRecord.import_status == ImportStatusEnum.COMPLETED,
                DataImportRecord.start_processing_time.isnot(None),
                DataImportRecord.completion_time.isnot(None)
            )
        ).all()
        
        average_processing_time = 0.0
        if completed_records:
            total_time = sum([
                (record.completion_time - record.start_processing_time).total_seconds() 
                for record in completed_records
            ])
            average_processing_time = total_time / len(completed_records)
        
        # 文件类型统计
        file_type_stats = db.query(
            DataImportRecord.file_type, 
            func.count(DataImportRecord.id).label('count')
        ).group_by(DataImportRecord.file_type).all()
        
        top_file_types = [{"type": stat[0], "count": stat[1]} for stat in file_type_stats]
        
        # 最近的导入记录
        recent_imports = query.order_by(desc(DataImportRecord.created_at)).limit(10).all()
        
        return ImportSummary(
            total_imports=total_imports,
            successful_imports=successful_imports,
            failed_imports=failed_imports,
            in_progress_imports=in_progress_imports,
            average_processing_time=average_processing_time,
            top_file_types=top_file_types,
            recent_imports=recent_imports
        )
    
    @staticmethod
    def find_matching_templates(
        db: Session, 
        file_type: FileTypeEnum,
        data_sample: Optional[Dict[str, Any]] = None
    ) -> List[TemplateMatch]:
        """查找匹配的数据集模板"""
        templates = db.query(DatasetTemplate).filter(
            and_(
                DatasetTemplate.is_active == True,
                DatasetTemplate.file_types.contains([file_type])
            )
        ).all()
        
        matches = []
        for template in templates:
            confidence = 0.0
            matched_patterns = []
            
            # 基础文件类型匹配
            if file_type in template.file_types:
                confidence += 0.3
                matched_patterns.append(f"文件类型匹配: {file_type}")
            
            # 数据模式匹配（如果提供了数据样本）
            if data_sample and template.data_patterns:
                pattern_score = DataImportService._match_data_patterns(
                    data_sample, template.data_patterns
                )
                confidence += pattern_score * 0.7
                if pattern_score > 0.5:
                    matched_patterns.append("数据模式匹配")
            
            # 历史使用成功率加权
            if template.usage_count > 0:
                confidence = confidence * (0.8 + 0.2 * template.success_rate)
            
            if confidence > 0.1:  # 只返回有一定匹配度的模板
                matches.append(TemplateMatch(
                    template=template,
                    confidence=min(confidence, 1.0),
                    matched_patterns=matched_patterns,
                    suggested_adjustments={}
                ))
        
        # 按置信度排序
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:5]  # 返回前5个最匹配的模板
    
    @staticmethod
    def _match_data_patterns(data_sample: Dict[str, Any], patterns: Dict[str, Any]) -> float:
        """匹配数据模式"""
        if not patterns or not data_sample:
            return 0.0
        
        score = 0.0
        total_patterns = len(patterns)
        
        for pattern_name, pattern_config in patterns.items():
            if pattern_name == "column_patterns":
                # 匹配列名模式
                if "columns" in data_sample:
                    column_names = [col.lower() for col in data_sample["columns"]]
                    for required_pattern in pattern_config.get("required", []):
                        if any(required_pattern.lower() in col for col in column_names):
                            score += 1.0 / total_patterns
            elif pattern_name == "data_type_patterns":
                # 匹配数据类型模式
                if "data_types" in data_sample:
                    for data_type, count in data_sample["data_types"].items():
                        expected_count = pattern_config.get(data_type, 0)
                        if count >= expected_count:
                            score += 0.5 / total_patterns
        
        return min(score, 1.0)
    
    @staticmethod
    def generate_smart_suggestions(
        db: Session, 
        temp_id: str
    ) -> List[SmartSuggestion]:
        """生成智能建议"""
        suggestions = []
        
        # 获取导入记录
        db_record = DataImportService.get_import_record(db, temp_id)
        if not db_record:
            return suggestions
        
        # 基于文件类型的建议
        if db_record.file_type == FileTypeEnum.CSV:
            suggestions.append(SmartSuggestion(
                type="encoding",
                title="编码建议",
                description="建议使用UTF-8编码以确保最佳兼容性",
                confidence=0.8,
                suggested_value="utf-8",
                action_required=False,
                auto_applicable=True
            ))
        
        # 基于历史数据的建议
        similar_records = db.query(DataImportRecord).filter(
            and_(
                DataImportRecord.file_type == db_record.file_type,
                DataImportRecord.import_status == ImportStatusEnum.COMPLETED,
                DataImportRecord.id != db_record.id
            )
        ).limit(10).all()
        
        if similar_records:
            # 分析成功案例的共同特征
            common_institutions = {}
            for record in similar_records:
                if record.metadata_config and "global_attributes" in record.metadata_config:
                    institution = record.metadata_config["global_attributes"].get("institution")
                    if institution:
                        common_institutions[institution] = common_institutions.get(institution, 0) + 1
            
            if common_institutions:
                most_common = max(common_institutions.items(), key=lambda x: x[1])
                if most_common[1] >= len(similar_records) * 0.3:  # 至少30%的记录使用
                    suggestions.append(SmartSuggestion(
                        type="institution",
                        title="机构建议",
                        description=f"基于历史数据，建议使用机构名称: {most_common[0]}",
                        confidence=0.6,
                        suggested_value=most_common[0],
                        action_required=True,
                        auto_applicable=False
                    ))
        
        # CF标准名称建议
        if db_record.metadata_config and "variables" in db_record.metadata_config:
            for var_name, var_config in db_record.metadata_config["variables"].items():
                if not var_config.get("standard_name"):
                    # 查找相似的CF标准名称
                    cf_names = db.query(CFStandardName).filter(
                        CFStandardName.aliases.contains([var_name.lower()])
                    ).first()
                    
                    if cf_names:
                        suggestions.append(SmartSuggestion(
                            type="cf_standard_name",
                            title=f"变量 {var_name} 的CF标准名称建议",
                            description=f"建议使用CF标准名称: {cf_names.standard_name}",
                            confidence=0.9,
                            suggested_value=cf_names.standard_name,
                            current_value=None,
                            action_required=True,
                            auto_applicable=True
                        ))
        
        return suggestions
    
    @staticmethod
    def cleanup_old_records(db: Session, days: int = 30) -> int:
        """清理旧的导入记录"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 查找需要清理的记录
        old_records = db.query(DataImportRecord).filter(
            and_(
                DataImportRecord.created_at < cutoff_date,
                or_(
                    DataImportRecord.import_status == ImportStatusEnum.FAILED,
                    DataImportRecord.import_status == ImportStatusEnum.CANCELLED
                )
            )
        ).all()
        
        cleaned_count = 0
        for record in old_records:
            # 删除关联的文件（如果存在）
            if record.upload_path and os.path.exists(record.upload_path):
                try:
                    os.remove(record.upload_path)
                except:
                    pass
            
            if record.output_file_path and os.path.exists(record.output_file_path):
                try:
                    os.remove(record.output_file_path)
                except:
                    pass
            
            # 删除数据库记录（关联记录会自动删除）
            db.delete(record)
            cleaned_count += 1
        
        db.commit()
        return cleaned_count
    
    @staticmethod
    def get_user_preference(db: Session, user_id: str) -> Optional[UserPreference]:
        """获取用户偏好设置"""
        return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    
    @staticmethod
    def create_or_update_user_preference(
        db: Session, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> UserPreference:
        """创建或更新用户偏好设置"""
        db_preference = DataImportService.get_user_preference(db, user_id)
        
        if db_preference:
            # 更新现有记录
            for key, value in preferences.items():
                if hasattr(db_preference, key):
                    setattr(db_preference, key, value)
        else:
            # 创建新记录
            db_preference = UserPreference(user_id=user_id, **preferences)
            db.add(db_preference)
        
        db.commit()
        db.refresh(db_preference)
        return db_preference 