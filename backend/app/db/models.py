from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
from app.db.session import Base

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
    processing_status = Column(String(50), default="standard", comment="处理状态: raw, processing, standard")
    processing_log = Column(Text, comment="处理日志")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<NetCDFMetadata(id={self.id}, file_name='{self.file_name}', processing_status='{self.processing_status}')>"
