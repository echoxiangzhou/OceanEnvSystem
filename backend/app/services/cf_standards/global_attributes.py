"""
CF标准全局属性智能生成器

实现功能：
- 基于文件名生成title建议
- 根据数据特征推断数据类型（观测、预报、再分析）
- 自动计算时空覆盖范围
- 生成summary描述模板
- 机构和项目信息管理
- 质量控制属性生成
- 参考文献建议
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class GlobalAttributeSuggestion:
    """全局属性建议结果"""
    title: Optional[str] = None
    summary: Optional[str] = None
    keywords: Optional[str] = None
    institution: Optional[str] = None
    source: Optional[str] = None
    history: Optional[str] = None
    references: Optional[str] = None
    comment: Optional[str] = None
    
    # CF必需属性
    conventions: str = "CF-1.8"
    
    # 空间覆盖
    geospatial_lat_min: Optional[float] = None
    geospatial_lat_max: Optional[float] = None
    geospatial_lon_min: Optional[float] = None
    geospatial_lon_max: Optional[float] = None
    geospatial_vertical_min: Optional[float] = None
    geospatial_vertical_max: Optional[float] = None
    
    # 时间覆盖
    time_coverage_start: Optional[str] = None
    time_coverage_end: Optional[str] = None
    time_coverage_duration: Optional[str] = None
    time_coverage_resolution: Optional[str] = None
    
    # 创建信息
    creator_name: Optional[str] = None
    creator_email: Optional[str] = None
    creator_institution: Optional[str] = None
    
    # 项目信息
    project: Optional[str] = None
    program: Optional[str] = None
    
    # 数据类型和质量
    data_type: Optional[str] = None
    processing_level: Optional[str] = None
    quality_control_level: Optional[str] = None
    
    # 置信度和匹配信息
    confidence: float = 0.0
    auto_generated_fields: List[str] = None


class GlobalAttributeGenerator:
    """CF标准全局属性智能生成器"""
    
    # 常见海洋研究机构数据库
    INSTITUTIONS = {
        # 中国机构
        'sio': {
            'name': 'Second Institute of Oceanography, MNR',
            'full_name': 'Second Institute of Oceanography, Ministry of Natural Resources',
            'keywords': ['sio', '海洋二所', '自然资源部第二海洋研究所'],
            'country': 'China'
        },
        'fio': {
            'name': 'First Institute of Oceanography, MNR', 
            'full_name': 'First Institute of Oceanography, Ministry of Natural Resources',
            'keywords': ['fio', '海洋一所', '自然资源部第一海洋研究所'],
            'country': 'China'
        },
        'tio': {
            'name': 'Third Institute of Oceanography, MNR',
            'full_name': 'Third Institute of Oceanography, Ministry of Natural Resources', 
            'keywords': ['tio', '海洋三所', '自然资源部第三海洋研究所'],
            'country': 'China'
        },
        'iocas': {
            'name': 'Institute of Oceanology, Chinese Academy of Sciences',
            'full_name': 'Institute of Oceanology, Chinese Academy of Sciences',
            'keywords': ['iocas', '海洋所', '中科院海洋所'],
            'country': 'China'
        },
        'ouc': {
            'name': 'Ocean University of China',
            'full_name': 'Ocean University of China',
            'keywords': ['ouc', '中国海洋大学', 'ocean university'],
            'country': 'China'
        },
        
        # 国际机构
        'noaa': {
            'name': 'National Oceanic and Atmospheric Administration',
            'full_name': 'National Oceanic and Atmospheric Administration',
            'keywords': ['noaa', 'national oceanic'],
            'country': 'United States'
        },
        'nasa': {
            'name': 'National Aeronautics and Space Administration',
            'full_name': 'National Aeronautics and Space Administration',
            'keywords': ['nasa', 'goddard', 'jpl'],
            'country': 'United States'
        },
        'whoi': {
            'name': 'Woods Hole Oceanographic Institution',
            'full_name': 'Woods Hole Oceanographic Institution',
            'keywords': ['whoi', 'woods hole'],
            'country': 'United States'
        },
        'scripps': {
            'name': 'Scripps Institution of Oceanography',
            'full_name': 'Scripps Institution of Oceanography, UC San Diego',
            'keywords': ['scripps', 'sio', 'ucsd'],
            'country': 'United States'
        },
        'cmems': {
            'name': 'Copernicus Marine Environment Monitoring Service',
            'full_name': 'Copernicus Marine Environment Monitoring Service',
            'keywords': ['cmems', 'copernicus', 'mercator'],
            'country': 'Europe'
        }
    }
    
    # 数据类型分类规则
    DATA_TYPE_PATTERNS = {
        'observation': {
            'keywords': ['ctd', 'adcp', 'buoy', 'mooring', 'cruise', 'station', 'profile', 'survey'],
            'variables': ['temperature', 'salinity', 'pressure', 'depth'],
            'description': 'In-situ oceanographic observations'
        },
        'satellite': {
            'keywords': ['satellite', 'modis', 'viirs', 'avhrr', 'sst', 'chlorophyll', 'altimetry'],
            'variables': ['sea_surface_temperature', 'chlorophyll', 'sea_surface_height'],
            'description': 'Satellite remote sensing data'
        },
        'model': {
            'keywords': ['model', 'forecast', 'hindcast', 'simulation', 'roms', 'mom', 'nemo'],
            'variables': ['eastward_velocity', 'northward_velocity'],
            'description': 'Numerical model output'
        },
        'reanalysis': {
            'keywords': ['reanalysis', 'assimilation', 'analysis', 'era5', 'glorys'],
            'variables': ['sea_water_temperature', 'sea_water_salinity'],
            'description': 'Ocean reanalysis data'
        },
        'climatology': {
            'keywords': ['climatology', 'climate', 'monthly', 'seasonal', 'annual', 'woa'],
            'variables': ['sea_water_temperature', 'sea_water_salinity'],
            'description': 'Climatological data'
        }
    }
    
    # 项目和计划映射
    PROJECTS = {
        'argo': {
            'name': 'Argo',
            'description': 'Array for Real-time Geostrophic Oceanography',
            'url': 'http://www.argo.ucsd.edu/',
            'keywords': ['argo', 'float', 'profile']
        },
        'goos': {
            'name': 'GOOS',
            'description': 'Global Ocean Observing System',
            'url': 'http://www.goosocean.org/',
            'keywords': ['goos', 'observing system']
        },
        'woce': {
            'name': 'WOCE',
            'description': 'World Ocean Circulation Experiment',
            'url': 'http://woce.nodc.noaa.gov/',
            'keywords': ['woce', 'circulation']
        },
        'clivar': {
            'name': 'CLIVAR',
            'description': 'Climate and Ocean: Variability, Predictability and Change',
            'url': 'http://www.clivar.org/',
            'keywords': ['clivar', 'climate']
        }
    }
    
    # 质量控制级别
    QC_LEVELS = {
        0: "Raw data",
        1: "Real-time data with automatic quality control",
        2: "Near real-time data with delayed mode quality control", 
        3: "Delayed mode data with full quality control",
        4: "Research quality data"
    }
    
    def __init__(self):
        """初始化全局属性生成器"""
        pass
    
    def generate_global_attributes(self, 
                                 file_info: Dict[str, Any],
                                 column_info: List[Dict[str, Any]],
                                 data_preview: Optional[List[Dict[str, Any]]] = None,
                                 custom_info: Optional[Dict[str, Any]] = None) -> GlobalAttributeSuggestion:
        """
        生成全局属性建议
        
        Args:
            file_info: 文件信息（文件名、路径、大小等）
            column_info: 列信息（变量名、CF标准名称等）
            data_preview: 数据预览（用于推断时空范围等）
            custom_info: 用户提供的自定义信息
            
        Returns:
            全局属性建议
        """
        suggestion = GlobalAttributeSuggestion()
        auto_generated = []
        
        # 1. 生成标题
        title_result = self._generate_title(file_info, column_info)
        if title_result:
            suggestion.title = title_result
            auto_generated.append('title')
        
        # 2. 推断数据类型
        data_type_result = self._infer_data_type(file_info, column_info)
        if data_type_result:
            suggestion.data_type = data_type_result['type']
            suggestion.source = data_type_result['description']
            auto_generated.extend(['data_type', 'source'])
        
        # 3. 生成摘要
        summary_result = self._generate_summary(file_info, column_info, data_type_result)
        if summary_result:
            suggestion.summary = summary_result
            auto_generated.append('summary')
        
        # 4. 生成关键词
        keywords_result = self._generate_keywords(file_info, column_info)
        if keywords_result:
            suggestion.keywords = keywords_result
            auto_generated.append('keywords')
        
        # 5. 识别机构
        institution_result = self._identify_institution(file_info, custom_info)
        if institution_result:
            suggestion.institution = institution_result['name']
            if institution_result.get('creator_name'):
                suggestion.creator_name = institution_result['creator_name']
                suggestion.creator_institution = institution_result['name']
                auto_generated.extend(['creator_name', 'creator_institution'])
            auto_generated.append('institution')
        
        # 6. 识别项目
        project_result = self._identify_project(file_info, column_info)
        if project_result:
            suggestion.project = project_result['name']
            if project_result.get('program'):
                suggestion.program = project_result['program']
                auto_generated.append('program')
            auto_generated.append('project')
        
        # 7. 计算空间覆盖范围
        spatial_coverage = self._calculate_spatial_coverage(column_info, data_preview)
        if spatial_coverage:
            suggestion.geospatial_lat_min = spatial_coverage.get('lat_min')
            suggestion.geospatial_lat_max = spatial_coverage.get('lat_max')
            suggestion.geospatial_lon_min = spatial_coverage.get('lon_min')
            suggestion.geospatial_lon_max = spatial_coverage.get('lon_max')
            suggestion.geospatial_vertical_min = spatial_coverage.get('depth_min')
            suggestion.geospatial_vertical_max = spatial_coverage.get('depth_max')
            auto_generated.extend(['geospatial_lat_min', 'geospatial_lat_max', 
                                 'geospatial_lon_min', 'geospatial_lon_max'])
            if spatial_coverage.get('depth_min') is not None:
                auto_generated.extend(['geospatial_vertical_min', 'geospatial_vertical_max'])
        
        # 8. 计算时间覆盖范围
        temporal_coverage = self._calculate_temporal_coverage(column_info, data_preview)
        if temporal_coverage:
            suggestion.time_coverage_start = temporal_coverage.get('start')
            suggestion.time_coverage_end = temporal_coverage.get('end')
            suggestion.time_coverage_duration = temporal_coverage.get('duration')
            suggestion.time_coverage_resolution = temporal_coverage.get('resolution')
            auto_generated.extend(['time_coverage_start', 'time_coverage_end'])
            if temporal_coverage.get('duration'):
                auto_generated.extend(['time_coverage_duration', 'time_coverage_resolution'])
        
        # 9. 生成处理历史
        history_result = self._generate_history(file_info)
        if history_result:
            suggestion.history = history_result
            auto_generated.append('history')
        
        # 10. 推断质量控制级别
        qc_level = self._infer_qc_level(file_info, column_info)
        if qc_level is not None:
            suggestion.quality_control_level = f"Level {qc_level}"
            suggestion.processing_level = self.QC_LEVELS.get(qc_level, "Unknown")
            auto_generated.extend(['quality_control_level', 'processing_level'])
        
        # 11. 生成参考文献建议
        references_result = self._generate_references(data_type_result, project_result)
        if references_result:
            suggestion.references = references_result
            auto_generated.append('references')
        
        # 12. 计算总体置信度
        suggestion.confidence = self._calculate_confidence(auto_generated, file_info, column_info)
        suggestion.auto_generated_fields = auto_generated
        
        return suggestion
    
    def _generate_title(self, file_info: Dict[str, Any], column_info: List[Dict[str, Any]]) -> Optional[str]:
        """基于文件名和变量信息生成标题"""
        try:
            filename = file_info.get('filename', '')
            if not filename:
                return None
            
            # 清理文件名
            base_name = filename.replace('.csv', '').replace('.cnv', '').replace('.xlsx', '')
            base_name = re.sub(r'[_-]', ' ', base_name)
            
            # 识别变量类型
            variable_types = set()
            for col in column_info:
                cf_name = col.get('suggested_cf_name', '')
                if cf_name:
                    if 'temperature' in cf_name:
                        variable_types.add('temperature')
                    elif 'salinity' in cf_name:
                        variable_types.add('salinity')
                    elif 'velocity' in cf_name:
                        variable_types.add('current')
                    elif 'chlorophyll' in cf_name:
                        variable_types.add('chlorophyll')
                    elif 'pressure' in cf_name:
                        variable_types.add('pressure')
            
            # 构建标题
            if variable_types:
                var_str = ', '.join(sorted(variable_types))
                title = f"{base_name.title()} - {var_str.title()} Data"
            else:
                title = f"{base_name.title()} - Oceanographic Data"
            
            return title
            
        except Exception as e:
            logger.warning(f"标题生成失败: {e}")
            return None
    
    def _infer_data_type(self, file_info: Dict[str, Any], column_info: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """推断数据类型"""
        try:
            filename = file_info.get('filename', '').lower()
            
            # 提取所有变量的CF标准名称
            cf_names = [col.get('suggested_cf_name', '').lower() for col in column_info if col.get('suggested_cf_name')]
            all_text = f"{filename} {' '.join(cf_names)}"
            
            best_match = None
            best_score = 0
            
            for data_type, patterns in self.DATA_TYPE_PATTERNS.items():
                score = 0
                
                # 检查关键词匹配
                for keyword in patterns['keywords']:
                    if keyword in all_text:
                        score += 2
                
                # 检查变量匹配
                for var_pattern in patterns['variables']:
                    for cf_name in cf_names:
                        if var_pattern in cf_name:
                            score += 1
                
                if score > best_score:
                    best_score = score
                    best_match = {
                        'type': data_type,
                        'description': patterns['description'],
                        'score': score
                    }
            
            return best_match if best_score > 0 else None
            
        except Exception as e:
            logger.warning(f"数据类型推断失败: {e}")
            return None
    
    def _generate_summary(self, file_info: Dict[str, Any], column_info: List[Dict[str, Any]], 
                         data_type_info: Optional[Dict[str, str]]) -> Optional[str]:
        """生成数据集摘要"""
        try:
            # 基本信息
            num_vars = len(column_info)
            num_rows = file_info.get('row_count', 0)
            
            # 变量类型统计
            var_categories = {}
            for col in column_info:
                cf_name = col.get('suggested_cf_name', '')
                if 'temperature' in cf_name:
                    var_categories['temperature'] = var_categories.get('temperature', 0) + 1
                elif 'salinity' in cf_name:
                    var_categories['salinity'] = var_categories.get('salinity', 0) + 1
                elif 'velocity' in cf_name or 'current' in cf_name:
                    var_categories['velocity'] = var_categories.get('velocity', 0) + 1
                elif 'chlorophyll' in cf_name:
                    var_categories['chlorophyll'] = var_categories.get('chlorophyll', 0) + 1
            
            # 构建摘要
            data_type_desc = data_type_info.get('description', 'oceanographic data') if data_type_info else 'oceanographic data'
            
            summary_parts = [
                f"This dataset contains {data_type_desc}",
                f"with {num_vars} variables and {num_rows} data records."
            ]
            
            if var_categories:
                var_list = []
                for var_type, count in var_categories.items():
                    if count > 1:
                        var_list.append(f"{count} {var_type} variables")
                    else:
                        var_list.append(f"{var_type}")
                
                if var_list:
                    summary_parts.append(f"The dataset includes {', '.join(var_list)}.")
            
            return ' '.join(summary_parts)
            
        except Exception as e:
            logger.warning(f"摘要生成失败: {e}")
            return None
    
    def _generate_keywords(self, file_info: Dict[str, Any], column_info: List[Dict[str, Any]]) -> Optional[str]:
        """生成关键词"""
        try:
            keywords = set()
            
            # 基于变量添加关键词
            for col in column_info:
                cf_name = col.get('suggested_cf_name', '')
                if 'temperature' in cf_name:
                    keywords.update(['ocean temperature', 'sea water temperature'])
                elif 'salinity' in cf_name:
                    keywords.update(['ocean salinity', 'sea water salinity'])
                elif 'velocity' in cf_name or 'current' in cf_name:
                    keywords.update(['ocean currents', 'water velocity'])
                elif 'chlorophyll' in cf_name:
                    keywords.update(['chlorophyll', 'ocean color', 'phytoplankton'])
                elif 'pressure' in cf_name:
                    keywords.update(['sea water pressure'])
                elif 'depth' in cf_name:
                    keywords.update(['water depth', 'bathymetry'])
            
            # 添加通用海洋学关键词
            keywords.update(['oceanography', 'marine science', 'ocean data'])
            
            # 基于文件名添加关键词
            filename = file_info.get('filename', '').lower()
            if 'ctd' in filename:
                keywords.add('CTD')
            if 'adcp' in filename:
                keywords.add('ADCP')
            if 'cruise' in filename:
                keywords.add('research cruise')
            
            return ', '.join(sorted(list(keywords)))
            
        except Exception as e:
            logger.warning(f"关键词生成失败: {e}")
            return None
    
    def _identify_institution(self, file_info: Dict[str, Any], 
                            custom_info: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """识别机构信息"""
        try:
            # 首先检查用户提供的信息
            if custom_info and custom_info.get('institution'):
                return {'name': custom_info['institution']}
            
            # 基于文件路径或名称推断
            filepath = file_info.get('filepath', '').lower()
            filename = file_info.get('filename', '').lower()
            search_text = f"{filepath} {filename}"
            
            for inst_key, inst_info in self.INSTITUTIONS.items():
                for keyword in inst_info['keywords']:
                    if keyword.lower() in search_text:
                        return {
                            'name': inst_info['name'],
                            'full_name': inst_info['full_name'],
                            'country': inst_info['country']
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"机构识别失败: {e}")
            return None
    
    def _identify_project(self, file_info: Dict[str, Any], column_info: List[Dict[str, Any]]) -> Optional[Dict[str, str]]:
        """识别项目信息"""
        try:
            filepath = file_info.get('filepath', '').lower()
            filename = file_info.get('filename', '').lower()
            search_text = f"{filepath} {filename}"
            
            for proj_key, proj_info in self.PROJECTS.items():
                for keyword in proj_info['keywords']:
                    if keyword.lower() in search_text:
                        return {
                            'name': proj_info['name'],
                            'description': proj_info['description'],
                            'url': proj_info['url'],
                            'program': proj_info.get('program')
                        }
            
            return None
            
        except Exception as e:
            logger.warning(f"项目识别失败: {e}")
            return None
    
    def _calculate_spatial_coverage(self, column_info: List[Dict[str, Any]], 
                                  data_preview: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, float]]:
        """计算空间覆盖范围"""
        try:
            if not data_preview:
                return None
            
            # 查找坐标变量
            lat_col = None
            lon_col = None
            depth_col = None
            
            for col in column_info:
                cf_name = col.get('suggested_cf_name', '')
                col_name = col.get('name', '')
                
                if cf_name == 'latitude':
                    lat_col = col_name
                elif cf_name == 'longitude':
                    lon_col = col_name
                elif cf_name in ['depth', 'sea_water_pressure']:
                    depth_col = col_name
            
            coverage = {}
            
            # 提取纬度范围
            if lat_col:
                lat_values = []
                for row in data_preview:
                    val = row.get(lat_col)
                    if val is not None and val != '':
                        try:
                            lat_values.append(float(val))
                        except (ValueError, TypeError):
                            continue
                
                if lat_values:
                    coverage['lat_min'] = round(min(lat_values), 6)
                    coverage['lat_max'] = round(max(lat_values), 6)
            
            # 提取经度范围
            if lon_col:
                lon_values = []
                for row in data_preview:
                    val = row.get(lon_col)
                    if val is not None and val != '':
                        try:
                            lon_values.append(float(val))
                        except (ValueError, TypeError):
                            continue
                
                if lon_values:
                    coverage['lon_min'] = round(min(lon_values), 6)
                    coverage['lon_max'] = round(max(lon_values), 6)
            
            # 提取深度范围
            if depth_col:
                depth_values = []
                for row in data_preview:
                    val = row.get(depth_col)
                    if val is not None and val != '':
                        try:
                            depth_values.append(float(val))
                        except (ValueError, TypeError):
                            continue
                
                if depth_values:
                    coverage['depth_min'] = round(min(depth_values), 2)
                    coverage['depth_max'] = round(max(depth_values), 2)
            
            return coverage if coverage else None
            
        except Exception as e:
            logger.warning(f"空间覆盖范围计算失败: {e}")
            return None
    
    def _calculate_temporal_coverage(self, column_info: List[Dict[str, Any]], 
                                   data_preview: Optional[List[Dict[str, Any]]]) -> Optional[Dict[str, str]]:
        """计算时间覆盖范围"""
        try:
            if not data_preview:
                return None
            
            # 查找时间变量
            time_col = None
            for col in column_info:
                cf_name = col.get('suggested_cf_name', '')
                if cf_name == 'time' or col.get('data_type') == 'datetime':
                    time_col = col.get('name')
                    break
            
            if not time_col:
                return None
            
            # 提取时间值
            time_values = []
            for row in data_preview:
                val = row.get(time_col)
                if val is not None and val != '':
                    try:
                        # 尝试解析时间
                        if isinstance(val, str):
                            time_obj = pd.to_datetime(val)
                            time_values.append(time_obj)
                    except:
                        continue
            
            if not time_values:
                return None
            
            coverage = {}
            time_min = min(time_values)
            time_max = max(time_values)
            
            coverage['start'] = time_min.strftime('%Y-%m-%dT%H:%M:%SZ')
            coverage['end'] = time_max.strftime('%Y-%m-%dT%H:%M:%SZ')
            
            # 计算持续时间
            duration = time_max - time_min
            coverage['duration'] = f"P{duration.days}D"
            
            # 估算时间分辨率
            if len(time_values) > 1:
                time_diffs = [(time_values[i] - time_values[i-1]).total_seconds() 
                             for i in range(1, min(10, len(time_values)))]
                avg_diff = np.mean(time_diffs)
                
                if avg_diff < 3600:  # < 1小时
                    coverage['resolution'] = f"PT{int(avg_diff)}S"
                elif avg_diff < 86400:  # < 1天
                    coverage['resolution'] = f"PT{int(avg_diff/3600)}H"
                else:  # >= 1天
                    coverage['resolution'] = f"P{int(avg_diff/86400)}D"
            
            return coverage
            
        except Exception as e:
            logger.warning(f"时间覆盖范围计算失败: {e}")
            return None
    
    def _generate_history(self, file_info: Dict[str, Any]) -> Optional[str]:
        """生成处理历史"""
        try:
            now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            filename = file_info.get('filename', 'unknown_file')
            
            history = f"{now}: File {filename} processed by Ocean Environment Data System"
            return history
            
        except Exception as e:
            logger.warning(f"处理历史生成失败: {e}")
            return None
    
    def _infer_qc_level(self, file_info: Dict[str, Any], column_info: List[Dict[str, Any]]) -> Optional[int]:
        """推断质量控制级别"""
        try:
            filename = file_info.get('filename', '').lower()
            
            # 基于文件名推断QC级别
            if any(keyword in filename for keyword in ['raw', 'level0', 'l0']):
                return 0
            elif any(keyword in filename for keyword in ['rt', 'realtime', 'level1', 'l1']):
                return 1
            elif any(keyword in filename for keyword in ['nrt', 'near_realtime', 'level2', 'l2']):
                return 2
            elif any(keyword in filename for keyword in ['delayed', 'dm', 'level3', 'l3']):
                return 3
            elif any(keyword in filename for keyword in ['research', 'final', 'level4', 'l4']):
                return 4
            
            # 基于变量完整性推断（如果有完整的温盐深等，可能是较高级别）
            cf_names = [col.get('suggested_cf_name', '') for col in column_info]
            
            if ('sea_water_temperature' in cf_names and 
                'sea_water_practical_salinity' in cf_names and 
                'depth' in cf_names):
                return 2  # 较完整的数据集，可能是近实时或延迟模式
            
            return 1  # 默认实时数据级别
            
        except Exception as e:
            logger.warning(f"QC级别推断失败: {e}")
            return None
    
    def _generate_references(self, data_type_info: Optional[Dict[str, str]], 
                           project_info: Optional[Dict[str, str]]) -> Optional[str]:
        """生成参考文献建议"""
        try:
            references = []
            
            # 基于项目添加参考文献
            if project_info:
                project_name = project_info.get('name', '')
                if project_name == 'Argo':
                    references.append("Argo (2020). Argo float data and metadata from Global Data Assembly Centre (Argo GDAC). SEANOE. https://doi.org/10.17882/42182")
                elif project_name == 'WOCE':
                    references.append("WOCE Data Products Committee (2002). WOCE Global Data, Version 3.0. WOCE International Project Office, WOCE Report No. 180/02.")
            
            # 基于数据类型添加通用参考文献
            if data_type_info:
                data_type = data_type_info.get('type', '')
                if data_type == 'satellite':
                    references.append("Remote sensing data processing guidelines and best practices documentation.")
                elif data_type == 'model':
                    references.append("Model configuration and validation documentation.")
            
            return '; '.join(references) if references else None
            
        except Exception as e:
            logger.warning(f"参考文献生成失败: {e}")
            return None
    
    def _calculate_confidence(self, auto_generated_fields: List[str], 
                            file_info: Dict[str, Any], 
                            column_info: List[Dict[str, Any]]) -> float:
        """计算总体置信度"""
        try:
            total_fields = 20  # 总共可生成的字段数
            generated_count = len(auto_generated_fields)
            
            # 基础置信度
            base_confidence = generated_count / total_fields
            
            # 根据数据质量调整
            quality_bonus = 0.0
            
            # 如果有CF标准变量识别
            cf_identified = sum(1 for col in column_info if col.get('suggested_cf_name'))
            if cf_identified > 0:
                quality_bonus += 0.1 * (cf_identified / len(column_info))
            
            # 如果有坐标变量
            has_coords = any(col.get('suggested_cf_name') in ['latitude', 'longitude', 'time'] 
                           for col in column_info)
            if has_coords:
                quality_bonus += 0.1
            
            total_confidence = min(base_confidence + quality_bonus, 0.95)
            return round(total_confidence, 2)
            
        except Exception as e:
            logger.warning(f"置信度计算失败: {e}")
            return 0.0


# 工厂函数
def create_global_attribute_generator() -> GlobalAttributeGenerator:
    """创建全局属性生成器实例"""
    return GlobalAttributeGenerator()


# 便捷函数
def generate_global_attributes(file_info: Dict[str, Any],
                             column_info: List[Dict[str, Any]],
                             data_preview: Optional[List[Dict[str, Any]]] = None,
                             custom_info: Optional[Dict[str, Any]] = None) -> GlobalAttributeSuggestion:
    """生成全局属性的便捷函数"""
    generator = create_global_attribute_generator()
    return generator.generate_global_attributes(file_info, column_info, data_preview, custom_info) 