from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum as SQLAEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import enum

# 枚举类型定义
class FileTypeEnum(str, enum.Enum):
    CSV = "csv"
    EXCEL = "excel"
    CNV = "cnv"
    NETCDF = "netcdf"
    JSON = "json"
    XML = "xml"

class ImportStatusEnum(str, enum.Enum):
    UPLOADED = "uploaded"           # 已上传
    PARSING = "parsing"             # 解析中
    PARSED = "parsed"               # 解析完成
    VALIDATING = "validating"       # 验证中
    VALIDATED = "validated"         # 验证完成
    CONVERTING = "converting"       # 转换中
    COMPLETED = "completed"         # 转换完成
    FAILED = "failed"              # 失败
    CANCELLED = "cancelled"        # 取消

class ProcessingStatusEnum(str, enum.Enum):
    RAW = "raw"                    # 原始数据
    PROCESSING = "processing"       # 处理中
    STANDARD = "standard"          # 标准格式
    ARCHIVED = "archived"          # 已归档
    ERROR = "error"                # 处理错误

class ValidationLevelEnum(str, enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class NetCDFMetadata(Base):
    """NetCDF文件元数据表模型"""
    __tablename__ = "netcdf_metadata"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 文件基本信息
    file_path = Column(String(1000), unique=True, index=True, nullable=False, comment="文件路径")
    file_name = Column(String(255), nullable=False, comment="文件名")
    file_size = Column(Integer, comment="文件大小（字节）")
    file_hash = Column(String(64), index=True, comment="文件MD5哈希值")
    
    # CF规范信息
    cf_version = Column(String(20), comment="CF规范版本")
    is_cf_compliant = Column(Boolean, default=False, comment="是否符合CF规范")
    
    # 全局属性
    title = Column(String(500), comment="数据集标题")
    summary = Column(Text, comment="数据集摘要")
    institution = Column(String(255), comment="机构")
    source = Column(String(255), comment="数据来源")
    history = Column(Text, comment="处理历史")
    references = Column(Text, comment="参考文献")
    comment = Column(Text, comment="注释")
    conventions = Column(String(100), comment="约定")
    
    # 时空信息
    time_coverage_start = Column(DateTime, comment="时间范围开始")
    time_coverage_end = Column(DateTime, comment="时间范围结束")
    time_coverage_duration = Column(String(100), comment="时间范围持续时间")
    time_coverage_resolution = Column(String(100), comment="时间分辨率")
    
    geospatial_lat_min = Column(Float, comment="最小纬度")
    geospatial_lat_max = Column(Float, comment="最大纬度")
    geospatial_lon_min = Column(Float, comment="最小经度")
    geospatial_lon_max = Column(Float, comment="最大经度")
    geospatial_vertical_min = Column(Float, comment="最小深度/高度")
    geospatial_vertical_max = Column(Float, comment="最大深度/高度")
    
    # 数据变量信息
    variables = Column(JSON, comment="变量信息JSON")
    dimensions = Column(JSON, comment="维度信息JSON")
    
    # 质量控制信息
    qc_status = Column(String(50), comment="质量控制状态")
    qc_flags = Column(JSON, comment="质量控制标志")
    
    # 处理状态
    processing_status = Column(SQLAEnum(ProcessingStatusEnum), default=ProcessingStatusEnum.STANDARD, comment="处理状态")
    processing_log = Column(Text, comment="处理日志")
    
    # 关联导入记录
    import_record_id = Column(Integer, ForeignKey("data_import_records.id"), nullable=True, comment="关联的导入记录ID")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 建立关联关系
    import_record = relationship("DataImportRecord", back_populates="metadata_records")
    
    def __repr__(self):
        return f"<NetCDFMetadata(id={self.id}, file_name='{self.file_name}', processing_status='{self.processing_status}')>"

class DataImportRecord(Base):
    """数据导入记录表"""
    __tablename__ = "data_import_records"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 临时文件标识
    temp_id = Column(String(36), unique=True, index=True, nullable=False, comment="临时文件UUID")
    
    # 文件基本信息
    original_filename = Column(String(255), nullable=False, comment="原始文件名")
    file_type = Column(SQLAEnum(FileTypeEnum), nullable=False, comment="文件类型")
    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")
    file_hash = Column(String(64), index=True, comment="文件MD5哈希值")
    upload_path = Column(String(1000), comment="上传文件路径")
    
    # 导入状态
    import_status = Column(SQLAEnum(ImportStatusEnum), default=ImportStatusEnum.UPLOADED, comment="导入状态")
    progress_percentage = Column(Float, default=0.0, comment="处理进度百分比")
    
    # 解析信息
    parse_config = Column(JSON, comment="解析配置JSON")
    column_count = Column(Integer, comment="列数")
    row_count = Column(Integer, comment="行数")
    
    # 元数据配置
    metadata_config = Column(JSON, comment="元数据配置JSON")
    
    # 验证结果
    validation_result = Column(JSON, comment="验证结果JSON")
    is_cf_compliant = Column(Boolean, default=False, comment="是否符合CF规范")
    compliance_score = Column(Float, comment="合规性评分")
    
    # 转换结果
    output_file_path = Column(String(1000), comment="输出NetCDF文件路径")
    tds_url = Column(String(1000), comment="TDS服务访问URL")
    opendap_url = Column(String(1000), comment="OPeNDAP访问URL")
    conversion_time = Column(Float, comment="转换耗时（秒）")
    
    # 用户信息
    user_id = Column(String(50), comment="用户ID")
    user_name = Column(String(100), comment="用户名")
    user_email = Column(String(255), comment="用户邮箱")
    
    # 错误信息
    error_message = Column(Text, comment="错误信息")
    error_details = Column(JSON, comment="详细错误信息JSON")
    
    # 时间戳
    upload_time = Column(DateTime(timezone=True), server_default=func.now(), comment="上传时间")
    start_processing_time = Column(DateTime(timezone=True), comment="开始处理时间")
    completion_time = Column(DateTime(timezone=True), comment="完成时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 建立关联关系
    metadata_records = relationship("NetCDFMetadata", back_populates="import_record")
    validation_issues = relationship("ValidationIssue", back_populates="import_record", cascade="all, delete-orphan")
    file_operations = relationship("FileOperation", back_populates="import_record", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<DataImportRecord(id={self.id}, temp_id='{self.temp_id}', status='{self.import_status}')>"

class ValidationIssue(Base):
    """验证问题记录表"""
    __tablename__ = "validation_issues"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联导入记录
    import_record_id = Column(Integer, ForeignKey("data_import_records.id"), nullable=False, comment="导入记录ID")
    
    # 问题信息
    level = Column(SQLAEnum(ValidationLevelEnum), nullable=False, comment="问题级别")
    issue_code = Column(String(100), nullable=False, comment="问题代码")
    message = Column(Text, nullable=False, comment="问题描述")
    location = Column(String(255), comment="问题位置")
    suggestion = Column(Text, comment="修改建议")
    
    # 自动修复
    auto_fixable = Column(Boolean, default=False, comment="是否可自动修复")
    fixed = Column(Boolean, default=False, comment="是否已修复")
    fix_action = Column(Text, comment="修复操作记录")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    fixed_at = Column(DateTime(timezone=True), comment="修复时间")
    
    # 建立关联关系
    import_record = relationship("DataImportRecord", back_populates="validation_issues")
    
    def __repr__(self):
        return f"<ValidationIssue(id={self.id}, level='{self.level}', code='{self.issue_code}')>"

class FileOperation(Base):
    """文件操作记录表"""
    __tablename__ = "file_operations"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 关联导入记录
    import_record_id = Column(Integer, ForeignKey("data_import_records.id"), nullable=False, comment="导入记录ID")
    
    # 操作信息
    operation_type = Column(String(50), nullable=False, comment="操作类型: upload, parse, validate, convert, cleanup")
    operation_status = Column(String(50), nullable=False, comment="操作状态: pending, running, completed, failed")
    input_path = Column(String(1000), comment="输入文件路径")
    output_path = Column(String(1000), comment="输出文件路径")
    
    # 执行信息
    start_time = Column(DateTime(timezone=True), comment="开始时间")
    end_time = Column(DateTime(timezone=True), comment="结束时间")
    duration = Column(Float, comment="执行时长（秒）")
    
    # 结果信息
    success = Column(Boolean, default=False, comment="是否成功")
    error_message = Column(Text, comment="错误信息")
    operation_log = Column(Text, comment="操作日志")
    operation_metadata = Column(JSON, comment="操作元数据JSON")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 建立关联关系
    import_record = relationship("DataImportRecord", back_populates="file_operations")
    
    def __repr__(self):
        return f"<FileOperation(id={self.id}, type='{self.operation_type}', status='{self.operation_status}')>"

class DatasetTemplate(Base):
    """数据集模板表"""
    __tablename__ = "dataset_templates"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 模板基本信息
    name = Column(String(255), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    category = Column(String(100), comment="模板分类")
    
    # 适用条件
    file_types = Column(JSON, comment="适用文件类型")
    data_patterns = Column(JSON, comment="数据模式匹配规则")
    
    # 模板内容
    global_attributes_template = Column(JSON, comment="全局属性模板")
    variable_mapping_rules = Column(JSON, comment="变量映射规则")
    coordinate_detection_rules = Column(JSON, comment="坐标检测规则")
    
    # 验证规则
    validation_rules = Column(JSON, comment="验证规则")
    required_attributes = Column(JSON, comment="必需属性列表")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    success_rate = Column(Float, default=0.0, comment="成功率")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_builtin = Column(Boolean, default=False, comment="是否内置模板")
    
    # 创建者信息
    created_by = Column(String(100), comment="创建者")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<DatasetTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"

class CFStandardName(Base):
    """CF标准名称库表"""
    __tablename__ = "cf_standard_names"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # CF标准信息
    standard_name = Column(String(255), unique=True, nullable=False, index=True, comment="CF标准名称")
    canonical_units = Column(String(100), comment="标准单位")
    grib = Column(String(100), comment="GRIB参数")
    amip = Column(String(100), comment="AMIP标识")
    description = Column(Text, comment="描述")
    
    # 扩展信息
    category = Column(String(100), comment="分类")
    aliases = Column(JSON, comment="别名列表")
    related_names = Column(JSON, comment="相关名称")
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment="使用次数")
    last_used = Column(DateTime(timezone=True), comment="最后使用时间")
    
    # 来源信息
    cf_version = Column(String(20), comment="CF版本")
    source_url = Column(String(500), comment="来源URL")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<CFStandardName(id={self.id}, name='{self.standard_name}', units='{self.canonical_units}')>"

class UserPreference(Base):
    """用户偏好设置表"""
    __tablename__ = "user_preferences"
    
    # 主键
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # 用户信息
    user_id = Column(String(50), unique=True, nullable=False, index=True, comment="用户ID")
    user_name = Column(String(100), comment="用户名")
    
    # 默认配置
    default_global_attributes = Column(JSON, comment="默认全局属性")
    preferred_file_encoding = Column(String(50), default="utf-8", comment="首选文件编码")
    auto_detect_variables = Column(Boolean, default=True, comment="是否自动检测变量")
    auto_apply_cf_standards = Column(Boolean, default=True, comment="是否自动应用CF标准")
    
    # 导入偏好
    default_institution = Column(String(255), comment="默认机构")
    default_creator_name = Column(String(100), comment="默认创建者姓名")
    default_creator_email = Column(String(255), comment="默认创建者邮箱")
    
    # 验证偏好
    validation_strictness = Column(String(50), default="standard", comment="验证严格程度: lenient, standard, strict")
    auto_fix_issues = Column(Boolean, default=True, comment="是否自动修复问题")
    
    # UI偏好
    interface_language = Column(String(10), default="zh", comment="界面语言")
    timezone = Column(String(50), default="Asia/Shanghai", comment="时区")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<UserPreference(id={self.id}, user_id='{self.user_id}')>"
