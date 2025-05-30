"""
NetCDF文件元数据提取服务
从NetCDF文件中提取元数据信息并保存到数据库
"""

import os
import hashlib
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import xarray as xr
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from app.db.models import NetCDFMetadata
from app.db.session import get_db

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """NetCDF元数据提取器"""
    
    def __init__(self):
        pass
    
    def extract_metadata(self, file_path: str, processing_status: str = "standard") -> Dict[str, Any]:
        """
        从NetCDF文件中提取元数据
        
        Args:
            file_path: NetCDF文件路径
            processing_status: 处理状态 (raw, processing, standard)
            
        Returns:
            提取的元数据字典
        """
        try:
            metadata = {}
            
            # 文件基本信息
            metadata.update(self._extract_file_info(file_path))
            
            # 使用xarray打开文件并提取元数据
            with xr.open_dataset(file_path, decode_times=False) as ds:
                # 全局属性
                metadata.update(self._extract_global_attributes(ds))
                
                # 特殊处理：如果没有title，生成标准格式的title
                if not metadata.get('title'):
                    file_name = metadata.get('file_name', os.path.basename(file_path))
                    # 去掉文件扩展名
                    if file_name.endswith(('.nc', '.netcdf', '.nc4')):
                        file_name = os.path.splitext(file_name)[0]
                    metadata['title'] = f"Ocean Environmental Data-{file_name}"
                
                # 时空信息
                metadata.update(self._extract_spatiotemporal_info(ds))
                
                # 变量和维度信息
                metadata.update(self._extract_variables_info(ds))
                
                # CF规范信息
                metadata.update(self._extract_cf_info(ds))
            
            # 设置处理状态
            metadata['processing_status'] = processing_status
            
            return metadata
            
        except Exception as e:
            logger.error(f"提取元数据失败: {file_path}, 错误: {str(e)}")
            raise
    
    def _extract_file_info(self, file_path: str) -> Dict[str, Any]:
        """提取文件基本信息"""
        info = {}
        
        # 文件路径和名称
        info['file_path'] = file_path
        info['file_name'] = os.path.basename(file_path)
        
        # 文件大小
        info['file_size'] = os.path.getsize(file_path)
        
        # 计算文件MD5哈希
        info['file_hash'] = self._calculate_file_hash(file_path)
        
        return info
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件MD5哈希值"""
        try:
            hash_md5 = hashlib.md5()
            
            # 对于大文件，分块读取以节省内存
            with open(file_path, "rb") as f:
                # 读取文件头部的一定字节数用于快速哈希（对于大型NetCDF文件）
                # 这样可以平衡性能和唯一性
                chunk_size = 8192
                bytes_read = 0
                max_bytes = 1024 * 1024  # 读取前1MB用于哈希计算
                
                while bytes_read < max_bytes:
                    chunk = f.read(min(chunk_size, max_bytes - bytes_read))
                    if not chunk:
                        break
                    hash_md5.update(chunk)
                    bytes_read += len(chunk)
                
                # 如果文件小于1MB，继续读取剩余部分
                if bytes_read < max_bytes:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        hash_md5.update(chunk)
            
            return hash_md5.hexdigest()
            
        except Exception as e:
            logger.warning(f"计算文件哈希失败 {file_path}: {str(e)}")
            return None
    
    def _extract_global_attributes(self, ds: xr.Dataset) -> Dict[str, Any]:
        """提取全局属性"""
        attrs = {}
        
        # 常见全局属性映射
        global_attr_mapping = {
            'title': 'title',
            'summary': 'summary',
            'institution': 'institution',
            'source': 'source',
            'history': 'history',
            'references': 'references',
            'comment': 'comment',
            'Conventions': 'conventions',
            'conventions': 'conventions',
        }
        
        for nc_attr, db_field in global_attr_mapping.items():
            if nc_attr in ds.attrs:
                value = ds.attrs[nc_attr]
                if isinstance(value, (bytes, np.bytes_)):
                    value = value.decode('utf-8', errors='ignore')
                attrs[db_field] = str(value) if value is not None else None
        
        return attrs
    
    def _extract_spatiotemporal_info(self, ds: xr.Dataset) -> Dict[str, Any]:
        """提取时空信息"""
        info = {}
        
        try:
            # 纬度信息
            lat_vars = ['lat', 'latitude', 'y']
            for var in lat_vars:
                if var in ds.coords or var in ds.data_vars:
                    lat_data = ds[var].values
                    if lat_data.size > 0:
                        info['geospatial_lat_min'] = float(np.nanmin(lat_data))
                        info['geospatial_lat_max'] = float(np.nanmax(lat_data))
                        break
            
            # 经度信息
            lon_vars = ['lon', 'longitude', 'x']
            for var in lon_vars:
                if var in ds.coords or var in ds.data_vars:
                    lon_data = ds[var].values
                    if lon_data.size > 0:
                        info['geospatial_lon_min'] = float(np.nanmin(lon_data))
                        info['geospatial_lon_max'] = float(np.nanmax(lon_data))
                        break
            
            # 垂直方向信息（深度/高度）
            vertical_vars = ['depth', 'z', 'level', 'pressure', 'height']
            for var in vertical_vars:
                if var in ds.coords or var in ds.data_vars:
                    vertical_data = ds[var].values
                    if vertical_data.size > 0:
                        info['geospatial_vertical_min'] = float(np.nanmin(vertical_data))
                        info['geospatial_vertical_max'] = float(np.nanmax(vertical_data))
                        break
            
            # 时间信息
            time_vars = ['time', 't']
            for var in time_vars:
                if var in ds.coords or var in ds.data_vars:
                    try:
                        # 尝试解析时间
                        time_data = ds[var]
                        if 'units' in time_data.attrs:
                            time_decoded = xr.decode_cf(ds)[var]
                            if time_decoded.size > 0:
                                time_values = pd.to_datetime(time_decoded.values)
                                info['time_coverage_start'] = time_values.min().to_pydatetime()
                                info['time_coverage_end'] = time_values.max().to_pydatetime()
                                
                                # 计算时间范围持续时间
                                duration = time_values.max() - time_values.min()
                                info['time_coverage_duration'] = str(duration)
                        break
                    except Exception as e:
                        logger.warning(f"解析时间信息失败: {str(e)}")
                        continue
        
        except Exception as e:
            logger.warning(f"提取时空信息失败: {str(e)}")
        
        return info
    
    def _extract_variables_info(self, ds: xr.Dataset) -> Dict[str, Any]:
        """提取变量和维度信息"""
        info = {}
        
        # 变量信息
        variables = {}
        for var_name, var in ds.data_vars.items():
            var_info = {
                'name': var_name,
                'dtype': str(var.dtype),
                'shape': list(var.shape),
                'dimensions': list(var.dims),
                'attributes': {}
            }
            
            # 变量属性
            for attr_name, attr_value in var.attrs.items():
                if isinstance(attr_value, (bytes, np.bytes_)):
                    attr_value = attr_value.decode('utf-8', errors='ignore')
                var_info['attributes'][attr_name] = str(attr_value) if attr_value is not None else None
            
            variables[var_name] = var_info
        
        info['variables'] = variables
        
        # 维度信息
        dimensions = {}
        for dim_name, dim_size in ds.dims.items():
            dimensions[dim_name] = {
                'name': dim_name,
                'size': int(dim_size)
            }
        
        info['dimensions'] = dimensions
        
        return info
    
    def _extract_cf_info(self, ds: xr.Dataset) -> Dict[str, Any]:
        """提取CF规范相关信息"""
        info = {}
        
        # CF版本
        if 'Conventions' in ds.attrs:
            conventions = ds.attrs['Conventions']
            if isinstance(conventions, (bytes, np.bytes_)):
                conventions = conventions.decode('utf-8', errors='ignore')
            info['conventions'] = str(conventions)
            
            # 提取CF版本号
            if 'CF' in str(conventions):
                cf_parts = str(conventions).split('CF-')
                if len(cf_parts) > 1:
                    version_part = cf_parts[1].split()[0].split(',')[0]
                    info['cf_version'] = f"CF-{version_part}"
        
        # 简单的CF规范符合性检查
        info['is_cf_compliant'] = self._check_basic_cf_compliance(ds)
        
        return info
    
    def _check_basic_cf_compliance(self, ds: xr.Dataset) -> bool:
        """简单的CF规范符合性检查"""
        try:
            # 检查是否有Conventions属性
            if 'Conventions' not in ds.attrs:
                return False
            
            # 检查是否声明了CF规范
            conventions = str(ds.attrs['Conventions'])
            if 'CF' not in conventions:
                return False
            
            # 检查是否有基本的坐标变量
            has_coords = False
            coord_vars = ['lat', 'latitude', 'lon', 'longitude', 'time', 'x', 'y', 't']
            for var in coord_vars:
                if var in ds.coords or var in ds.data_vars:
                    has_coords = True
                    break
            
            return has_coords
            
        except Exception:
            return False
    
    def save_metadata_to_db(self, metadata: Dict[str, Any], db: Session, force_update: bool = False) -> NetCDFMetadata:
        """
        保存元数据到数据库，支持去重和更新控制
        
        Args:
            metadata: 元数据字典
            db: 数据库会话
            force_update: 是否强制更新已存在的记录
            
        Returns:
            保存的元数据记录
        """
        try:
            file_path = metadata['file_path']
            file_size = metadata.get('file_size')
            
            # 多层检查以避免重复记录
            existing = None
            
            # 1. 首先按文件路径查找
            existing = db.query(NetCDFMetadata).filter(
                NetCDFMetadata.file_path == file_path
            ).first()
            
            # 2. 如果按路径没找到，按文件名和大小查找（处理文件移动的情况）
            if not existing and file_size:
                file_name = metadata.get('file_name')
                if file_name:
                    existing = db.query(NetCDFMetadata).filter(
                        NetCDFMetadata.file_name == file_name,
                        NetCDFMetadata.file_size == file_size
                    ).first()
            
            # 3. 如果按文件名+大小也没找到，检查文件哈希（如果有）
            if not existing and 'file_hash' in metadata and metadata['file_hash']:
                existing = db.query(NetCDFMetadata).filter(
                    NetCDFMetadata.file_hash == metadata['file_hash']
                ).first()
            
            if existing:
                if force_update:
                    # 强制更新现有记录
                    logger.info(f"强制更新现有元数据记录: {file_path} (ID: {existing.id})")
                    
                    # 保留原有的ID和创建时间
                    original_id = existing.id
                    original_created_at = existing.created_at
                    
                    # 更新所有字段
                    for key, value in metadata.items():
                        if hasattr(existing, key) and key != 'id':  # 不更新ID
                            setattr(existing, key, value)
                    
                    # 保持原有创建时间
                    existing.created_at = original_created_at
                    
                    db.commit()
                    db.refresh(existing)
                    logger.info(f"更新元数据记录成功: {file_path} (ID: {existing.id})")
                    return existing
                else:
                    # 不更新，返回现有记录
                    logger.info(f"文件元数据已存在，跳过创建: {file_path} (ID: {existing.id})")
                    return existing
            else:
                # 创建新记录
                db_metadata = NetCDFMetadata(**metadata)
                db.add(db_metadata)
                db.commit()
                db.refresh(db_metadata)
                logger.info(f"创建新元数据记录: {file_path} (ID: {db_metadata.id})")
                return db_metadata
                
        except Exception as e:
            db.rollback()
            logger.error(f"保存元数据到数据库失败: {str(e)}")
            raise
    
    def extract_and_save(self, file_path: str, processing_status: str = "standard", 
                        db: Session = None, force_update: bool = False) -> NetCDFMetadata:
        """
        提取元数据并保存到数据库
        
        Args:
            file_path: NetCDF文件路径
            processing_status: 处理状态
            db: 数据库会话
            force_update: 是否强制更新已存在的记录
            
        Returns:
            保存的元数据记录
        """
        if db is None:
            # 如果没有提供数据库会话，创建一个新的
            from app.db.session import SessionLocal
            db = SessionLocal()
            try:
                return self._extract_and_save_with_db(file_path, processing_status, db, force_update)
            finally:
                db.close()
        else:
            return self._extract_and_save_with_db(file_path, processing_status, db, force_update)
    
    def _extract_and_save_with_db(self, file_path: str, processing_status: str, 
                                 db: Session, force_update: bool = False) -> NetCDFMetadata:
        """使用提供的数据库会话提取并保存元数据"""
        
        # 在提取之前先检查是否已存在
        if not force_update:
            existing = db.query(NetCDFMetadata).filter(
                NetCDFMetadata.file_path == file_path
            ).first()
            
            if existing:
                logger.info(f"文件元数据已存在，跳过提取: {file_path} (ID: {existing.id})")
                return existing
        
        # 提取元数据
        metadata = self.extract_metadata(file_path, processing_status)
        
        # 保存到数据库
        return self.save_metadata_to_db(metadata, db, force_update)


# 全局实例
metadata_extractor = MetadataExtractor()


def extract_and_save_metadata(file_path: str, processing_status: str = "standard", 
                             force_update: bool = False) -> NetCDFMetadata:
    """
    便捷函数：提取并保存元数据
    
    Args:
        file_path: NetCDF文件路径
        processing_status: 处理状态
        force_update: 是否强制更新已存在的记录
        
    Returns:
        保存的元数据记录
    """
    return metadata_extractor.extract_and_save(file_path, processing_status, force_update=force_update) 