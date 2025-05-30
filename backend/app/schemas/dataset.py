from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any, Union
from enum import Enum
from datetime import datetime

class Variable(BaseModel):
    name: str
    unit: str
    description: Optional[str] = None

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    source_type: str
    data_type: str
    spatial_coverage: Dict[str, Any]
    temporal_coverage: Dict[str, str]
    variables: List[Variable]
    file_format: str
    file_location: str

class DatasetCreate(DatasetBase):
    pass

class Dataset(DatasetBase):
    id: str

class DatasetListItem(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    file_location: str

# 枚举类型定义
class FileType(str, Enum):
    CSV = "csv"
    EXCEL = "excel" 
    CNV = "cnv"
    NETCDF = "netcdf"
    JSON = "json"
    XML = "xml"

class ParseStatus(str, Enum):
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

class ImportStatus(str, Enum):
    UPLOADED = "uploaded"
    PARSING = "parsing"
    PARSED = "parsed"
    VALIDATING = "validating"
    VALIDATED = "validated"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingStatus(str, Enum):
    RAW = "raw"
    PROCESSING = "processing"
    STANDARD = "standard"
    ARCHIVED = "archived"
    ERROR = "error"

class ValidationLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

# 基础响应模式
class FileUploadResponse(BaseModel):
    """文件上传响应"""
    temp_id: str = Field(..., description="临时文件标识")
    filename: str = Field(..., description="原始文件名")
    file_type: FileType = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    upload_time: datetime = Field(..., description="上传时间")
    parse_status: ParseStatus = Field(..., description="解析状态")
    parse_message: Optional[str] = Field(None, description="解析信息")

class ColumnInfo(BaseModel):
    """列信息"""
    name: str = Field(..., description="列名")
    data_type: str = Field(..., description="数据类型")
    sample_values: List[Any] = Field(..., description="示例值")
    missing_count: int = Field(..., description="缺失值数量")
    total_count: int = Field(..., description="总数量")
    suggested_cf_name: Optional[str] = Field(None, description="建议的CF标准名称")
    suggested_units: Optional[str] = Field(None, description="建议的单位")
    confidence: Optional[float] = Field(None, description="建议置信度")

class DataPreview(BaseModel):
    """数据预览"""
    temp_id: str = Field(..., description="临时文件标识")
    row_count: int = Field(..., description="总行数")
    column_count: int = Field(..., description="总列数")
    columns: List[ColumnInfo] = Field(..., description="列信息")
    preview_data: List[Dict[str, Any]] = Field(..., description="预览数据（前50行）")
    parsing_config: Dict[str, Any] = Field(..., description="解析配置")
    quality_report: Dict[str, Any] = Field(..., description="数据质量报告")

class VariableAttribute(BaseModel):
    """变量属性"""
    standard_name: Optional[str] = Field(None, description="CF标准名称")
    long_name: Optional[str] = Field(None, description="长名称")
    units: Optional[str] = Field(None, description="单位")
    valid_min: Optional[float] = Field(None, description="最小有效值")
    valid_max: Optional[float] = Field(None, description="最大有效值")
    fill_value: Optional[Any] = Field(None, description="填充值")
    coordinates: Optional[str] = Field(None, description="坐标变量")
    description: Optional[str] = Field(None, description="描述")

class GlobalAttribute(BaseModel):
    """全局属性"""
    title: Optional[str] = Field(None, description="数据集标题")
    institution: Optional[str] = Field(None, description="机构")
    source: Optional[str] = Field(None, description="数据源")
    history: Optional[str] = Field(None, description="处理历史")
    references: Optional[str] = Field(None, description="参考文献")
    comment: Optional[str] = Field(None, description="注释")
    summary: Optional[str] = Field(None, description="摘要")
    keywords: Optional[str] = Field(None, description="关键词")
    time_coverage_start: Optional[str] = Field(None, description="时间覆盖开始")
    time_coverage_end: Optional[str] = Field(None, description="时间覆盖结束")
    geospatial_lat_min: Optional[float] = Field(None, description="最小纬度")
    geospatial_lat_max: Optional[float] = Field(None, description="最大纬度") 
    geospatial_lon_min: Optional[float] = Field(None, description="最小经度")
    geospatial_lon_max: Optional[float] = Field(None, description="最大经度")
    creator_name: Optional[str] = Field(None, description="创建者姓名")
    creator_email: Optional[str] = Field(None, description="创建者邮箱")
    creator_institution: Optional[str] = Field(None, description="创建者机构")

class MetadataConfig(BaseModel):
    """元数据配置"""
    temp_id: str = Field(..., description="临时文件标识")
    variables: Dict[str, VariableAttribute] = Field(..., description="变量属性配置")
    global_attributes: GlobalAttribute = Field(..., description="全局属性配置") 
    coordinate_variables: Dict[str, str] = Field(..., description="坐标变量映射")
    
class ValidationIssue(BaseModel):
    """验证问题"""
    level: ValidationLevel = Field(..., description="问题级别")
    code: str = Field(..., description="问题代码")
    message: str = Field(..., description="问题描述")
    location: Optional[str] = Field(None, description="问题位置")
    suggestion: Optional[str] = Field(None, description="修改建议")
    auto_fixable: Optional[bool] = Field(False, description="是否可自动修复")
    fixed: Optional[bool] = Field(False, description="是否已修复")

class ValidationResult(BaseModel):
    """验证结果"""
    temp_id: str = Field(..., description="临时文件标识")
    is_valid: bool = Field(..., description="是否通过验证")
    cf_version: str = Field(..., description="CF Convention版本")
    total_issues: int = Field(..., description="问题总数")
    error_count: int = Field(..., description="错误数量")
    warning_count: int = Field(..., description="警告数量")
    info_count: int = Field(..., description="信息数量")
    issues: List[ValidationIssue] = Field(..., description="问题列表")
    compliance_score: float = Field(..., description="合规性评分")

class ConversionResult(BaseModel):
    """转换结果"""
    temp_id: str = Field(..., description="临时文件标识")
    success: bool = Field(..., description="是否转换成功")
    output_path: Optional[str] = Field(None, description="输出文件路径")
    tds_url: Optional[str] = Field(None, description="TDS访问URL")
    opendap_url: Optional[str] = Field(None, description="OPeNDAP访问URL")
    file_size: Optional[int] = Field(None, description="生成文件大小")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    issues_fixed: List[ValidationIssue] = Field(default_factory=list, description="已修复的问题")
    remaining_issues: List[ValidationIssue] = Field(default_factory=list, description="剩余问题")
    message: Optional[str] = Field(None, description="处理信息")
    metadata_extracted: Optional[bool] = Field(None, description="是否成功提取元数据")
    metadata_record_id: Optional[int] = Field(None, description="元数据记录ID")
    metadata_error: Optional[str] = Field(None, description="元数据提取错误信息")

# 扩展的数据库模型对应的Pydantic模式

class DataImportRecordBase(BaseModel):
    """数据导入记录基础模式"""
    temp_id: str = Field(..., description="临时文件UUID")
    original_filename: str = Field(..., description="原始文件名")
    file_type: FileType = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    file_hash: Optional[str] = Field(None, description="文件MD5哈希值")
    import_status: ImportStatus = Field(ImportStatus.UPLOADED, description="导入状态")
    progress_percentage: float = Field(0.0, description="处理进度百分比")
    user_id: Optional[str] = Field(None, description="用户ID")
    user_name: Optional[str] = Field(None, description="用户名")
    user_email: Optional[str] = Field(None, description="用户邮箱")

class DataImportRecordCreate(DataImportRecordBase):
    """创建数据导入记录"""
    pass

class DataImportRecordUpdate(BaseModel):
    """更新数据导入记录"""
    import_status: Optional[ImportStatus] = None
    progress_percentage: Optional[float] = None
    parse_config: Optional[Dict[str, Any]] = None
    metadata_config: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    is_cf_compliant: Optional[bool] = None
    compliance_score: Optional[float] = None
    output_file_path: Optional[str] = None
    tds_url: Optional[str] = None
    opendap_url: Optional[str] = None
    conversion_time: Optional[float] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

class DataImportRecord(DataImportRecordBase):
    """数据导入记录完整模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    upload_path: Optional[str] = None
    column_count: Optional[int] = None
    row_count: Optional[int] = None
    parse_config: Optional[Dict[str, Any]] = None
    metadata_config: Optional[Dict[str, Any]] = None
    validation_result: Optional[Dict[str, Any]] = None
    is_cf_compliant: bool = False
    compliance_score: Optional[float] = None
    output_file_path: Optional[str] = None
    tds_url: Optional[str] = None
    opendap_url: Optional[str] = None
    conversion_time: Optional[float] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    upload_time: datetime
    start_processing_time: Optional[datetime] = None
    completion_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

class FileOperationBase(BaseModel):
    """文件操作基础模式"""
    operation_type: str = Field(..., description="操作类型")
    operation_status: str = Field(..., description="操作状态")
    input_path: Optional[str] = Field(None, description="输入文件路径")
    output_path: Optional[str] = Field(None, description="输出文件路径")

class FileOperationCreate(FileOperationBase):
    """创建文件操作记录"""
    import_record_id: int = Field(..., description="导入记录ID")

class FileOperation(FileOperationBase):
    """文件操作完整模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    import_record_id: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    operation_log: Optional[str] = None
    operation_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class DatasetTemplateBase(BaseModel):
    """数据集模板基础模式"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    category: Optional[str] = Field(None, description="模板分类")
    file_types: Optional[List[str]] = Field(None, description="适用文件类型")
    data_patterns: Optional[Dict[str, Any]] = Field(None, description="数据模式匹配规则")

class DatasetTemplateCreate(DatasetTemplateBase):
    """创建数据集模板"""
    global_attributes_template: Optional[Dict[str, Any]] = Field(None, description="全局属性模板")
    variable_mapping_rules: Optional[Dict[str, Any]] = Field(None, description="变量映射规则")
    coordinate_detection_rules: Optional[Dict[str, Any]] = Field(None, description="坐标检测规则")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    required_attributes: Optional[List[str]] = Field(None, description="必需属性列表")
    created_by: Optional[str] = Field(None, description="创建者")

class DatasetTemplate(DatasetTemplateBase):
    """数据集模板完整模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    global_attributes_template: Optional[Dict[str, Any]] = None
    variable_mapping_rules: Optional[Dict[str, Any]] = None
    coordinate_detection_rules: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    required_attributes: Optional[List[str]] = None
    usage_count: int = 0
    success_rate: float = 0.0
    is_active: bool = True
    is_builtin: bool = False
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class CFStandardNameBase(BaseModel):
    """CF标准名称基础模式"""
    standard_name: str = Field(..., description="CF标准名称")
    canonical_units: Optional[str] = Field(None, description="标准单位")
    description: Optional[str] = Field(None, description="描述")
    category: Optional[str] = Field(None, description="分类")

class CFStandardNameCreate(CFStandardNameBase):
    """创建CF标准名称"""
    grib: Optional[str] = Field(None, description="GRIB参数")
    amip: Optional[str] = Field(None, description="AMIP标识")
    aliases: Optional[List[str]] = Field(None, description="别名列表")
    related_names: Optional[List[str]] = Field(None, description="相关名称")
    cf_version: Optional[str] = Field(None, description="CF版本")
    source_url: Optional[str] = Field(None, description="来源URL")

class CFStandardName(CFStandardNameBase):
    """CF标准名称完整模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    grib: Optional[str] = None
    amip: Optional[str] = None
    aliases: Optional[List[str]] = None
    related_names: Optional[List[str]] = None
    usage_count: int = 0
    last_used: Optional[datetime] = None
    cf_version: Optional[str] = None
    source_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UserPreferenceBase(BaseModel):
    """用户偏好基础模式"""
    user_id: str = Field(..., description="用户ID")
    user_name: Optional[str] = Field(None, description="用户名")
    preferred_file_encoding: str = Field("utf-8", description="首选文件编码")
    auto_detect_variables: bool = Field(True, description="是否自动检测变量")
    auto_apply_cf_standards: bool = Field(True, description="是否自动应用CF标准")

class UserPreferenceCreate(UserPreferenceBase):
    """创建用户偏好"""
    default_global_attributes: Optional[Dict[str, Any]] = Field(None, description="默认全局属性")
    default_institution: Optional[str] = Field(None, description="默认机构")
    default_creator_name: Optional[str] = Field(None, description="默认创建者姓名")
    default_creator_email: Optional[str] = Field(None, description="默认创建者邮箱")
    validation_strictness: str = Field("standard", description="验证严格程度")
    auto_fix_issues: bool = Field(True, description="是否自动修复问题")
    interface_language: str = Field("zh", description="界面语言")
    timezone: str = Field("Asia/Shanghai", description="时区")

class UserPreferenceUpdate(BaseModel):
    """更新用户偏好"""
    user_name: Optional[str] = None
    default_global_attributes: Optional[Dict[str, Any]] = None
    preferred_file_encoding: Optional[str] = None
    auto_detect_variables: Optional[bool] = None
    auto_apply_cf_standards: Optional[bool] = None
    default_institution: Optional[str] = None
    default_creator_name: Optional[str] = None
    default_creator_email: Optional[str] = None
    validation_strictness: Optional[str] = None
    auto_fix_issues: Optional[bool] = None
    interface_language: Optional[str] = None
    timezone: Optional[str] = None

class UserPreference(UserPreferenceBase):
    """用户偏好完整模式"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    default_global_attributes: Optional[Dict[str, Any]] = None
    default_institution: Optional[str] = None
    default_creator_name: Optional[str] = None
    default_creator_email: Optional[str] = None
    validation_strictness: str = "standard"
    auto_fix_issues: bool = True
    interface_language: str = "zh"
    timezone: str = "Asia/Shanghai"
    created_at: datetime
    updated_at: datetime

# 复合响应模式
class ImportProgress(BaseModel):
    """导入进度响应"""
    temp_id: str = Field(..., description="临时文件标识")
    import_status: ImportStatus = Field(..., description="导入状态")
    progress_percentage: float = Field(..., description="进度百分比")
    current_step: str = Field(..., description="当前步骤")
    steps_completed: int = Field(..., description="已完成步骤数")
    total_steps: int = Field(..., description="总步骤数")
    estimated_time_remaining: Optional[float] = Field(None, description="预计剩余时间（秒）")
    error_message: Optional[str] = Field(None, description="错误信息")

class ImportSummary(BaseModel):
    """导入摘要"""
    total_imports: int = Field(..., description="总导入数")
    successful_imports: int = Field(..., description="成功导入数")
    failed_imports: int = Field(..., description="失败导入数")
    in_progress_imports: int = Field(..., description="进行中导入数")
    average_processing_time: float = Field(..., description="平均处理时间")
    top_file_types: List[Dict[str, Union[str, int]]] = Field(..., description="主要文件类型统计")
    recent_imports: List[DataImportRecord] = Field(..., description="最近导入记录")

class TemplateMatch(BaseModel):
    """模板匹配结果"""
    template: DatasetTemplate = Field(..., description="匹配的模板")
    confidence: float = Field(..., description="匹配置信度")
    matched_patterns: List[str] = Field(..., description="匹配的模式")
    suggested_adjustments: Dict[str, Any] = Field(..., description="建议的调整")

class SmartSuggestion(BaseModel):
    """智能建议"""
    type: str = Field(..., description="建议类型")
    title: str = Field(..., description="建议标题")
    description: str = Field(..., description="建议描述")
    confidence: float = Field(..., description="置信度")
    suggested_value: Optional[Any] = Field(None, description="建议值")
    current_value: Optional[Any] = Field(None, description="当前值")
    action_required: bool = Field(False, description="是否需要用户操作")
    auto_applicable: bool = Field(False, description="是否可自动应用")
