"""
CNV文件智能解析器

实现功能：
- 严格按照readcnv.mdc规范解析CNV文件
- 解析文件头部元数据（* 开头的行）
- 提取变量定义（# name行）
- 处理坏数据标记（# bad_flag）
- 解析时间和位置信息
- 提取仪器校准信息
- 自动识别CTD、ADCP等仪器类型
- 生成CF标准的元数据建议
- 全局属性智能生成
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from sqlalchemy.orm import Session

# 导入新的CF变量识别引擎和全局属性生成器
from ..cf_standards.variable_identifier import CFVariableIdentifier, CFVariableSuggestion
from ..cf_standards.global_attributes import GlobalAttributeGenerator, GlobalAttributeSuggestion

logger = logging.getLogger(__name__)


class CNVParser:
    """CNV文件智能解析器"""
    
    # CTD变量映射表（按照SBE标准）- 保留作为备份
    CTD_VARIABLE_MAPPING = {
        # 温度相关
        'tv290c': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.95},
        'temp': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.9},
        'temperature': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.9},
        't090c': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.95},
        't190c': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.95},
        
        # 电导率相关
        'c0s/m': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.95},
        'c1s/m': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.95},
        'cond': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.9},
        'conductivity': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.9},
        
        # 压力和深度
        'prdm': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.95},
        'pressure': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.9},
        'press': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.9},
        'depsm': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.95},
        'depth': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.9},
        'depfm': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.9},
        
        # 盐度
        'sal00': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.95},
        'sal11': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.95},
        'salinity': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.9},
        'salt': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.85},
        
        # 溶解氧
        'sbeox0v': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.9},
        'sbeox1v': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.9},
        'oxygen': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.85},
        'do': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.8},
        
        # 荧光
        'fleco-afl': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.8},
        'fluorescence': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.75},
        'chl': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.8},
        
        # 浊度
        'turbidity': {'standard_name': 'sea_water_turbidity', 'units': 'NTU', 'confidence': 0.85},
        'turb': {'standard_name': 'sea_water_turbidity', 'units': 'NTU', 'confidence': 0.8},
        
        # pH
        'ph': {'standard_name': 'sea_water_ph_reported_on_total_scale', 'units': '1', 'confidence': 0.85},
        
        # 声速
        'svave': {'standard_name': 'speed_of_sound_in_sea_water', 'units': 'm s-1', 'confidence': 0.9},
        'sound_velocity': {'standard_name': 'speed_of_sound_in_sea_water', 'units': 'm s-1', 'confidence': 0.85},
        
        # 密度
        'density': {'standard_name': 'sea_water_density', 'units': 'kg m-3', 'confidence': 0.85},
        'sigma-t': {'standard_name': 'sea_water_sigma_t', 'units': 'kg m-3', 'confidence': 0.9},
        'sigma-theta': {'standard_name': 'sea_water_sigma_theta', 'units': 'kg m-3', 'confidence': 0.9},
        
        # 光学量
        'par': {'standard_name': 'downwelling_photosynthetic_photon_flux_in_sea_water', 'units': 'umol m-2 s-1', 'confidence': 0.8},
        'beam_transmission': {'standard_name': 'volume_beam_attenuation_coefficient_of_radiative_flux_in_sea_water', 'units': 'm-1', 'confidence': 0.8}
    }
    
    # 仪器类型识别模式
    INSTRUMENT_PATTERNS = {
        'ctd': ['sbe', 'seabird', 'ctd'],
        'adcp': ['adcp', 'workhorse', 'navigator'],
        'profiler': ['profiler', 'argo'],
        'mooring': ['mooring', 'buoy'],
        'glider': ['glider', 'slocum', 'seaglider']
    }
    
    def __init__(self, db: Optional[Session] = None):
        """
        初始化CNV解析器
        
        Args:
            db: 数据库会话，用于CF标准名称查询
        """
        self.header_info = {}
        self.variables_info = []
        self.data_start_line = 0
        self.bad_flag = -9.990e-29
        self.encoding = 'utf-8'
        
        # 初始化CF变量识别引擎
        self.cf_identifier = CFVariableIdentifier(db=db)
        # 初始化全局属性生成器
        self.global_attr_generator = GlobalAttributeGenerator()
        
    def parse_file(self, file_path: str, temp_id: str) -> Dict[str, Any]:
        """
        完整解析CNV文件
        
        Args:
            file_path: CNV文件路径
            temp_id: 临时文件ID
            
        Returns:
            完整的解析结果
        """
        try:
            logger.info(f"开始解析CNV文件: {file_path}")
            
            # 1. 读取文件内容
            with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                lines = f.readlines()
            
            # 2. 解析头部信息
            self._parse_header(lines)
            
            # 3. 解析变量定义
            self._parse_variables(lines)
            
            # 4. 解析数据部分
            data_df = self._parse_data(lines)
            
            # 5. 智能变量识别
            columns_info = self._identify_variables()
            
            # 填充缺失的列信息
            for i, col_info in enumerate(columns_info):
                col_name = col_info['name']
                if col_name in data_df.columns:
                    col_data = data_df[col_name]
                    # 示例值
                    sample_values = col_data.dropna().head(5).tolist()
                    col_info['sample_values'] = [str(v) for v in sample_values]
                    # 缺失值统计
                    col_info['missing_count'] = int(col_data.isnull().sum())
                    col_info['total_count'] = len(col_data)
            
            # 6. 提取仪器和元数据信息
            instrument_info = self._extract_instrument_info()
            
            # 7. 生成预览数据
            preview_data = data_df.head(50).fillna("").to_dict('records')
            
            # 8. 质量报告
            quality_report = self._generate_quality_report(data_df)
            
            # 9. 生成全局属性建议
            try:
                file_info = {
                    'filename': file_path.split('/')[-1] if '/' in file_path else file_path,
                    'filepath': file_path,
                    'row_count': len(data_df)
                }
                
                global_attributes = self.global_attr_generator.generate_global_attributes(
                    file_info=file_info,
                    column_info=columns_info,
                    data_preview=preview_data[:10] if preview_data else None  # 使用前10行作为预览
                )
                
                # 转换为字典格式以便JSON序列化
                global_attr_dict = {
                    'title': global_attributes.title,
                    'summary': global_attributes.summary,
                    'keywords': global_attributes.keywords,
                    'institution': global_attributes.institution,
                    'source': global_attributes.source,
                    'history': global_attributes.history,
                    'references': global_attributes.references,
                    'conventions': global_attributes.conventions,
                    'data_type': global_attributes.data_type,
                    'processing_level': global_attributes.processing_level,
                    'quality_control_level': global_attributes.quality_control_level,
                    'geospatial_lat_min': global_attributes.geospatial_lat_min,
                    'geospatial_lat_max': global_attributes.geospatial_lat_max,
                    'geospatial_lon_min': global_attributes.geospatial_lon_min,
                    'geospatial_lon_max': global_attributes.geospatial_lon_max,
                    'geospatial_vertical_min': global_attributes.geospatial_vertical_min,
                    'geospatial_vertical_max': global_attributes.geospatial_vertical_max,
                    'time_coverage_start': global_attributes.time_coverage_start,
                    'time_coverage_end': global_attributes.time_coverage_end,
                    'time_coverage_duration': global_attributes.time_coverage_duration,
                    'time_coverage_resolution': global_attributes.time_coverage_resolution,
                    'creator_name': global_attributes.creator_name,
                    'creator_email': global_attributes.creator_email,
                    'creator_institution': global_attributes.creator_institution,
                    'project': global_attributes.project,
                    'program': global_attributes.program,
                    'confidence': global_attributes.confidence,
                    'auto_generated_fields': global_attributes.auto_generated_fields or []
                }
                
            except Exception as e:
                logger.warning(f"全局属性生成失败: {e}")
                global_attr_dict = {'confidence': 0.0, 'auto_generated_fields': []}

            result = {
                "temp_id": temp_id,
                "row_count": len(data_df),
                "column_count": len(data_df.columns),
                "columns": columns_info,
                "preview_data": preview_data,
                "parsing_config": {
                    "file_format": "cnv",
                    "instrument_type": instrument_info.get("type", "ctd"),
                    "data_start_line": self.data_start_line,
                    "bad_flag": self.bad_flag
                },
                "quality_report": quality_report,
                "header_info": self.header_info,
                "instrument_info": instrument_info,
                "global_attributes": global_attr_dict
            }
            
            logger.info(f"CNV文件解析成功: {len(data_df)}行 x {len(data_df.columns)}列")
            return result
            
        except Exception as e:
            logger.error(f"CNV文件解析失败: {e}", exc_info=True)
            raise Exception(f"CNV文件解析失败: {str(e)}")
    
    def _parse_header(self, lines: List[str]) -> None:
        """解析CNV文件头部信息"""
        header_patterns = {
            'filename': r'\* NMEA Latitude = (.+)',
            'instrument': r'\* Sea-Bird (.+)',
            'temperature_sn': r'\* Temperature SN = (.+)',
            'conductivity_sn': r'\* Conductivity SN = (.+)',
            'pressure_sn': r'\* Pressure SN = (.+)',
            'voltage0': r'\* Voltage 0 = (.+)',
            'voltage1': r'\* Voltage 1 = (.+)',
            'voltage2': r'\* Voltage 2 = (.+)',
            'voltage3': r'\* Voltage 3 = (.+)',
            'datcnv_date': r'\* datcnv_date = (.+)',
            'datcnv_in': r'\* datcnv_in = (.+)',
            'datcnv_ox_hysteresis_correction': r'\* datcnv_ox_hysteresis_correction = (.+)',
            'wildedit_date': r'\* wildedit_date = (.+)',
            'celltm_date': r'\* celltm_date = (.+)',
            'filter_date': r'\* filter_date = (.+)',
            'loopedit_date': r'\* loopedit_date = (.+)',
            'derive_date': r'\* derive_date = (.+)',
            'binavg_date': r'\* binavg_date = (.+)',
            'file_type': r'\* File type = (.+)',
            'cast': r'\* cast = (.+)',
            'station': r'\* station = (.+)',
            'latitude': r'\* NMEA Latitude = (.+)',
            'longitude': r'\* NMEA Longitude = (.+)',
            'nmea_utc': r'\* NMEA UTC \(Time\) = (.+)',
            'system_upload_time': r'\* System UpLoad Time = (.+)',
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('*'):
                for key, pattern in header_patterns.items():
                    match = re.search(pattern, line, re.IGNORECASE)
                    if match:
                        self.header_info[key] = match.group(1).strip()
                        break
                
                # 处理其他元数据行
                if '=' in line and line.startswith('*'):
                    parts = line[1:].split('=', 1)
                    if len(parts) == 2:
                        key = parts[0].strip().lower().replace(' ', '_')
                        value = parts[1].strip()
                        if key not in self.header_info:
                            self.header_info[key] = value
    
    def _parse_variables(self, lines: List[str]) -> None:
        """解析变量定义"""
        name_pattern = r'# name (\d+) = (.+)'
        span_pattern = r'# span (\d+) = (.+)'
        interval_pattern = r'# interval = (.+)'
        nvalues_pattern = r'# nvalues = (.+)'
        nquan_pattern = r'# nquan = (.+)'
        bad_flag_pattern = r'# bad_flag = (.+)'
        
        variables = {}
        
        for line in lines:
            line = line.strip()
            
            # 解析变量名
            match = re.search(name_pattern, line)
            if match:
                var_index = int(match.group(1))
                var_info = match.group(2).strip()
                
                # 解析变量信息 (通常格式: varname: description [units])
                var_parts = self._parse_variable_info(var_info)
                variables[var_index] = var_parts
            
            # 解析变量范围
            match = re.search(span_pattern, line)
            if match:
                var_index = int(match.group(1))
                span_info = match.group(2).strip()
                if var_index in variables:
                    variables[var_index]['span'] = span_info
            
            # 解析其他信息
            if line.startswith('# interval'):
                match = re.search(interval_pattern, line)
                if match:
                    self.header_info['interval'] = match.group(1).strip()
            
            if line.startswith('# nvalues'):
                match = re.search(nvalues_pattern, line)
                if match:
                    self.header_info['nvalues'] = int(match.group(1).strip())
            
            if line.startswith('# nquan'):
                match = re.search(nquan_pattern, line)
                if match:
                    self.header_info['nquan'] = int(match.group(1).strip())
            
            if line.startswith('# bad_flag'):
                match = re.search(bad_flag_pattern, line)
                if match:
                    self.bad_flag = float(match.group(1).strip())
            
            # 检测数据开始行
            if line == '*END*':
                break
        
        # 将变量按索引排序
        self.variables_info = [variables.get(i, {}) for i in sorted(variables.keys())]
    
    def _parse_variable_info(self, var_info: str) -> Dict[str, Any]:
        """解析单个变量信息"""
        # 典型格式: "prDM: Pressure, Digiquartz [db]"
        # 或: "tv290C: Temperature [ITS-90, deg C]"
        
        result = {'name': '', 'description': '', 'units': '', 'sensor': ''}
        
        # 分离变量名和描述
        if ':' in var_info:
            parts = var_info.split(':', 1)
            result['name'] = parts[0].strip()
            description_part = parts[1].strip()
        else:
            description_part = var_info
            result['name'] = var_info.split()[0] if var_info.split() else 'unknown'
        
        # 提取单位 (通常在[]或()中)
        units_match = re.search(r'[\[\(]([^\]\)]+)[\]\)]', description_part)
        if units_match:
            result['units'] = units_match.group(1).strip()
            result['description'] = re.sub(r'[\[\(][^\]\)]+[\]\)]', '', description_part).strip()
        else:
            result['description'] = description_part
        
        # 提取传感器信息
        sensor_keywords = ['digiquartz', 'sbe', 'wetlabs', 'chelsea', 'biospherical']
        description_lower = result['description'].lower()
        for keyword in sensor_keywords:
            if keyword in description_lower:
                result['sensor'] = keyword
                break
        
        return result
    
    def _parse_data(self, lines: List[str]) -> pd.DataFrame:
        """解析数据部分"""
        # 找到数据开始行
        data_start_index = 0
        for i, line in enumerate(lines):
            if line.strip() == '*END*':
                data_start_index = i + 1
                break
        
        self.data_start_line = data_start_index
        
        # 提取数据行
        data_lines = []
        for line in lines[data_start_index:]:
            line = line.strip()
            if line and not line.startswith(('#', '*')):
                data_lines.append(line)
        
        if not data_lines:
            raise ValueError("未找到有效的数据行")
        
        # 解析数据 - CNV文件通常使用固定宽度或空格分隔
        data_rows = []
        for line in data_lines:
            # 按照11字符固定宽度或空格分隔
            values = []
            if len(line) % 11 == 0 and '  ' not in line:
                # 固定宽度格式 (每个值11字符)
                for i in range(0, len(line), 11):
                    value_str = line[i:i+11].strip()
                    if value_str:
                        try:
                            value = float(value_str)
                            # 处理坏数据标记
                            if abs(value - self.bad_flag) < 1e-20:
                                value = np.nan
                            values.append(value)
                        except ValueError:
                            values.append(np.nan)
            else:
                # 空格分隔格式
                parts = line.split()
                for part in parts:
                    try:
                        value = float(part)
                        # 处理坏数据标记
                        if abs(value - self.bad_flag) < 1e-20:
                            value = np.nan
                        values.append(value)
                    except ValueError:
                        values.append(np.nan)
            
            if values:
                data_rows.append(values)
        
        if not data_rows:
            raise ValueError("无法解析数据行")
        
        # 创建DataFrame
        max_cols = max(len(row) for row in data_rows)
        
        # 生成列名
        column_names = []
        for i in range(max_cols):
            if i < len(self.variables_info) and self.variables_info[i].get('name'):
                column_names.append(self.variables_info[i]['name'])
            else:
                column_names.append(f'col_{i}')
        
        # 确保所有行都有相同的列数
        normalized_rows = []
        for row in data_rows:
            normalized_row = row + [np.nan] * (max_cols - len(row))
            normalized_rows.append(normalized_row[:max_cols])
        
        df = pd.DataFrame(normalized_rows, columns=column_names)
        return df
    
    def _identify_variables(self) -> List[Dict[str, Any]]:
        """智能识别变量类型和CF标准映射"""
        columns_info = []
        
        for i, var_info in enumerate(self.variables_info):
            var_name = var_info.get('name', f'col_{i}')
            var_description = var_info.get('description', '')
            var_units = var_info.get('units', '')
            
            # 匹配CF标准变量
            cf_suggestion = self._suggest_cf_variable(var_name, var_description, var_units)
            
            column_info = {
                "name": var_name,
                "data_type": "numeric",  # CNV文件主要是数值数据
                "sample_values": [],  # 这里暂时为空，在主解析函数中填充
                "missing_count": 0,   # 这里暂时为0，在主解析函数中计算
                "total_count": 0,     # 这里暂时为0，在主解析函数中计算
                "suggested_cf_name": cf_suggestion.get('standard_name'),
                "suggested_units": cf_suggestion.get('units'),
                "confidence": cf_suggestion.get('confidence', 0.0),
                "description": var_description,
                "original_units": var_units,
                "sensor": var_info.get('sensor', ''),
                "span": var_info.get('span', '')
            }
            
            columns_info.append(column_info)
        
        return columns_info
    
    def _suggest_cf_variable(self, var_name: str, description: str, units: str) -> Dict[str, Any]:
        """基于变量名、描述和单位建议CF标准变量（使用新的CF识别引擎）"""
        try:
            # 使用新的CF变量识别引擎
            suggestion = self.cf_identifier.identify_variable(
                var_name=var_name,
                description=description,
                units=units,
                sample_values=None,  # CNV解析阶段还没有样本值
                column_index=None
            )
            
            # 转换为原有格式以保持兼容性
            return {
                'standard_name': suggestion.standard_name,
                'units': suggestion.units,
                'confidence': suggestion.confidence,
                'long_name': suggestion.long_name,
                'valid_range': suggestion.valid_range,
                'axis': suggestion.axis,
                'positive': suggestion.positive,
                'category': suggestion.category,
                'match_type': suggestion.match_type,
                'description': suggestion.description
            }
        
        except Exception as e:
            logger.warning(f"CF变量识别失败，使用备用方法: {e}")
            
            # 备用方法：使用原有的CTD映射
            var_name_lower = var_name.lower()
            description_lower = description.lower()
            
            # 直接匹配变量名
            if var_name_lower in self.CTD_VARIABLE_MAPPING:
                return self.CTD_VARIABLE_MAPPING[var_name_lower].copy()
            
            # 模糊匹配
            best_match = None
            best_confidence = 0.0
            
            for ctd_var, var_info in self.CTD_VARIABLE_MAPPING.items():
                confidence = 0.0
                
                # 检查变量名匹配
                if ctd_var in var_name_lower or var_name_lower in ctd_var:
                    confidence += 0.6
                
                # 检查描述匹配
                ctd_keywords = ctd_var.split('_')
                for keyword in ctd_keywords:
                    if keyword in description_lower:
                        confidence += 0.2
                
                # 检查单位匹配
                if var_info.get('units') and units and var_info['units'].lower() in units.lower():
                    confidence += 0.3
                
                # 应用原始置信度
                confidence *= var_info.get('confidence', 1.0)
                
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = var_info.copy()
                    best_match['confidence'] = confidence
            
            if best_match and best_confidence > 0.3:
                return best_match
            
            # 无匹配时返回默认值
            return {
                'standard_name': None,
                'units': None,
                'confidence': 0.0
            }
    
    def _extract_instrument_info(self) -> Dict[str, Any]:
        """提取仪器信息"""
        instrument_info = {
            'type': 'ctd',
            'manufacturer': 'unknown',
            'model': 'unknown',
            'serial_numbers': {},
            'calibration_info': {},
            'processing_history': []
        }
        
        # 识别仪器类型
        header_text = ' '.join(str(value) for value in self.header_info.values()).lower()
        for instrument_type, keywords in self.INSTRUMENT_PATTERNS.items():
            for keyword in keywords:
                if keyword in header_text:
                    instrument_info['type'] = instrument_type
                    break
        
        # 提取制造商和型号
        if 'instrument' in self.header_info:
            instrument_str = self.header_info['instrument']
            if 'sea-bird' in instrument_str.lower() or 'sbe' in instrument_str.lower():
                instrument_info['manufacturer'] = 'Sea-Bird Scientific'
                # 提取型号
                model_match = re.search(r'SBE[- ]?(\d+)', instrument_str, re.IGNORECASE)
                if model_match:
                    instrument_info['model'] = f"SBE {model_match.group(1)}"
        
        # 提取序列号
        sn_fields = ['temperature_sn', 'conductivity_sn', 'pressure_sn']
        for field in sn_fields:
            if field in self.header_info:
                sensor_type = field.replace('_sn', '')
                instrument_info['serial_numbers'][sensor_type] = self.header_info[field]
        
        # 提取处理历史
        processing_fields = [
            'datcnv_date', 'wildedit_date', 'celltm_date', 'filter_date', 
            'loopedit_date', 'derive_date', 'binavg_date'
        ]
        for field in processing_fields:
            if field in self.header_info:
                process_name = field.replace('_date', '')
                instrument_info['processing_history'].append({
                    'process': process_name,
                    'date': self.header_info[field]
                })
        
        return instrument_info
    
    def _generate_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """生成数据质量报告"""
        total_values = df.size
        missing_values = df.isnull().sum().sum()
        missing_percentage = (missing_values / total_values) * 100 if total_values > 0 else 0
        
        # 检测异常值
        anomalies = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                Q1 = col_data.quantile(0.25)
                Q3 = col_data.quantile(0.75)
                IQR = Q3 - Q1
                
                outliers = col_data[(col_data < Q1 - 1.5 * IQR) | (col_data > Q3 + 1.5 * IQR)]
                
                if len(outliers) > 0:
                    anomalies[col] = [f"检测到 {len(outliers)} 个可能的异常值"]
        
        quality_report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_data_percentage": float(missing_percentage),
            "data_types_detected": {
                "numeric": len(df.select_dtypes(include=[np.number]).columns),
                "datetime": 0,  # CNV文件很少有日期时间列
                "text": len(df.select_dtypes(include=['object']).columns)
            },
            "anomalies": anomalies,
            "file_format": "cnv",
            "bad_flag_value": self.bad_flag,
            "header_lines": len(self.header_info),
            "variables_defined": len(self.variables_info)
        }
        
        return quality_report


# 工厂函数
def create_cnv_parser(db: Optional[Session] = None) -> CNVParser:
    """创建CNV解析器实例"""
    return CNVParser(db)


# 便捷函数
def parse_cnv_file(file_path: str, temp_id: str) -> Dict[str, Any]:
    """解析CNV文件的便捷函数"""
    parser = create_cnv_parser()
    return parser.parse_file(file_path, temp_id) 