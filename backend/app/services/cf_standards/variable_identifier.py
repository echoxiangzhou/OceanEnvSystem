"""
CF标准变量识别引擎

建立海洋学变量的智能识别系统，提供CF标准名称和属性建议

功能：
- 常见海洋学变量映射表（温度、盐度、深度、压力等）
- 多语言支持（中英文变量名识别）  
- 模糊匹配算法（处理缩写、变体）
- CF标准属性建议（standard_name、units、long_name、valid_range）
- 坐标变量自动识别（时间、空间坐标）
- 数据类型和精度建议
- 可信度评分
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class CFVariableSuggestion:
    """CF变量建议结果"""
    standard_name: Optional[str] = None
    units: Optional[str] = None
    long_name: Optional[str] = None
    valid_range: Optional[Tuple[float, float]] = None
    axis: Optional[str] = None
    positive: Optional[str] = None
    confidence: float = 0.0
    match_type: str = "none"  # exact, partial, fuzzy, none
    category: Optional[str] = None
    description: Optional[str] = None


class CFVariableIdentifier:
    """CF标准变量识别引擎"""
    
    # 综合变量映射表 - 整合了所有现有的映射表并扩展
    COMPREHENSIVE_VARIABLE_MAPPING = {
        # 温度相关 - 整合CSV、CNV、CF_converter中的映射
        'temp': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.8, 'category': 'temperature'},
        'temperature': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.9, 'category': 'temperature'},
        'water_temp': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.85, 'category': 'temperature'},
        '温度': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.8, 'category': 'temperature'},
        'sst': {'standard_name': 'sea_surface_temperature', 'units': 'degree_C', 'confidence': 0.9, 'category': 'temperature'},
        'tv290c': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.95, 'category': 'temperature'},
        't090c': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.95, 'category': 'temperature'},
        't190c': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.95, 'category': 'temperature'},
        't': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.6, 'category': 'temperature'},  # 低置信度，因为可能是时间
        
        # 盐度相关
        'sal': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.8, 'category': 'salinity'},
        'salinity': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.9, 'category': 'salinity'},
        'salt': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.7, 'category': 'salinity'},
        '盐度': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.8, 'category': 'salinity'},
        'psu': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.85, 'category': 'salinity'},
        'sal00': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.95, 'category': 'salinity'},
        'sal11': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.95, 'category': 'salinity'},
        's': {'standard_name': 'sea_water_practical_salinity', 'units': '1', 'confidence': 0.6, 'category': 'salinity'},
        
        # 深度和压力相关
        'depth': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'Z', 'positive': 'down'},
        'dep': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.8, 'category': 'coordinate', 'axis': 'Z', 'positive': 'down'},
        '深度': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'Z', 'positive': 'down'},
        'z': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.7, 'category': 'coordinate', 'axis': 'Z', 'positive': 'down'},
        'level': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.6, 'category': 'coordinate', 'axis': 'Z'},
        'depsm': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.95, 'category': 'coordinate', 'axis': 'Z', 'positive': 'down'},
        'depfm': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'Z', 'positive': 'down'},
        
        'pressure': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.9, 'category': 'pressure'},
        'press': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.8, 'category': 'pressure'},
        'pres': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.8, 'category': 'pressure'},
        '压力': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.8, 'category': 'pressure'},
        'prdm': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.95, 'category': 'pressure'},
        'p': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.6, 'category': 'pressure'},
        
        # 坐标变量 - 经纬度
        'lat': {'standard_name': 'latitude', 'units': 'degrees_north', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'Y'},
        'latitude': {'standard_name': 'latitude', 'units': 'degrees_north', 'confidence': 0.95, 'category': 'coordinate', 'axis': 'Y'},
        '纬度': {'standard_name': 'latitude', 'units': 'degrees_north', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'Y'},
        'y': {'standard_name': 'latitude', 'units': 'degrees_north', 'confidence': 0.6, 'category': 'coordinate', 'axis': 'Y'},
        
        'lon': {'standard_name': 'longitude', 'units': 'degrees_east', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'X'},
        'longitude': {'standard_name': 'longitude', 'units': 'degrees_east', 'confidence': 0.95, 'category': 'coordinate', 'axis': 'X'},
        '经度': {'standard_name': 'longitude', 'units': 'degrees_east', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'X'},
        'x': {'standard_name': 'longitude', 'units': 'degrees_east', 'confidence': 0.6, 'category': 'coordinate', 'axis': 'X'},
        
        # 时间变量
        'time': {'standard_name': 'time', 'units': 'days since 1970-01-01 00:00:00', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'T'},
        'datetime': {'standard_name': 'time', 'units': 'days since 1970-01-01 00:00:00', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'T'},
        'date': {'standard_name': 'time', 'units': 'days since 1970-01-01 00:00:00', 'confidence': 0.8, 'category': 'coordinate', 'axis': 'T'},
        '时间': {'standard_name': 'time', 'units': 'days since 1970-01-01 00:00:00', 'confidence': 0.9, 'category': 'coordinate', 'axis': 'T'},
        
        # 电导率相关
        'c0s/m': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.95, 'category': 'conductivity'},
        'c1s/m': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.95, 'category': 'conductivity'},
        'cond': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.9, 'category': 'conductivity'},
        'conductivity': {'standard_name': 'sea_water_electrical_conductivity', 'units': 'S m-1', 'confidence': 0.9, 'category': 'conductivity'},
        
        # 溶解氧
        'sbeox0v': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.9, 'category': 'chemistry'},
        'sbeox1v': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.9, 'category': 'chemistry'},
        'oxygen': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.85, 'category': 'chemistry'},
        'do': {'standard_name': 'mole_concentration_of_dissolved_molecular_oxygen_in_sea_water', 'units': 'umol kg-1', 'confidence': 0.8, 'category': 'chemistry'},
        
        # 荧光和叶绿素
        'fleco-afl': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.8, 'category': 'biology'},
        'fluorescence': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.75, 'category': 'biology'},
        'chl': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.8, 'category': 'biology'},
        'chlorophyll': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.9, 'category': 'biology'},
        
        # 浊度
        'turbidity': {'standard_name': 'sea_water_turbidity', 'units': 'NTU', 'confidence': 0.85, 'category': 'optical'},
        'turb': {'standard_name': 'sea_water_turbidity', 'units': 'NTU', 'confidence': 0.8, 'category': 'optical'},
        
        # pH
        'ph': {'standard_name': 'sea_water_ph_reported_on_total_scale', 'units': '1', 'confidence': 0.85, 'category': 'chemistry'},
        
        # 声速
        'svave': {'standard_name': 'speed_of_sound_in_sea_water', 'units': 'm s-1', 'confidence': 0.9, 'category': 'acoustic'},
        'sound_velocity': {'standard_name': 'speed_of_sound_in_sea_water', 'units': 'm s-1', 'confidence': 0.85, 'category': 'acoustic'},
        
        # 密度
        'density': {'standard_name': 'sea_water_density', 'units': 'kg m-3', 'confidence': 0.85, 'category': 'density'},
        'sigma-t': {'standard_name': 'sea_water_sigma_t', 'units': 'kg m-3', 'confidence': 0.9, 'category': 'density'},
        'sigma-theta': {'standard_name': 'sea_water_sigma_theta', 'units': 'kg m-3', 'confidence': 0.9, 'category': 'density'},
        
        # 光学量
        'par': {'standard_name': 'downwelling_photosynthetic_photon_flux_in_sea_water', 'units': 'umol m-2 s-1', 'confidence': 0.8, 'category': 'optical'},
        'beam_transmission': {'standard_name': 'volume_beam_attenuation_coefficient_of_radiative_flux_in_sea_water', 'units': 'm-1', 'confidence': 0.8, 'category': 'optical'},
        
        # 流速
        'u': {'standard_name': 'eastward_sea_water_velocity', 'units': 'm s-1', 'confidence': 0.7, 'category': 'velocity'},
        'v': {'standard_name': 'northward_sea_water_velocity', 'units': 'm s-1', 'confidence': 0.7, 'category': 'velocity'},
        'w': {'standard_name': 'upward_sea_water_velocity', 'units': 'm s-1', 'confidence': 0.7, 'category': 'velocity'},
        
        # 海表高度
        'sla': {'standard_name': 'sea_surface_height_above_sea_level', 'units': 'm', 'confidence': 0.9, 'category': 'sea_level'},
        'ssh': {'standard_name': 'sea_surface_height', 'units': 'm', 'confidence': 0.9, 'category': 'sea_level'},
        
        # 风场
        'wind_speed': {'standard_name': 'wind_speed', 'units': 'm s-1', 'confidence': 0.9, 'category': 'meteorology'},
        'wind_direction': {'standard_name': 'wind_from_direction', 'units': 'degree', 'confidence': 0.9, 'category': 'meteorology'},
        'u_wind': {'standard_name': 'eastward_wind', 'units': 'm s-1', 'confidence': 0.8, 'category': 'meteorology'},
        'v_wind': {'standard_name': 'northward_wind', 'units': 'm s-1', 'confidence': 0.8, 'category': 'meteorology'},
    }
    
    # 变量类别的典型数值范围
    TYPICAL_RANGES = {
        'sea_water_temperature': (-2.0, 35.0),
        'sea_water_practical_salinity': (0.0, 42.0),
        'sea_water_pressure': (0.0, 11000.0),
        'depth': (0.0, 11000.0),
        'latitude': (-90.0, 90.0),
        'longitude': (-180.0, 360.0),
        'sea_water_density': (1000.0, 1050.0),
        'mass_concentration_of_chlorophyll_in_sea_water': (0.0, 100.0),
        'sea_water_ph_reported_on_total_scale': (6.0, 9.0),
        'sea_water_electrical_conductivity': (0.0, 10.0),
        'speed_of_sound_in_sea_water': (1400.0, 1600.0),
    }
    
    # 关键词模式匹配
    KEYWORD_PATTERNS = {
        'temperature': ['temp', 'temperature', '温度', 'temperatur'],
        'salinity': ['sal', 'salinity', '盐度', 'salt'],
        'pressure': ['pres', 'pressure', '压力', 'press'],
        'depth': ['depth', 'dep', '深度', 'profondeur'],
        'latitude': ['lat', 'latitude', '纬度', 'latitud'],
        'longitude': ['lon', 'longitude', '经度', 'longitud'],
        'time': ['time', 'date', '时间', 'tiempo', 'datetime'],
        'conductivity': ['cond', 'conductivity', 'electrical'],
        'oxygen': ['oxy', 'oxygen', '氧气', 'oxigen'],
        'chlorophyll': ['chl', 'chlorophyll', '叶绿素', 'fluorescence'],
        'velocity': ['vel', 'velocity', 'current', '流速'],
        'wind': ['wind', '风', 'viento'],
        'density': ['dens', 'density', '密度', 'sigma'],
    }
    
    def __init__(self, db: Optional[Session] = None):
        """
        初始化CF变量识别器
        
        Args:
            db: 数据库会话，用于查询CF标准名称库
        """
        self.db = db
    
    def identify_variable(self, 
                         var_name: str, 
                         description: str = "", 
                         units: str = "", 
                         sample_values: Optional[List[Any]] = None,
                         column_index: Optional[int] = None) -> CFVariableSuggestion:
        """
        智能识别变量类型和CF标准映射
        
        Args:
            var_name: 变量名
            description: 变量描述
            units: 变量单位
            sample_values: 示例值（用于数值范围推断）
            column_index: 列索引（用于坐标变量推断）
            
        Returns:
            CF变量建议
        """
        var_name_clean = self._clean_variable_name(var_name)
        
        # 1. 精确匹配
        exact_match = self._exact_match(var_name_clean)
        if exact_match.confidence > 0.7:
            exact_match.match_type = "exact"
            return self._enhance_suggestion(exact_match, units, sample_values, description)
        
        # 2. 部分匹配
        partial_match = self._partial_match(var_name_clean, description)
        if partial_match.confidence > 0.6:
            partial_match.match_type = "partial"
            return self._enhance_suggestion(partial_match, units, sample_values, description)
        
        # 3. 模糊匹配
        fuzzy_match = self._fuzzy_match(var_name_clean, description)
        if fuzzy_match.confidence > 0.4:
            fuzzy_match.match_type = "fuzzy"
            return self._enhance_suggestion(fuzzy_match, units, sample_values, description)
        
        # 4. 基于数值范围的推断
        range_match = self._range_based_inference(sample_values, units)
        if range_match.confidence > 0.3:
            range_match.match_type = "range_inference"
            return self._enhance_suggestion(range_match, units, sample_values, description)
        
        # 5. 坐标变量推断（基于位置）
        coord_match = self._coordinate_inference(var_name_clean, column_index, sample_values)
        if coord_match.confidence > 0.3:
            coord_match.match_type = "coordinate_inference"
            return self._enhance_suggestion(coord_match, units, sample_values, description)
        
        # 6. 数据库查询（如果可用）
        if self.db:
            db_match = self._database_search(var_name_clean, description)
            if db_match.confidence > 0.3:
                db_match.match_type = "database"
                return self._enhance_suggestion(db_match, units, sample_values, description)
        
        # 7. 返回默认建议
        return CFVariableSuggestion(
            standard_name=None,
            units=units if units else None,
            long_name=var_name.replace('_', ' ').title(),
            confidence=0.0,
            match_type="none",
            description="无法识别的变量类型"
        )
    
    def _clean_variable_name(self, var_name: str) -> str:
        """清理变量名"""
        # 转换为小写
        clean_name = var_name.lower().strip()
        
        # 移除常见的前后缀
        prefixes = ['avg_', 'mean_', 'max_', 'min_', 'std_', 'var_']
        suffixes = ['_avg', '_mean', '_max', '_min', '_std', '_var', '_qc', '_flag']
        
        for prefix in prefixes:
            if clean_name.startswith(prefix):
                clean_name = clean_name[len(prefix):]
                break
        
        for suffix in suffixes:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)]
                break
        
        return clean_name
    
    def _exact_match(self, var_name: str) -> CFVariableSuggestion:
        """精确匹配"""
        if var_name in self.COMPREHENSIVE_VARIABLE_MAPPING:
            mapping = self.COMPREHENSIVE_VARIABLE_MAPPING[var_name]
            return CFVariableSuggestion(
                standard_name=mapping['standard_name'],
                units=mapping['units'],
                confidence=mapping['confidence'],
                category=mapping.get('category'),
                axis=mapping.get('axis'),
                positive=mapping.get('positive')
            )
        
        return CFVariableSuggestion(confidence=0.0)
    
    def _partial_match(self, var_name: str, description: str) -> CFVariableSuggestion:
        """部分匹配"""
        best_match = CFVariableSuggestion(confidence=0.0)
        
        search_text = f"{var_name} {description}".lower()
        
        for mapping_name, mapping_info in self.COMPREHENSIVE_VARIABLE_MAPPING.items():
            if mapping_name in var_name or var_name in mapping_name:
                confidence = mapping_info['confidence'] * 0.8  # 部分匹配降低置信度
                
                if confidence > best_match.confidence:
                    best_match = CFVariableSuggestion(
                        standard_name=mapping_info['standard_name'],
                        units=mapping_info['units'],
                        confidence=confidence,
                        category=mapping_info.get('category'),
                        axis=mapping_info.get('axis'),
                        positive=mapping_info.get('positive')
                    )
        
        return best_match
    
    def _fuzzy_match(self, var_name: str, description: str) -> CFVariableSuggestion:
        """模糊匹配"""
        best_match = CFVariableSuggestion(confidence=0.0)
        
        search_text = f"{var_name} {description}".lower()
        
        for category, keywords in self.KEYWORD_PATTERNS.items():
            match_score = 0.0
            
            for keyword in keywords:
                if keyword in search_text:
                    match_score += 0.2
            
            if match_score > 0:
                # 根据类别找到最佳的标准名称
                category_matches = [
                    (name, info) for name, info in self.COMPREHENSIVE_VARIABLE_MAPPING.items()
                    if info.get('category') == category or category in info['standard_name']
                ]
                
                if category_matches:
                    # 选择置信度最高的匹配
                    best_category_match = max(category_matches, key=lambda x: x[1]['confidence'])
                    confidence = min(match_score, best_category_match[1]['confidence'] * 0.6)
                    
                    if confidence > best_match.confidence:
                        mapping_info = best_category_match[1]
                        best_match = CFVariableSuggestion(
                            standard_name=mapping_info['standard_name'],
                            units=mapping_info['units'],
                            confidence=confidence,
                            category=mapping_info.get('category'),
                            axis=mapping_info.get('axis'),
                            positive=mapping_info.get('positive')
                        )
        
        return best_match
    
    def _range_based_inference(self, sample_values: Optional[List[Any]], units: str) -> CFVariableSuggestion:
        """基于数值范围的推断"""
        if not sample_values:
            return CFVariableSuggestion(confidence=0.0)
        
        try:
            # 提取数值
            numeric_values = []
            for val in sample_values:
                if val is not None:
                    try:
                        numeric_values.append(float(val))
                    except (ValueError, TypeError):
                        continue
            
            if len(numeric_values) < 2:
                return CFVariableSuggestion(confidence=0.0)
            
            value_min = min(numeric_values)
            value_max = max(numeric_values)
            value_range = (value_min, value_max)
            
            # 检查与典型范围的匹配
            for standard_name, typical_range in self.TYPICAL_RANGES.items():
                range_overlap = self._calculate_range_overlap(value_range, typical_range)
                
                if range_overlap > 0.5:  # 50%重叠
                    # 查找对应的变量映射
                    for var_name, var_info in self.COMPREHENSIVE_VARIABLE_MAPPING.items():
                        if var_info['standard_name'] == standard_name:
                            confidence = range_overlap * 0.6  # 基于范围的推断置信度较低
                            
                            return CFVariableSuggestion(
                                standard_name=standard_name,
                                units=var_info['units'],
                                confidence=confidence,
                                category=var_info.get('category'),
                                valid_range=typical_range
                            )
        
        except Exception as e:
            logger.warning(f"范围推断失败: {e}")
        
        return CFVariableSuggestion(confidence=0.0)
    
    def _coordinate_inference(self, var_name: str, column_index: Optional[int], 
                            sample_values: Optional[List[Any]]) -> CFVariableSuggestion:
        """坐标变量推断"""
        # 基于列位置的推断（通常经度、纬度在前几列）
        if column_index is not None and column_index < 4:
            if sample_values:
                try:
                    numeric_values = [float(val) for val in sample_values 
                                    if val is not None and str(val).replace('.', '').replace('-', '').isdigit()]
                    
                    if numeric_values:
                        value_min = min(numeric_values)
                        value_max = max(numeric_values)
                        
                        # 纬度推断
                        if -90 <= value_min and value_max <= 90:
                            return CFVariableSuggestion(
                                standard_name='latitude',
                                units='degrees_north',
                                confidence=0.4,
                                category='coordinate',
                                axis='Y'
                            )
                        
                        # 经度推断
                        if -180 <= value_min and value_max <= 360:
                            return CFVariableSuggestion(
                                standard_name='longitude',
                                units='degrees_east',
                                confidence=0.4,
                                category='coordinate',
                                axis='X'
                            )
                except (ValueError, TypeError):
                    pass
        
        return CFVariableSuggestion(confidence=0.0)
    
    def _database_search(self, var_name: str, description: str) -> CFVariableSuggestion:
        """数据库搜索（如果数据库可用）"""
        if not self.db:
            return CFVariableSuggestion(confidence=0.0)
        
        try:
            from app.db.models import CFStandardName
            
            # 搜索标准名称、别名和描述
            query_text = f"{var_name} {description}".lower()
            
            cf_names = self.db.query(CFStandardName).filter(
                CFStandardName.standard_name.contains(var_name.lower()) |
                CFStandardName.aliases.contains([var_name.lower()]) |
                CFStandardName.description.contains(var_name.lower())
            ).order_by(CFStandardName.usage_count.desc()).limit(5).all()
            
            if cf_names:
                best_match = cf_names[0]
                confidence = 0.5  # 数据库匹配的基础置信度
                
                # 根据匹配质量调整置信度
                if var_name.lower() in best_match.standard_name.lower():
                    confidence += 0.2
                if best_match.aliases and var_name.lower() in [alias.lower() for alias in best_match.aliases]:
                    confidence += 0.3
                
                return CFVariableSuggestion(
                    standard_name=best_match.standard_name,
                    units=best_match.canonical_units,
                    confidence=min(confidence, 0.9),
                    description=best_match.description
                )
        
        except Exception as e:
            logger.warning(f"数据库搜索失败: {e}")
        
        return CFVariableSuggestion(confidence=0.0)
    
    def _enhance_suggestion(self, suggestion: CFVariableSuggestion, 
                          units: str, sample_values: Optional[List[Any]], 
                          description: str) -> CFVariableSuggestion:
        """增强建议信息"""
        # 单位验证和调整
        if units and suggestion.units:
            if self._units_compatible(units, suggestion.units):
                suggestion.confidence += 0.1
            else:
                suggestion.confidence *= 0.8  # 单位不匹配降低置信度
        
        # 添加long_name
        if not suggestion.long_name and suggestion.standard_name:
            suggestion.long_name = self._generate_long_name(suggestion.standard_name)
        
        # 添加valid_range
        if suggestion.standard_name in self.TYPICAL_RANGES:
            suggestion.valid_range = self.TYPICAL_RANGES[suggestion.standard_name]
        
        # 根据sample_values调整valid_range
        if sample_values and suggestion.valid_range:
            try:
                numeric_values = [float(val) for val in sample_values 
                                if val is not None and str(val).replace('.', '').replace('-', '').isdigit()]
                if numeric_values:
                    actual_min, actual_max = min(numeric_values), max(numeric_values)
                    typical_min, typical_max = suggestion.valid_range
                    
                    # 如果实际范围在典型范围内，提高置信度
                    if typical_min <= actual_min and actual_max <= typical_max:
                        suggestion.confidence += 0.1
            except:
                pass
        
        # 限制置信度最大值
        suggestion.confidence = min(suggestion.confidence, 0.99)
        
        return suggestion
    
    def _calculate_range_overlap(self, range1: Tuple[float, float], 
                               range2: Tuple[float, float]) -> float:
        """计算两个范围的重叠度"""
        min1, max1 = range1
        min2, max2 = range2
        
        # 计算重叠区间
        overlap_min = max(min1, min2)
        overlap_max = min(max1, max2)
        
        if overlap_min >= overlap_max:
            return 0.0
        
        overlap_length = overlap_max - overlap_min
        range1_length = max1 - min1
        
        if range1_length == 0:
            return 0.0
        
        return overlap_length / range1_length
    
    def _units_compatible(self, units1: str, units2: str) -> bool:
        """检查单位兼容性"""
        if not units1 or not units2:
            return False
        
        # 简单的单位兼容性检查
        units1_clean = units1.lower().strip()
        units2_clean = units2.lower().strip()
        
        # 完全匹配
        if units1_clean == units2_clean:
            return True
        
        # 常见的等价单位
        equivalent_units = [
            ['degree_c', 'deg_c', 'celsius', '°c'],
            ['degrees_north', 'degree_north', 'deg_n'],
            ['degrees_east', 'degree_east', 'deg_e'],
            ['m s-1', 'm/s', 'meter per second'],
            ['kg m-3', 'kg/m3', 'kg per cubic meter'],
            ['dbar', 'decibar'],
            ['psu', '1', 'dimensionless'],
        ]
        
        for equiv_group in equivalent_units:
            if units1_clean in equiv_group and units2_clean in equiv_group:
                return True
        
        return False
    
    def _generate_long_name(self, standard_name: str) -> str:
        """生成long_name"""
        # 将下划线替换为空格，并转换为标题格式
        long_name = standard_name.replace('_', ' ').title()
        
        # 特殊处理
        replacements = {
            'Ph': 'pH',
            'Sea Water': 'Sea water',
            'Molecular Oxygen': 'molecular oxygen',
        }
        
        for old, new in replacements.items():
            long_name = long_name.replace(old, new)
        
        return long_name
    
    def get_supported_categories(self) -> List[str]:
        """获取支持的变量类别"""
        categories = set()
        for var_info in self.COMPREHENSIVE_VARIABLE_MAPPING.values():
            if var_info.get('category'):
                categories.add(var_info['category'])
        return sorted(list(categories))
    
    def get_variables_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据类别获取变量列表"""
        variables = []
        for var_name, var_info in self.COMPREHENSIVE_VARIABLE_MAPPING.items():
            if var_info.get('category') == category:
                variables.append({
                    'name': var_name,
                    'standard_name': var_info['standard_name'],
                    'units': var_info['units'],
                    'confidence': var_info['confidence']
                })
        
        return sorted(variables, key=lambda x: x['confidence'], reverse=True)
    
    def batch_identify(self, variables: List[Dict[str, Any]]) -> List[CFVariableSuggestion]:
        """批量识别变量"""
        results = []
        
        for i, var_info in enumerate(variables):
            var_name = var_info.get('name', '')
            description = var_info.get('description', '')
            units = var_info.get('units', '')
            sample_values = var_info.get('sample_values', [])
            
            suggestion = self.identify_variable(
                var_name=var_name,
                description=description,
                units=units,
                sample_values=sample_values,
                column_index=i
            )
            
            results.append(suggestion)
        
        return results 