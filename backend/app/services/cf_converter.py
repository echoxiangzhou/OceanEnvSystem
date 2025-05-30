"""
CF-1.8规范转换服务
将不符合CF-1.8标准的NetCDF文件转换为标准格式
"""

import os
import logging
import shutil
from typing import Dict, List, Optional, Any
from datetime import datetime
import xarray as xr
import numpy as np
import pandas as pd
from .cf_validator import CFValidator, ValidationResult, ValidationLevel

logger = logging.getLogger(__name__)


class CFConverter:
    """CF-1.8规范转换器"""
    
    # 变量名映射表
    VARIABLE_NAME_MAPPING = {
        # 温度相关
        'temp': 'temperature',
        't': 'temperature', 
        'sst': 'sea_surface_temperature',
        'temperature': 'sea_water_temperature',
        
        # 盐度相关
        'salt': 'salinity',
        's': 'salinity',
        'salinity': 'sea_water_salinity',
        
        # 压力相关
        'pres': 'pressure',
        'p': 'pressure',
        'pressure': 'sea_water_pressure',
        
        # 坐标相关
        'lon': 'longitude',
        'x': 'longitude',
        'lat': 'latitude', 
        'y': 'latitude',
        't': 'time',
        'z': 'depth',
        'level': 'depth',
    }
    
    # standard_name映射表
    STANDARD_NAME_MAPPING = {
        'temperature': 'sea_water_temperature',
        'salinity': 'sea_water_salinity', 
        'pressure': 'sea_water_pressure',
        'longitude': 'longitude',
        'latitude': 'latitude',
        'time': 'time',
        'depth': 'depth',
    }
    
    # 单位映射表
    UNITS_MAPPING = {
        'sea_water_temperature': 'degree_C',
        'sea_water_salinity': 'psu',
        'sea_water_pressure': 'dbar',
        'longitude': 'degrees_east',
        'latitude': 'degrees_north', 
        'depth': 'm',
        'time': 'days since 1970-01-01 00:00:00',
    }
    
    def __init__(self):
        self.validator = CFValidator()
    
    def convert_file(self, input_path: str, output_path: str, 
                    auto_fix: bool = True, backup: bool = True) -> Dict[str, Any]:
        """
        转换NetCDF文件为CF-1.8标准格式
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            auto_fix: 是否自动修复问题
            backup: 是否备份原文件
            
        Returns:
            转换结果字典
        """
        import tempfile
        
        # 尝试导入fcntl（Unix/Linux/macOS），Windows系统没有此模块
        try:
            import fcntl
            use_fcntl = True
        except ImportError:
            use_fcntl = False
            logger.warning("fcntl模块不可用，将使用替代文件锁定机制")
        
        result = {
            'success': False,
            'message': '',
            'issues_fixed': [],
            'remaining_issues': [],
            'backup_path': None
        }
        
        # 文件锁对象
        lock_file = None
        
        try:
            # 创建文件锁，避免并发访问
            lock_path = input_path + '.lock'
            
            if use_fcntl:
                # Unix/Linux/macOS系统使用fcntl
                lock_file = open(lock_path, 'w')
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    result['message'] = '文件正在被其他进程处理，跳过转换'
                    logger.warning(f"文件被锁定，跳过: {input_path}")
                    return result
            else:
                # Windows系统或其他系统使用文件存在性检查
                if os.path.exists(lock_path):
                    result['message'] = '文件正在被其他进程处理，跳过转换'
                    logger.warning(f"发现锁文件，跳过: {input_path}")
                    return result
                else:
                    # 创建锁文件
                    lock_file = open(lock_path, 'w')
                    lock_file.write(f"locked_by_pid_{os.getpid()}")
                    lock_file.flush()
            
            # 验证输入文件
            logger.info(f"开始验证文件: {input_path}")
            validation_result = self.validator.validate_file(input_path)
            
            if validation_result.is_valid:
                # 文件已经符合CF标准，直接复制
                if input_path != output_path:
                    import shutil
                    shutil.copy2(input_path, output_path)
                result['success'] = True
                result['message'] = '文件已符合CF-1.8标准'
                
                # 提取并保存元数据到数据库（标准文件）
                try:
                    self._extract_and_save_metadata(output_path, "standard")
                    logger.info(f"标准文件元数据已保存到数据库: {output_path}")
                except Exception as e:
                    logger.warning(f"保存标准文件元数据失败: {str(e)}")
                
                return result
            
            # 备份原文件
            if backup:
                # 将备份文件保存到processing目录
                processing_dir = os.path.join(os.getcwd(), "data", "processing")
                os.makedirs(processing_dir, exist_ok=True)
                
                # 生成备份文件名
                input_filename = os.path.basename(input_path)
                backup_filename = f"backup_{input_filename}"
                backup_path = os.path.join(processing_dir, backup_filename)
                
                import shutil
                if not os.path.exists(backup_path):  # 避免重复备份
                    shutil.copy2(input_path, backup_path)
                    result['backup_path'] = backup_path
                    logger.info(f"已备份原文件至: {backup_path}")
                else:
                    result['backup_path'] = backup_path
                    logger.info(f"备份文件已存在，跳过备份: {backup_path}")
            
            # 加载数据集
            logger.info(f"正在加载数据集: {input_path}")
            converted_ds = None
            
            # 使用安全的方式加载数据集，避免编码冲突
            try:
                # 先尝试不解码时间的方式加载
                with xr.open_dataset(input_path, decode_times=False, engine='netcdf4') as ds:
                    # 创建转换后的数据集
                    converted_ds = self._convert_dataset(ds, validation_result, auto_fix)
            except Exception as e:
                logger.warning(f"使用decode_times=False加载失败，尝试其他方式: {e}")
                # 如果上述方式失败，尝试直接加载
                try:
                    with xr.open_dataset(input_path, engine='netcdf4') as ds:
                        converted_ds = self._convert_dataset(ds, validation_result, auto_fix)
                except Exception as e2:
                    # 最后尝试使用h5netcdf引擎
                    try:
                        with xr.open_dataset(input_path, engine='h5netcdf') as ds:
                            converted_ds = self._convert_dataset(ds, validation_result, auto_fix)
                    except Exception as e3:
                        logger.error(f"所有加载方式均失败: {e3}")
                        raise e3
            
            if converted_ds is None:
                raise RuntimeError("数据集转换失败")
            
            # 保存转换后的文件
            self._save_dataset(converted_ds, output_path)
            
            # 验证转换结果
            final_validation = self.validator.validate_file(output_path)
            
            result['success'] = True
            result['message'] = '文件转换完成'
            result['issues_fixed'] = self._get_fixed_issues(validation_result, final_validation)
            result['remaining_issues'] = [
                {
                    'level': issue.level.value,
                    'code': issue.code,
                    'message': issue.message,
                    'location': issue.location
                }
                for issue in final_validation.issues
                if issue.level == ValidationLevel.CRITICAL
            ]
            
            # 转换成功后，提取并保存元数据到数据库
            try:
                self._extract_and_save_metadata(output_path, "standard")
                logger.info(f"转换成功，元数据已保存到数据库: {output_path}")
            except Exception as e:
                logger.warning(f"保存元数据失败: {str(e)}")
                # 不影响主要的转换流程，只记录警告
            
            logger.info(f"文件转换成功: {input_path} -> {output_path}")
            
        except Exception as e:
            result['message'] = f'转换失败: {str(e)}'
            logger.error(f"文件转换失败: {str(e)}", exc_info=True)
        finally:
            # 释放文件锁
            if lock_file:
                try:
                    if use_fcntl:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    lock_file.close()
                    # 删除锁文件
                    if os.path.exists(lock_path):
                        os.unlink(lock_path)
                except Exception as e:
                    logger.warning(f"释放文件锁失败: {e}")
        
        return result
    
    def _convert_dataset(self, ds: xr.Dataset, validation_result: ValidationResult, 
                        auto_fix: bool) -> xr.Dataset:
        """转换数据集"""
        # 创建新的数据集副本
        new_ds = ds.copy(deep=True)
        
        # 预处理：清理可能冲突的编码属性
        new_ds = self._preprocess_encoding_attributes(new_ds)
        
        if auto_fix:
            # 修复全局属性
            new_ds = self._fix_global_attributes(new_ds, validation_result)
            
            # 修复变量属性
            new_ds = self._fix_variable_attributes(new_ds, validation_result)
            
            # 修复坐标变量
            new_ds = self._fix_coordinate_variables(new_ds, validation_result)
            
            # 修复时间变量
            new_ds = self._fix_time_variables(new_ds, validation_result)
            
            # 修复缺失值
            new_ds = self._fix_missing_values(new_ds, validation_result)
        
        return new_ds
    
    def _preprocess_encoding_attributes(self, ds: xr.Dataset) -> xr.Dataset:
        """预处理编码属性，避免xarray保存时的冲突"""
        # 创建数据集副本
        new_ds = ds.copy(deep=True)
        
        # 需要从属性中移除并转移到encoding的字段
        encoding_fields = ['_FillValue', 'missing_value', 'scale_factor', 'add_offset', 'dtype']
        
        for var_name in new_ds.variables:
            var = new_ds[var_name]
            
            # 初始化encoding字典
            if not hasattr(var, 'encoding') or var.encoding is None:
                var.encoding = {}
            
            # 检查并处理冲突的属性
            for field in encoding_fields:
                if field in var.attrs:
                    try:
                        # 将属性值移动到encoding中，确保类型兼容
                        attr_value = var.attrs[field]
                        
                        # 特殊处理_FillValue，确保数据类型匹配
                        if field == '_FillValue' and hasattr(var, 'dtype'):
                            if var.dtype.kind == 'f':  # 浮点数
                                attr_value = float(attr_value) if not (np.isscalar(attr_value) and np.isnan(attr_value)) else np.nan
                            elif var.dtype.kind in ['i', 'u']:  # 整数
                                if np.isscalar(attr_value) and np.isnan(attr_value):
                                    attr_value = -999
                                else:
                                    attr_value = int(attr_value)
                        
                        var.encoding[field] = attr_value
                        # 从attributes中删除
                        del var.attrs[field]
                        logger.debug(f"移动 {field} 从 {var_name}.attrs 到 encoding")
                        
                    except Exception as e:
                        logger.warning(f"处理 {var_name}.{field} 时出错: {e}")
                        # 如果处理失败，直接删除属性以避免冲突
                        del var.attrs[field]
        
        return new_ds
    
    def _fix_global_attributes(self, ds: xr.Dataset, validation_result: ValidationResult) -> xr.Dataset:
        """修复全局属性"""
        attrs = ds.attrs.copy()
        
        # 修复Conventions属性
        if 'Conventions' not in attrs or 'CF' not in str(attrs.get('Conventions', '')):
            attrs['Conventions'] = 'CF-1.8'
        
        # 添加缺失的推荐属性
        default_attrs = {
            'title': 'Ocean Environmental Data',
            'institution': 'Ocean Environmental Data System',
            'source': 'Converted from original format',
            'history': f'{datetime.now().isoformat()}: Converted to CF-1.8 standard',
            'references': 'CF Conventions: http://cfconventions.org/',
            'comment': 'Automatically converted to CF-1.8 standard'
        }
        
        for attr_name, default_value in default_attrs.items():
            if attr_name not in attrs:
                attrs[attr_name] = default_value
        
        # 更新数据集属性
        ds.attrs.update(attrs)
        return ds
    
    def _fix_variable_attributes(self, ds: xr.Dataset, validation_result: ValidationResult) -> xr.Dataset:
        """修复数据变量属性"""
        for var_name, var in ds.data_vars.items():
            attrs = var.attrs.copy()
            
            # 添加standard_name
            if 'standard_name' not in attrs and 'long_name' not in attrs:
                suggested_standard_name = self._get_suggested_standard_name(var_name)
                if suggested_standard_name:
                    attrs['standard_name'] = suggested_standard_name
                else:
                    attrs['long_name'] = var_name.replace('_', ' ').title()
            
            # 添加units
            if 'units' not in attrs:
                suggested_units = self._get_suggested_units(var_name, attrs.get('standard_name'))
                if suggested_units:
                    attrs['units'] = suggested_units
            
            # 更新变量属性
            ds[var_name].attrs.update(attrs)
        
        return ds
    
    def _fix_coordinate_variables(self, ds: xr.Dataset, validation_result: ValidationResult) -> xr.Dataset:
        """修复坐标变量"""
        for coord_name, coord_var in ds.coords.items():
            attrs = coord_var.attrs.copy()
            
            # 添加standard_name
            if 'standard_name' not in attrs:
                suggested_standard_name = self._get_suggested_standard_name(coord_name)
                if suggested_standard_name:
                    attrs['standard_name'] = suggested_standard_name
            
            # 添加units
            if 'units' not in attrs:
                suggested_units = self._get_suggested_units(coord_name, attrs.get('standard_name'))
                if suggested_units:
                    attrs['units'] = suggested_units
            
            # 添加axis属性（对于标准坐标）
            if coord_name.lower() in ['longitude', 'lon', 'x']:
                attrs['axis'] = 'X'
            elif coord_name.lower() in ['latitude', 'lat', 'y']:
                attrs['axis'] = 'Y'
            elif coord_name.lower() in ['time', 't']:
                attrs['axis'] = 'T'
            elif coord_name.lower() in ['depth', 'z', 'level']:
                attrs['axis'] = 'Z'
                attrs['positive'] = 'down'  # 海洋学约定，深度向下为正
            
            # 更新坐标变量属性
            ds[coord_name].attrs.update(attrs)
        
        return ds
    
    def _fix_time_variables(self, ds: xr.Dataset, validation_result: ValidationResult) -> xr.Dataset:
        """修复时间变量"""
        time_vars = []
        
        # 查找时间变量
        for var_name, var in ds.variables.items():
            if (var_name.lower() in ['time', 't'] or 
                var.attrs.get('standard_name') == 'time' or
                'time' in var.attrs.get('units', '').lower()):
                time_vars.append(var_name)
        
        for time_var_name in time_vars:
            time_var = ds[time_var_name]
            attrs = time_var.attrs.copy()
            
            # 修复时间单位格式
            units = attrs.get('units', '')
            if not units or 'since' not in units:
                # 尝试推断时间格式
                if time_var.dtype.kind in ['i', 'f']:  # 数值型时间
                    attrs['units'] = 'days since 1970-01-01 00:00:00'
                    attrs['calendar'] = 'gregorian'
            
            # 添加calendar属性
            if 'calendar' not in attrs:
                attrs['calendar'] = 'gregorian'
            
            # 更新时间变量属性
            ds[time_var_name].attrs.update(attrs)
        
        return ds
    
    def _fix_missing_values(self, ds: xr.Dataset, validation_result: ValidationResult) -> xr.Dataset:
        """修复缺失值"""
        for var_name, var in ds.data_vars.items():
            attrs = var.attrs.copy()
            
            # 检查是否有缺失值但未定义_FillValue
            if var.isnull().any() and '_FillValue' not in attrs and 'missing_value' not in attrs:
                # 根据数据类型设置适当的缺失值
                if var.dtype.kind == 'f':  # 浮点型
                    fill_value = np.nan
                elif var.dtype.kind == 'i':  # 整型
                    fill_value = -999
                else:
                    fill_value = None
                
                if fill_value is not None:
                    attrs['_FillValue'] = fill_value
            
            # 更新变量属性
            ds[var_name].attrs.update(attrs)
        
        return ds
    
    def _get_suggested_standard_name(self, var_name: str) -> Optional[str]:
        """获取建议的standard_name"""
        var_name_lower = var_name.lower()
        
        # 首先检查变量名映射
        if var_name_lower in self.VARIABLE_NAME_MAPPING:
            mapped_name = self.VARIABLE_NAME_MAPPING[var_name_lower]
            return self.STANDARD_NAME_MAPPING.get(mapped_name, mapped_name)
        
        # 然后检查部分匹配
        for key, value in self.VARIABLE_NAME_MAPPING.items():
            if key in var_name_lower:
                mapped_name = value
                return self.STANDARD_NAME_MAPPING.get(mapped_name, mapped_name)
        
        return None
    
    def _get_suggested_units(self, var_name: str, standard_name: Optional[str] = None) -> Optional[str]:
        """获取建议的单位"""
        # 优先使用standard_name查找单位
        if standard_name and standard_name in self.UNITS_MAPPING:
            return self.UNITS_MAPPING[standard_name]
        
        # 使用变量名查找单位
        var_name_lower = var_name.lower()
        
        # 检查映射后的变量名
        if var_name_lower in self.VARIABLE_NAME_MAPPING:
            mapped_name = self.VARIABLE_NAME_MAPPING[var_name_lower]
            standard_name = self.STANDARD_NAME_MAPPING.get(mapped_name, mapped_name)
            if standard_name in self.UNITS_MAPPING:
                return self.UNITS_MAPPING[standard_name]
        
        # 部分匹配
        if 'temp' in var_name_lower:
            return 'degree_C'
        elif 'sal' in var_name_lower:
            return 'psu'
        elif 'pres' in var_name_lower:
            return 'dbar'
        elif 'lon' in var_name_lower:
            return 'degrees_east'
        elif 'lat' in var_name_lower:
            return 'degrees_north'
        elif 'depth' in var_name_lower or 'z' in var_name_lower:
            return 'm'
        
        return None
    
    def _save_dataset(self, ds: xr.Dataset, output_path: str):
        """保存数据集"""
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 创建数据集副本以避免修改原始数据
        ds_copy = ds.copy(deep=True)
        
        # 清理可能与xarray编码冲突的属性
        encoding_attrs = ['_FillValue', 'missing_value', 'scale_factor', 'add_offset', 'dtype']
        
        for var_name in ds_copy.variables:
            var = ds_copy[var_name]
            attrs_to_remove = []
            
            # 检查并移除冲突的编码属性
            for attr in encoding_attrs:
                if attr in var.attrs:
                    # 保存到encoding中而不是attrs
                    if not hasattr(var, 'encoding'):
                        var.encoding = {}
                    
                    # 确保数据类型兼容
                    attr_value = var.attrs[attr]
                    if attr == '_FillValue' and hasattr(var, 'dtype'):
                        # 确保_FillValue与变量数据类型兼容
                        try:
                            if var.dtype.kind == 'f':  # 浮点数
                                attr_value = float(attr_value) if not np.isnan(attr_value) else np.nan
                            elif var.dtype.kind in ['i', 'u']:  # 整数
                                attr_value = int(attr_value) if not np.isnan(attr_value) else -999
                        except (ValueError, TypeError):
                            # 如果转换失败，使用默认值
                            if var.dtype.kind == 'f':
                                attr_value = np.nan
                            else:
                                attr_value = -999
                    
                    var.encoding[attr] = attr_value
                    attrs_to_remove.append(attr)
            
            # 从attributes中移除冲突的属性
            for attr in attrs_to_remove:
                del var.attrs[attr]
        
        # 尝试多种保存方式
        save_success = False
        last_error = None
        
        # 方式1: 使用netcdf4引擎
        if not save_success:
            try:
                logger.debug("尝试使用netcdf4引擎保存文件")
                ds_copy.to_netcdf(output_path, format='NETCDF4', engine='netcdf4')
                save_success = True
                logger.info(f"数据集已保存至: {output_path} (netcdf4引擎)")
            except Exception as e:
                last_error = e
                logger.warning(f"netcdf4引擎保存失败: {e}")
        
        # 方式2: 使用h5netcdf引擎
        if not save_success:
            try:
                logger.debug("尝试使用h5netcdf引擎保存文件")
                ds_copy.to_netcdf(output_path, format='NETCDF4', engine='h5netcdf')
                save_success = True
                logger.info(f"数据集已保存至: {output_path} (h5netcdf引擎)")
            except Exception as e:
                last_error = e
                logger.warning(f"h5netcdf引擎保存失败: {e}")
        
        # 方式3: 移除所有编码信息，使用默认设置
        if not save_success:
            try:
                logger.debug("尝试移除编码信息后保存文件")
                # 移除所有编码信息，使用默认编码
                for var_name in ds_copy.variables:
                    if hasattr(ds_copy[var_name], 'encoding'):
                        ds_copy[var_name].encoding = {}
                
                ds_copy.to_netcdf(output_path, format='NETCDF4', engine='netcdf4')
                save_success = True
                logger.info(f"使用默认编码保存数据集: {output_path}")
            except Exception as e:
                last_error = e
                logger.warning(f"默认编码保存失败: {e}")
        
        # 方式4: 使用NETCDF3_CLASSIC格式
        if not save_success:
            try:
                logger.debug("尝试使用NETCDF3_CLASSIC格式保存文件")
                # 移除所有编码信息
                for var_name in ds_copy.variables:
                    if hasattr(ds_copy[var_name], 'encoding'):
                        ds_copy[var_name].encoding = {}
                
                ds_copy.to_netcdf(output_path, format='NETCDF3_CLASSIC', engine='netcdf4')
                save_success = True
                logger.info(f"使用NETCDF3_CLASSIC格式保存数据集: {output_path}")
            except Exception as e:
                last_error = e
                logger.warning(f"NETCDF3_CLASSIC格式保存失败: {e}")
        
        if not save_success:
            error_msg = f"所有保存方式均失败，最后错误: {last_error}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _get_fixed_issues(self, original_validation: ValidationResult, 
                         final_validation: ValidationResult) -> List[Dict[str, Any]]:
        """获取已修复的问题列表"""
        original_codes = {issue.code for issue in original_validation.issues}
        final_codes = {issue.code for issue in final_validation.issues}
        
        fixed_codes = original_codes - final_codes
        
        fixed_issues = []
        for issue in original_validation.issues:
            if issue.code in fixed_codes:
                fixed_issues.append({
                    'level': issue.level.value,
                    'code': issue.code,
                    'message': issue.message,
                    'location': issue.location
                })
        
        return fixed_issues

    def _extract_and_save_metadata(self, file_path: str, processing_status: str):
        """提取并保存文件元数据到数据库"""
        try:
            # 动态导入避免循环依赖
            from app.services.metadata_extractor import extract_and_save_metadata
            extract_and_save_metadata(file_path, processing_status)
        except ImportError as e:
            logger.warning(f"无法导入元数据提取器: {str(e)}")
        except Exception as e:
            logger.error(f"提取和保存元数据失败: {str(e)}")
            raise


def convert_netcdf_to_cf(input_path: str, output_path: str, 
                        auto_fix: bool = True, backup: bool = True) -> Dict[str, Any]:
    """
    将NetCDF文件转换为CF-1.8标准格式
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径  
        auto_fix: 是否自动修复问题
        backup: 是否备份原文件
        
    Returns:
        转换结果字典
    """
    converter = CFConverter()
    return converter.convert_file(input_path, output_path, auto_fix, backup)


if __name__ == "__main__":
    # 测试代码
    import sys
    if len(sys.argv) > 2:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        
        result = convert_netcdf_to_cf(input_file, output_file)
        
        print(f"转换结果: {'成功' if result['success'] else '失败'}")
        print(f"消息: {result['message']}")
        
        if result['issues_fixed']:
            print("\n已修复的问题:")
            for issue in result['issues_fixed']:
                print(f"  - [{issue['level'].upper()}] {issue['code']}: {issue['message']}")
        
        if result['remaining_issues']:
            print("\n剩余问题:")
            for issue in result['remaining_issues']:
                print(f"  - [{issue['level'].upper()}] {issue['code']}: {issue['message']}")
