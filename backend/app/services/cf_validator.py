"""
CF-1.8规范验证服务
检查NetCDF文件是否符合CF-1.8标准
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import xarray as xr
import numpy as np
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    CRITICAL = "critical"  # 严重错误，必须修复
    WARNING = "warning"   # 警告，建议修复
    INFO = "info"         # 信息提示


@dataclass
class ValidationIssue:
    """验证问题"""
    level: ValidationLevel
    code: str
    message: str
    location: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    issues: List[ValidationIssue]
    cf_version: Optional[str] = None
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.CRITICAL]
    
    @property
    def warning_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.WARNING]


class CFValidator:
    """CF-1.8规范验证器"""
    
    # CF-1.8标准的必需全局属性
    REQUIRED_GLOBAL_ATTRS = {
        'Conventions': 'CF-1.8',
        'title': str,
        'institution': str,
        'source': str,
        'history': str,
        'references': str,
    }
    
    # 标准坐标变量名称
    STANDARD_COORD_NAMES = {
        'longitude': ['longitude', 'lon', 'x'],
        'latitude': ['latitude', 'lat', 'y'], 
        'time': ['time', 't'],
        'depth': ['depth', 'z', 'level'],
        'pressure': ['pressure', 'pres'],
    }
    
    # 常见的standard_name
    COMMON_STANDARD_NAMES = {
        'sea_water_temperature': ['temperature', 'temp', 't'],
        'sea_water_salinity': ['salinity', 'salt', 's'],
        'sea_water_pressure': ['pressure', 'pres', 'p'],
        'depth': ['depth', 'z'],
    }
    
    def __init__(self):
        self.issues = []
    
    def validate_file(self, file_path: str) -> ValidationResult:
        """验证NetCDF文件"""
        self.issues = []
        
        try:
            with xr.open_dataset(file_path, decode_times=False) as ds:
                logger.info(f"开始验证文件: {file_path}")
                
                # 检查全局属性
                self._check_global_attributes(ds)
                
                # 检查坐标变量
                self._check_coordinate_variables(ds)
                
                # 检查数据变量
                self._check_data_variables(ds)
                
                # 检查时间变量
                self._check_time_variables(ds)
                
                # 检查单位
                self._check_units(ds)
                
                # 检查缺失值
                self._check_missing_values(ds)
                
                # 检查维度
                self._check_dimensions(ds)
                
        except Exception as e:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                code="FILE_READ_ERROR",
                message=f"无法读取NetCDF文件: {str(e)}",
                location="file"
            ))
        
        # 判断是否通过验证
        is_valid = len(self.critical_issues) == 0
        cf_version = self._get_cf_version()
        
        return ValidationResult(
            is_valid=is_valid,
            issues=self.issues.copy(),
            cf_version=cf_version
        )
    
    @property
    def critical_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == ValidationLevel.CRITICAL]
    
    def _get_cf_version(self) -> Optional[str]:
        """获取CF版本"""
        for issue in self.issues:
            if issue.code == "CONVENTIONS_FOUND":
                return issue.message.split(": ")[-1]
        return None
    
    def _check_global_attributes(self, ds: xr.Dataset):
        """检查全局属性"""
        attrs = ds.attrs
        
        # 检查Conventions属性
        if 'Conventions' not in attrs:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                code="MISSING_CONVENTIONS",
                message="缺少Conventions属性",
                location="global",
                suggestion="添加 Conventions = 'CF-1.8'"
            ))
        else:
            conventions = attrs['Conventions']
            if not isinstance(conventions, str) or 'CF' not in conventions:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    code="INVALID_CONVENTIONS",
                    message=f"Conventions属性无效: {conventions}",
                    location="global",
                    suggestion="设置 Conventions = 'CF-1.8'"
                ))
            else:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    code="CONVENTIONS_FOUND",
                    message=f"发现CF版本: {conventions}",
                    location="global"
                ))
        
        # 检查其他推荐的全局属性
        recommended_attrs = ['title', 'institution', 'source', 'history']
        for attr in recommended_attrs:
            if attr not in attrs:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code=f"MISSING_{attr.upper()}",
                    message=f"缺少推荐的全局属性: {attr}",
                    location="global",
                    suggestion=f"添加 {attr} 属性"
                ))
    
    def _check_coordinate_variables(self, ds: xr.Dataset):
        """检查坐标变量"""
        coords = ds.coords
        
        # 检查是否有经纬度坐标
        has_lon = any(name in coords for names in self.STANDARD_COORD_NAMES['longitude'] for name in names)
        has_lat = any(name in coords for names in self.STANDARD_COORD_NAMES['latitude'] for name in names)
        
        if not has_lon:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="MISSING_LONGITUDE",
                message="未找到经度坐标变量",
                location="coordinates",
                suggestion="添加经度坐标变量，建议命名为 'longitude'"
            ))
        
        if not has_lat:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="MISSING_LATITUDE", 
                message="未找到纬度坐标变量",
                location="coordinates",
                suggestion="添加纬度坐标变量，建议命名为 'latitude'"
            ))
        
        # 检查坐标变量的属性
        for coord_name, coord_var in coords.items():
            self._check_coordinate_attributes(coord_name, coord_var)
    
    def _check_coordinate_attributes(self, coord_name: str, coord_var: xr.DataArray):
        """检查单个坐标变量的属性"""
        attrs = coord_var.attrs
        
        # 检查units属性
        if 'units' not in attrs:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="COORD_MISSING_UNITS",
                message=f"坐标变量 '{coord_name}' 缺少units属性",
                location=f"coordinate:{coord_name}",
                suggestion="添加适当的units属性"
            ))
        
        # 检查standard_name属性
        if 'standard_name' not in attrs:
            # 尝试推断standard_name
            suggested_standard_name = self._suggest_standard_name(coord_name)
            if suggested_standard_name:
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="COORD_MISSING_STANDARD_NAME",
                    message=f"坐标变量 '{coord_name}' 缺少standard_name属性",
                    location=f"coordinate:{coord_name}",
                    suggestion=f"建议添加 standard_name = '{suggested_standard_name}'"
                ))
    
    def _check_data_variables(self, ds: xr.Dataset):
        """检查数据变量"""
        data_vars = ds.data_vars
        
        if not data_vars:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="NO_DATA_VARIABLES",
                message="数据集中没有数据变量",
                location="variables"
            ))
        
        for var_name, var in data_vars.items():
            self._check_data_variable_attributes(var_name, var)
    
    def _check_data_variable_attributes(self, var_name: str, var: xr.DataArray):
        """检查单个数据变量的属性"""
        attrs = var.attrs
        
        # 检查long_name或standard_name
        if 'long_name' not in attrs and 'standard_name' not in attrs:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="VAR_MISSING_DESCRIPTION",
                message=f"数据变量 '{var_name}' 缺少long_name或standard_name属性",
                location=f"variable:{var_name}",
                suggestion="添加long_name或standard_name属性来描述变量"
            ))
        
        # 检查units属性
        if 'units' not in attrs:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="VAR_MISSING_UNITS",
                message=f"数据变量 '{var_name}' 缺少units属性",
                location=f"variable:{var_name}",
                suggestion="添加units属性"
            ))
    
    def _check_time_variables(self, ds: xr.Dataset):
        """检查时间变量"""
        time_vars = []
        
        # 查找时间变量
        for var_name, var in ds.variables.items():
            attrs = var.attrs
            if (var_name.lower() in ['time', 't'] or 
                attrs.get('standard_name') == 'time' or
                'time' in attrs.get('units', '').lower()):
                time_vars.append((var_name, var))
        
        if not time_vars:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="NO_TIME_VARIABLE",
                message="未找到时间变量",
                location="time"
            ))
            return
        
        # 检查时间变量的格式
        for var_name, var in time_vars:
            self._check_time_variable_format(var_name, var)
    
    def _check_time_variable_format(self, var_name: str, var: xr.DataArray):
        """检查时间变量格式"""
        attrs = var.attrs
        units = attrs.get('units', '')
        
        # 检查时间单位格式
        time_unit_pattern = re.compile(r'(seconds|minutes|hours|days) since \d{4}-\d{2}-\d{2}')
        if not time_unit_pattern.match(units):
            self.issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                code="INVALID_TIME_UNITS",
                message=f"时间变量 '{var_name}' 的units格式不规范: {units}",
                location=f"time:{var_name}",
                suggestion="使用类似 'days since YYYY-MM-DD HH:MM:SS' 的格式"
            ))
        
        # 检查calendar属性
        if 'calendar' not in attrs:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                code="TIME_MISSING_CALENDAR",
                message=f"时间变量 '{var_name}' 缺少calendar属性",
                location=f"time:{var_name}",
                suggestion="建议添加 calendar = 'gregorian'"
            ))
    
    def _check_units(self, ds: xr.Dataset):
        """检查单位"""
        # 这里可以添加更详细的单位检查逻辑
        # 比如检查单位是否符合UDUNITS标准
        pass
    
    def _check_missing_values(self, ds: xr.Dataset):
        """检查缺失值"""
        for var_name, var in ds.data_vars.items():
            attrs = var.attrs
            
            # 检查是否定义了缺失值
            missing_value_attrs = ['_FillValue', 'missing_value']
            has_missing_value = any(attr in attrs for attr in missing_value_attrs)
            
            if not has_missing_value and var.isnull().any():
                self.issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    code="MISSING_VALUE_NOT_DEFINED",
                    message=f"变量 '{var_name}' 包含缺失值但未定义_FillValue",
                    location=f"variable:{var_name}",
                    suggestion="添加_FillValue属性"
                ))
    
    def _check_dimensions(self, ds: xr.Dataset):
        """检查维度"""
        # 检查维度名称是否规范
        dims = ds.dims
        
        # 检查是否有无限维度
        unlimited_dims = [dim for dim, size in dims.items() if size == 0]
        if unlimited_dims:
            self.issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                code="UNLIMITED_DIMENSIONS",
                message=f"发现无限维度: {', '.join(unlimited_dims)}",
                location="dimensions"
            ))
    
    def _suggest_standard_name(self, var_name: str) -> Optional[str]:
        """根据变量名推断standard_name"""
        var_name_lower = var_name.lower()
        
        for standard_name, common_names in self.COMMON_STANDARD_NAMES.items():
            if any(name in var_name_lower for name in common_names):
                return standard_name
        
        # 坐标变量的standard_name
        for standard_coord, names in self.STANDARD_COORD_NAMES.items():
            if any(name in var_name_lower for name in names):
                return standard_coord
        
        return None


def validate_netcdf_file(file_path: str) -> ValidationResult:
    """验证NetCDF文件的CF-1.8规范符合性"""
    validator = CFValidator()
    return validator.validate_file(file_path)


if __name__ == "__main__":
    # 测试代码
    import sys
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        result = validate_netcdf_file(file_path)
        
        print(f"文件: {file_path}")
        print(f"验证结果: {'通过' if result.is_valid else '未通过'}")
        print(f"CF版本: {result.cf_version}")
        print(f"严重问题: {len(result.critical_issues)}")
        print(f"警告问题: {len(result.warning_issues)}")
        
        for issue in result.issues:
            print(f"[{issue.level.value.upper()}] {issue.code}: {issue.message}")
            if issue.suggestion:
                print(f"  建议: {issue.suggestion}")
