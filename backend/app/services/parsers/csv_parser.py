"""
CSV文件智能解析器

实现功能：
- 自动编码检测（UTF-8、GBK、ISO-8859-1等）
- 智能分隔符识别（逗号、分号、制表符等）
- 自动头部行数判断
- 数据类型推断
- 缺失值和异常值检测
- 海洋学变量智能识别
"""

import pandas as pd
import numpy as np
import chardet
import io
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVParser:
    """CSV文件智能解析器"""
    
    # 支持的编码列表（按优先级排序）
    ENCODINGS = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'iso-8859-1', 'windows-1252']
    
    # 支持的分隔符列表
    SEPARATORS = [',', ';', '\t', '|', ' ']
    
    # 海洋学变量映射表
    OCEANOGRAPHIC_VARIABLES = {
        # 温度相关
        'temp': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.8},
        'temperature': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.9},
        'water_temp': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.85},
        '温度': {'standard_name': 'sea_water_temperature', 'units': 'degree_C', 'confidence': 0.8},
        'sst': {'standard_name': 'sea_surface_temperature', 'units': 'degree_C', 'confidence': 0.9},
        
        # 盐度相关
        'sal': {'standard_name': 'sea_water_salinity', 'units': '1', 'confidence': 0.8},
        'salinity': {'standard_name': 'sea_water_salinity', 'units': '1', 'confidence': 0.9},
        'salt': {'standard_name': 'sea_water_salinity', 'units': '1', 'confidence': 0.7},
        '盐度': {'standard_name': 'sea_water_salinity', 'units': '1', 'confidence': 0.8},
        'psu': {'standard_name': 'sea_water_salinity', 'units': '1', 'confidence': 0.85},
        
        # 深度相关
        'depth': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.9},
        'dep': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.8},
        '深度': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.9},
        'z': {'standard_name': 'depth', 'units': 'm', 'confidence': 0.7},
        
        # 压力相关
        'pressure': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.9},
        'press': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.8},
        'pres': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.8},
        '压力': {'standard_name': 'sea_water_pressure', 'units': 'dbar', 'confidence': 0.8},
        
        # 坐标变量
        'lat': {'standard_name': 'latitude', 'units': 'degrees_north', 'confidence': 0.9},
        'latitude': {'standard_name': 'latitude', 'units': 'degrees_north', 'confidence': 0.95},
        '纬度': {'standard_name': 'latitude', 'units': 'degrees_north', 'confidence': 0.9},
        'lon': {'standard_name': 'longitude', 'units': 'degrees_east', 'confidence': 0.9},
        'longitude': {'standard_name': 'longitude', 'units': 'degrees_east', 'confidence': 0.95},
        '经度': {'standard_name': 'longitude', 'units': 'degrees_east', 'confidence': 0.9},
        
        # 时间变量
        'time': {'standard_name': 'time', 'units': None, 'confidence': 0.9},
        'datetime': {'standard_name': 'time', 'units': None, 'confidence': 0.9},
        'date': {'standard_name': 'time', 'units': None, 'confidence': 0.8},
        '时间': {'standard_name': 'time', 'units': None, 'confidence': 0.9},
        
        # 其他海洋学变量
        'sla': {'standard_name': 'sea_surface_height_above_sea_level', 'units': 'm', 'confidence': 0.9},
        'ssh': {'standard_name': 'sea_surface_height', 'units': 'm', 'confidence': 0.9},
        'u': {'standard_name': 'eastward_sea_water_velocity', 'units': 'm s-1', 'confidence': 0.7},
        'v': {'standard_name': 'northward_sea_water_velocity', 'units': 'm s-1', 'confidence': 0.7},
        'chl': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.8},
        'chlorophyll': {'standard_name': 'mass_concentration_of_chlorophyll_in_sea_water', 'units': 'mg m-3', 'confidence': 0.9},
    }
    
    def __init__(self):
        self.encoding_cache = {}
    
    def detect_encoding(self, file_path: str, sample_size: int = 8192) -> str:
        """
        智能检测文件编码
        
        Args:
            file_path: 文件路径
            sample_size: 检测样本大小
            
        Returns:
            编码格式字符串
        """
        if file_path in self.encoding_cache:
            return self.encoding_cache[file_path]
            
        try:
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
                
            # 使用chardet检测编码
            result = chardet.detect(raw_data)
            detected_encoding = result.get('encoding', 'utf-8').lower()
            confidence = result.get('confidence', 0.0)
            
            logger.info(f"检测到编码: {detected_encoding}, 置信度: {confidence:.2f}")
            
            # 如果置信度太低，尝试常见编码
            if confidence < 0.7:
                for encoding in self.ENCODINGS:
                    try:
                        raw_data.decode(encoding)
                        detected_encoding = encoding
                        logger.info(f"回退到编码: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                        
            # 缓存结果
            self.encoding_cache[file_path] = detected_encoding
            return detected_encoding
            
        except Exception as e:
            logger.warning(f"编码检测失败: {e}, 使用默认UTF-8")
            return 'utf-8'
    
    def detect_separator(self, file_path: str, encoding: str, sample_lines: int = 10) -> str:
        """
        智能检测分隔符
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            sample_lines: 分析的样本行数
            
        Returns:
            最佳分隔符
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                sample_data = []
                for i, line in enumerate(f):
                    if i >= sample_lines:
                        break
                    sample_data.append(line.strip())
                    
            separator_scores = {}
            
            for sep in self.SEPARATORS:
                scores = []
                for line in sample_data:
                    if line:  # 跳过空行
                        parts = line.split(sep)
                        scores.append(len(parts))
                
                if scores:
                    # 计算分隔符得分：一致性和列数
                    avg_cols = np.mean(scores)
                    consistency = 1.0 - (np.std(scores) / avg_cols if avg_cols > 0 else 1.0)
                    
                    # 偏好较多列数和高一致性
                    separator_scores[sep] = avg_cols * consistency
                    
                    logger.debug(f"分隔符 '{sep}': 平均列数={avg_cols:.1f}, 一致性={consistency:.2f}, 得分={separator_scores[sep]:.2f}")
            
            # 选择得分最高的分隔符
            best_separator = max(separator_scores.items(), key=lambda x: x[1])[0]
            logger.info(f"选择的分隔符: '{best_separator}' (得分: {separator_scores[best_separator]:.2f})")
            
            return best_separator
            
        except Exception as e:
            logger.warning(f"分隔符检测失败: {e}, 使用默认逗号")
            return ','
    
    def detect_header_rows(self, file_path: str, encoding: str, separator: str, max_check: int = 20) -> Tuple[int, int]:
        """
        检测头部行数和数据起始行
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            separator: 分隔符
            max_check: 最大检查行数
            
        Returns:
            (头部行数, 数据起始行数)
        """
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_check:
                        break
                    lines.append(line.strip())
            
            # 分析每行的数据类型特征
            numeric_scores = []
            column_counts = []
            
            for i, line in enumerate(lines):
                if not line:
                    numeric_scores.append(0)
                    column_counts.append(0)
                    continue
                    
                parts = line.split(separator)
                column_counts.append(len(parts))
                
                # 计算数值列的比例
                numeric_count = 0
                for part in parts:
                    part = part.strip()
                    if part:
                        try:
                            float(part)
                            numeric_count += 1
                        except ValueError:
                            pass
                
                numeric_ratio = numeric_count / len(parts) if parts else 0
                numeric_scores.append(numeric_ratio)
            
            # 找到列数稳定且主要包含数值的起始行
            if len(column_counts) < 2:
                return 0, 1
                
            # 找到最常见的列数
            common_col_count = max(set(column_counts), key=column_counts.count)
            
            # 找到数据起始行（列数稳定且数值比例高）
            data_start_row = 1  # 默认第二行开始
            for i in range(len(lines)):
                if (column_counts[i] == common_col_count and 
                    numeric_scores[i] > 0.5 and  # 超过50%的列是数值
                    i > 0):  # 不能是第一行
                    data_start_row = i
                    break
            
            header_row = max(0, data_start_row - 1)
            
            logger.info(f"检测到头部行: {header_row}, 数据起始行: {data_start_row}")
            return header_row, data_start_row
            
        except Exception as e:
            logger.warning(f"头部行检测失败: {e}, 使用默认值")
            return 0, 1
    
    def infer_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        推断数据类型
        
        Args:
            df: pandas DataFrame
            
        Returns:
            列名到数据类型的映射
        """
        type_mapping = {}
        
        for col in df.columns:
            series = df[col].dropna()
            
            if len(series) == 0:
                type_mapping[col] = 'text'
                continue
            
            # 尝试转换为数值
            try:
                pd.to_numeric(series)
                type_mapping[col] = 'numeric'
                continue
            except (ValueError, TypeError):
                pass
            
            # 尝试转换为日期
            try:
                pd.to_datetime(series)
                type_mapping[col] = 'datetime'
                continue
            except (ValueError, TypeError):
                pass
            
            # 默认为文本
            type_mapping[col] = 'text'
        
        return type_mapping
    
    def suggest_cf_variables(self, column_name: str) -> Dict[str, Any]:
        """
        基于列名建议CF标准变量
        
        Args:
            column_name: 列名
            
        Returns:
            CF变量建议信息
        """
        col_lower = column_name.lower().strip()
        
        # 直接匹配
        if col_lower in self.OCEANOGRAPHIC_VARIABLES:
            return self.OCEANOGRAPHIC_VARIABLES[col_lower].copy()
        
        # 模糊匹配
        best_match = None
        best_confidence = 0.0
        
        for var_name, var_info in self.OCEANOGRAPHIC_VARIABLES.items():
            # 检查是否包含关键字
            if var_name in col_lower or col_lower in var_name:
                confidence = var_info['confidence'] * 0.8  # 模糊匹配降低置信度
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = var_info.copy()
                    best_match['confidence'] = confidence
        
        if best_match:
            return best_match
        
        # 无匹配时返回默认值
        return {
            'standard_name': None,
            'units': None,
            'confidence': 0.0
        }
    
    def detect_anomalies(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """
        检测数据异常
        
        Args:
            df: pandas DataFrame
            
        Returns:
            异常信息字典
        """
        anomalies = {}
        
        for col in df.columns:
            col_anomalies = []
            series = df[col]
            
            # 检查缺失值比例
            missing_ratio = series.isnull().sum() / len(series)
            if missing_ratio > 0.5:
                col_anomalies.append(f"缺失值比例过高: {missing_ratio:.1%}")
            
            # 对于数值列，检查异常值
            if pd.api.types.is_numeric_dtype(series):
                numeric_series = pd.to_numeric(series, errors='coerce')
                if len(numeric_series.dropna()) > 0:
                    Q1 = numeric_series.quantile(0.25)
                    Q3 = numeric_series.quantile(0.75)
                    IQR = Q3 - Q1
                    
                    outliers = numeric_series[(numeric_series < Q1 - 1.5 * IQR) | 
                                            (numeric_series > Q3 + 1.5 * IQR)]
                    
                    if len(outliers) > len(numeric_series) * 0.1:  # 超过10%是异常值
                        col_anomalies.append(f"可能存在异常值: {len(outliers)}个")
            
            if col_anomalies:
                anomalies[col] = col_anomalies
        
        return anomalies
    
    def parse_file(self, file_path: str, temp_id: str) -> Dict[str, Any]:
        """
        完整解析CSV文件
        
        Args:
            file_path: 文件路径
            temp_id: 临时文件ID
            
        Returns:
            完整的解析结果
        """
        try:
            # 1. 检测编码
            encoding = self.detect_encoding(file_path)
            
            # 2. 检测分隔符
            separator = self.detect_separator(file_path, encoding)
            
            # 3. 检测头部行
            header_row, data_start_row = self.detect_header_rows(file_path, encoding, separator)
            
            # 4. 读取数据
            df = pd.read_csv(
                file_path, 
                encoding=encoding, 
                sep=separator,
                header=header_row,
                skiprows=range(header_row + 1, data_start_row) if data_start_row > header_row + 1 else None
            )
            
            logger.info(f"成功读取CSV文件: {len(df)}行 x {len(df.columns)}列")
            
            # 5. 数据类型推断
            data_types = self.infer_data_types(df)
            
            # 6. 生成列信息
            columns = []
            for col in df.columns:
                col_data = df[col]
                cf_suggestion = self.suggest_cf_variables(col)
                
                column_info = {
                    "name": col,
                    "data_type": data_types[col],
                    "sample_values": col_data.head(5).fillna("").tolist(),
                    "missing_count": int(col_data.isnull().sum()),
                    "total_count": len(col_data),
                    "suggested_cf_name": cf_suggestion.get('standard_name'),
                    "suggested_units": cf_suggestion.get('units'),
                    "confidence": cf_suggestion.get('confidence', 0.0)
                }
                columns.append(column_info)
            
            # 7. 检测异常
            anomalies = self.detect_anomalies(df)
            
            # 8. 生成预览数据
            preview_data = df.head(50).fillna("").to_dict('records')
            
            # 9. 解析配置
            parsing_config = {
                "encoding": encoding,
                "separator": separator,
                "header_row": header_row,
                "data_start_row": data_start_row
            }
            
            # 10. 质量报告
            quality_report = {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "missing_data_percentage": float(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100),
                "data_types_detected": {
                    "numeric": sum(1 for dt in data_types.values() if dt == "numeric"),
                    "datetime": sum(1 for dt in data_types.values() if dt == "datetime"),
                    "text": sum(1 for dt in data_types.values() if dt == "text")
                },
                "anomalies": anomalies,
                "encoding_confidence": "high" if encoding in ['utf-8', 'utf-8-sig'] else "medium"
            }
            
            return {
                "temp_id": temp_id,
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": columns,
                "preview_data": preview_data,
                "parsing_config": parsing_config,
                "quality_report": quality_report
            }
            
        except Exception as e:
            logger.error(f"CSV文件解析失败: {e}", exc_info=True)
            raise Exception(f"CSV文件解析失败: {str(e)}")


# 工厂函数
def create_csv_parser() -> CSVParser:
    """创建CSV解析器实例"""
    return CSVParser()


# 便捷函数
def parse_csv_file(file_path: str, temp_id: str) -> Dict[str, Any]:
    """解析CSV文件的便捷函数"""
    parser = create_csv_parser()
    return parser.parse_file(file_path, temp_id) 