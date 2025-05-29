import os
import glob
import hashlib
from typing import List, Dict, Optional, Any, Union
import xarray as xr
import pandas as pd
import json
import pathlib
import datetime
import httpx
import xml.etree.ElementTree as ET
import urllib.parse
import numpy as np
import logging

# 获取项目根目录的绝对路径
BASE_DIR = pathlib.Path(__file__).parent.parent.parent.absolute()
print(f"BASE_DIR: {BASE_DIR}")

# 定义数据目录路径 - 使用绝对路径
PROCESSED_DATA_ROOT = os.path.join(BASE_DIR, "data/processed")  # 用户上传的处理后数据
THREDDS_DATA_ROOT = os.path.join(BASE_DIR, "docker/thredds/data/oceanenv")  # Thredds数据目录

# Thredds服务器访问配置
THREDDS_SERVER_URL = os.environ.get("THREDDS_SERVER_URL", "http://localhost:8080")  # 使用本地访问THREDDS服务
THREDDS_OPENDAP_PATH = "thredds/dodsC"
THREDDS_CATALOG_URL = f"{THREDDS_SERVER_URL}/thredds/catalog/catalog.xml"  # 包含完整路径

# XML命名空间
XML_NAMESPACES = {
    'thredds': 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0',
    'xlink': 'http://www.w3.org/1999/xlink'
}

# 确保路径存在
if not os.path.exists(PROCESSED_DATA_ROOT):
    print(f"警告: 处理数据目录不存在: {PROCESSED_DATA_ROOT}")
    
if not os.path.exists(THREDDS_DATA_ROOT):
    print(f"警告: Thredds数据目录不存在: {THREDDS_DATA_ROOT}")

logger = logging.getLogger(__name__) # Or use a specific name like logger_dataservice

class DataService:
    # 静态变量
    THREDDS_SERVER_URL = THREDDS_SERVER_URL
    THREDDS_OPENDAP_PATH = THREDDS_OPENDAP_PATH
    THREDDS_CATALOG_URL = THREDDS_CATALOG_URL

    @staticmethod
    def _convert_numpy_types(obj: Any) -> Any:
        """
        递归地将对象中的 NumPy 数据类型（如 int32, float64）转换为标准 Python 类型。
        处理 NaN 和 Inf 值。
        """
        if isinstance(obj, dict):
            return {k: DataService._convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [DataService._convert_numpy_types(i) for i in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return DataService._convert_numpy_types(obj.tolist()) # Convert ndarray to list first
        elif isinstance(obj, (pd.Timestamp, datetime.datetime, datetime.date)):
             return obj.isoformat()
        elif isinstance(obj, np.datetime64):
            # Convert np.datetime64 to pandas Timestamp then to ISO format string
            return pd.Timestamp(obj).isoformat()
        # Add any other specific numpy type conversions you need
        return obj

    @staticmethod
    def list_files(directory: str, extension: Optional[str] = None, recursive: bool = True) -> List[str]:
        """
        列出指定目录下所有符合扩展名的文件
        
        Args:
            directory: 目录路径
            extension: 文件扩展名(如 'nc', 'csv'), 不包含点号. 如果为None, 列出所有文件
            recursive: 是否递归搜索子目录
        
        Returns:
            文件路径的列表(相对于指定目录)
        """
        result = []
        
        if not os.path.exists(directory) or not os.path.isdir(directory):
            print(f"警告: 目录不存在或不是目录: {directory}")
            return result
        
        # 使用 os.walk 递归遍历所有子目录
        for root, _, files in os.walk(directory):
            # 如果不需要递归且不是目标目录，则跳过
            if not recursive and root != directory:
                continue
                
            for file in files:
                # 跳过隐藏文件
                if file.startswith('.'):
                    continue
                    
                # 如果指定了扩展名，过滤匹配的文件
                if extension and not file.lower().endswith(f'.{extension}'):
                    continue
                    
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, directory)
                result.append(rel_path)
                
        return sorted(result)
    
    @staticmethod
    def get_netcdf_metadata(file_path: str) -> Dict:
        """
        获取NetCDF文件的元数据
        
        Args:
            file_path: NetCDF文件路径
            
        Returns:
            包含变量、维度和属性信息的字典
        """
        try:
            ds = xr.open_dataset(file_path)
            # 提取元数据
            metadata = {
                "variables": list(ds.variables),
                "dims": {dim: int(size) for dim, size in ds.dims.items()}, # 确保维度是 Python int
                "coords": list(ds.coords),
                "attrs": dict(ds.attrs),
                "var_details": {}
            }
            
            # 添加每个变量的详细信息
            for var_name, var in ds.variables.items():
                metadata["var_details"][var_name] = {
                    "dims": list(var.dims),
                    "attrs": dict(var.attrs),
                    "dtype": str(var.dtype),
                    "shape": [int(s) for s in var.shape] # 确保形状是 Python int
                }
                
            ds.close()
            return DataService._convert_numpy_types(metadata) # 递归转换 NumPy 类型
        except Exception as e:
            raise Exception(f"读取NetCDF文件元数据错误: {str(e)}")
    
    @staticmethod
    def get_thredds_metadata(dataset_url: str) -> Dict:
        """
        获取Thredds服务器上数据集的元数据
        
        Args:
            dataset_url: 数据集URL，如 http://localhost:8080/thredds/dodsC/path/to/dataset.nc
            
        Returns:
            包含元数据的字典
        """
        try:
            # 尝试使用xarray打开远程数据集
            ds = xr.open_dataset(dataset_url, engine='netcdf4') # 确保 engine='netcdf4'
            
            # 提取元数据
            metadata = {
                "variables": list(ds.variables),
                "dims": {dim: int(size) for dim, size in ds.dims.items()}, # 确保维度是 Python int
                "coords": list(ds.coords),
                "attrs": dict(ds.attrs),
                "var_details": {}
            }
            
            # 添加每个变量的详细信息
            for var_name, var in ds.variables.items():
                detail = {
                    "dims": list(var.dims),
                    "attrs": dict(var.attrs),
                    "dtype": str(var.dtype),
                    "shape": [int(s) for s in var.shape] # 确保形状是 Python int
                }
                
                # 添加范围信息（如果可能）
                try:
                    if var.size > 0 and var.size < 10000:  # 防止过大的变量
                        values = var.values
                        # 使用 np.nanmin/np.nanmax 忽略 NaN 值，如果数组全为 NaN 则结果为 NaN
                        min_val = float(np.nanmin(values)) 
                        max_val = float(np.nanmax(values)) 
                        
                        # 检查是否为有限数字，如果不是则替换为 None
                        detail["min"] = min_val if np.isfinite(min_val) else None
                        detail["max"] = max_val if np.isfinite(max_val) else None
                except Exception as e:
                    detail["range_error"] = str(e)
            
                metadata["var_details"][var_name] = detail
            
            # 添加坐标信息
            metadata["coordinate_ranges"] = {}
            for coord_name in ds.coords:
                coord = ds.coords[coord_name]
                try:
                    if coord.size > 0 and coord.size < 10000:  # 防止过大的坐标
                        values = coord.values
                        # 使用 np.nanmin/np.nanmax 忽略 NaN 值，如果数组全为 NaN 则结果为 NaN
                        min_val = float(np.nanmin(values)) 
                        max_val = float(np.nanmax(values)) 
                        
                        # 检查是否为有限数字，如果不是则替换为 None
                        metadata["coordinate_ranges"][coord_name] = {
                            "min": min_val if np.isfinite(min_val) else None,
                            "max": max_val if np.isfinite(max_val) else None,
                            "size": int(values.size) # 确保 size 是 Python int
                        }
                except Exception as e:
                    metadata["coordinate_ranges"][coord_name] = {"error": str(e)}
            
            # 添加服务信息
            metadata["thredds_info"] = {
                "url": dataset_url,
                "access_type": "OPeNDAP"
            }
            
            ds.close()
            return DataService._convert_numpy_types(metadata) # 递归转换 NumPy 类型
        except Exception as e:
            raise Exception(f"获取Thredds数据元数据错误: {str(e)}")
    
    @staticmethod
    def get_csv_metadata(file_path: str) -> Dict:
        """
        获取CSV文件的元数据
        
        Args:
            file_path: CSV文件路径
            
        Returns:
            包含列名和数据类型的字典
        """
        try:
            # 只读取头部以提高效率
            df = pd.read_csv(file_path, nrows=5)
            
            metadata = {
                "columns": list(df.columns),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
                "shape": [df.shape[0], df.shape[1]],
                "preview": df.head().to_dict(orient="records")
            }
            
            return DataService._convert_numpy_types(metadata) # 递归转换 NumPy 类型
        except Exception as e:
            raise Exception(f"读取CSV文件元数据错误: {str(e)}")
    
    @staticmethod
    def get_file_metadata(file_path: str) -> Dict:
        """
        根据文件类型获取元数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            元数据字典
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.nc':
            return DataService.get_netcdf_metadata(file_path)
        elif ext in ['.csv', '.txt']:
            return DataService.get_csv_metadata(file_path)
        else:
            # 提供基本文件信息
            stats = os.stat(file_path)
            # 确保文件大小等也是 Python int
            result = {
                "file_size": int(stats.st_size),
                "modified": datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "ext": ext
            }
            return DataService._convert_numpy_types(result) # 递归转换 NumPy 类型
    
    @staticmethod
    def get_processed_data_list(extension: Optional[str] = None) -> List[str]:
        """
        获取已处理数据文件列表
        
        Args:
            extension: 可选的文件扩展名过滤
            
        Returns:
            文件路径列表
        """
        return DataService.list_files(PROCESSED_DATA_ROOT, extension)
    
    @staticmethod
    def get_thredds_data_list(extension: Optional[str] = None) -> List[str]:
        """
        获取Thredds数据目录下的文件列表
        
        Args:
            extension: 可选的文件扩展名过滤
            
        Returns:
            文件路径列表
        """
        return DataService.list_files(THREDDS_DATA_ROOT, extension)
    
    @staticmethod
    def get_data_file_path(data_type: str, rel_path: str) -> str:
        """
        获取完整的数据文件路径
        
        Args:
            data_type: 数据类型, 'processed' 或 'thredds'
            rel_path: 相对路径
            
        Returns:
            完整文件路径
        """
        if data_type == "processed":
            return os.path.join(PROCESSED_DATA_ROOT, rel_path)
        elif data_type == "thredds":
            return os.path.join(THREDDS_DATA_ROOT, rel_path)
        else:
            raise ValueError(f"未知的数据类型: {data_type}")
    
    @staticmethod
    def check_file_exists(file_path: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        return os.path.isfile(file_path)
    
    @staticmethod
    def generate_dataset_id(file_path: str) -> str:
        """
        根据文件路径生成唯一的datasetId
        
        Args:
            file_path: 文件路径
            
        Returns:
            datasetId字符串
        """
        # 使用MD5生成文件路径的哈希值，作为唯一ID
        return hashlib.md5(file_path.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_file_path_by_id(dataset_id: str) -> Optional[str]:
        """
        根据datasetId查找对应的文件路径
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            文件相对路径，如果未找到则返回None
        """
        # 获取所有可能的文件路径
        all_files = DataService.list_files(THREDDS_DATA_ROOT) # 应使用THREDDS_DATA_ROOT
        
        # 尝试匹配ID
        for file_path in all_files:
            if DataService.generate_dataset_id(file_path) == dataset_id:
                return file_path
                
        return None
    
    @staticmethod
    def _generate_title(file_name: str, folder_name: str) -> str:
        """生成数据集标题"""
        # 移除扩展名
        name_without_ext = os.path.splitext(file_name)[0]
        
        # 将下划线替换为空格，并将首字母大写
        title = name_without_ext.replace('_', ' ').title()
        
        # 如果文件名中包含年份，可以添加到标题中
        # 这里使用简单的示例逻辑，实际应用可能需要更精细的解析
        if folder_name.lower() in ['buoy', 'ctd', 'satellite', 'model']:
            ocean_area = "南海"  # 这里简单假设海域为南海，实际中可考虑从文件路径或内容中提取
            data_type = "表层盐度数据" if "salinity" in file_name.lower() else "海洋数据"
            return f"{ocean_area}{data_type}"
        
        return title
    
    @staticmethod
    def _generate_description(file_name: str, file_ext: str, folder_name: str) -> str:
        """生成数据集描述"""
        # 从文件名中提取年份
        year_match = DataService._extract_year(file_name)
        year_str = year_match if year_match else "2023"  # 默认使用当前年份
        
        # 根据文件夹和文件名生成不同的描述
        if "salinity" in file_name.lower():
            return f"{year_str}年南海区域表层盐度数据集，包含每日平均盐度"
        elif "temperature" in file_name.lower():
            return f"{year_str}年南海区域表层温度数据集，包含每日平均温度"
        elif folder_name.lower() == "model":
            return f"{year_str}年南海模式预报数据集"
        elif folder_name.lower() == "satellite":
            return f"{year_str}年南海卫星遥感数据集"
        else:
            return f"{year_str}年南海区域海洋环境数据集，{file_ext}格式"
    
    @staticmethod
    def _extract_year(filename: str) -> Optional[str]:
        """从文件名中提取年份"""
        import re
        # 匹配4位数字作为年份
        match = re.search(r'(19|20)\d{2}', filename)
        if match:
            return match.group(0)
        return None
    
    @staticmethod
    def _format_file_size(size_in_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_in_bytes < 1024.0:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.2f} PB"
    
    @staticmethod
    def _get_available_actions(file_ext: str) -> List[str]:
        """根据文件类型返回可用操作"""
        # 根据文件类型返回不同的操作
        actions = []
        
        if file_ext in ['NC', 'GRIB', 'HDF']:
            actions.append("模型")
            actions.append("再分析")
        elif file_ext in ['CSV', 'TXT']:
            actions.append("统计")
        
        # 对于常用数据全部添加可视化操作
        actions.append("可视化")
        
        return actions
    
    @staticmethod
    def get_formatted_dataset_list(data_root: str, extension: Optional[str] = None) -> List[Dict]:
        """
        获取格式化的数据集列表，包含查看详情所需信息
        
        Args:
            data_root: 数据目录路径
            extension: 可选的文件扩展名过滤
            
        Returns:
            数据集列表，每个元素包含datasetId和简要信息
        """
        result = []
        
        # 获取所有文件列表
        file_paths = DataService.list_files(data_root, extension)
        
        for rel_path in file_paths:
            try:
                full_path = os.path.join(data_root, rel_path)
                
                # 示例数据处理 - 实际应用中可能需要更复杂的解析逻辑
                file_info = os.stat(full_path)
                file_name = os.path.basename(rel_path)
                file_ext = os.path.splitext(file_name)[1].upper().lstrip('.')
                folder_name = os.path.basename(os.path.dirname(rel_path))
                
                # 生成datasetId
                dataset_id = DataService.generate_dataset_id(rel_path)
                
                # 根据文件属性和路径生成标题
                title = DataService._generate_title(file_name, folder_name)
                
                # 生成描述
                description = DataService._generate_description(file_name, file_ext, folder_name)
                
                # 获取变量列表
                variables = []
                if file_ext in ['NC', 'GRIB', 'HDF']:
                    try:
                        if file_ext == 'NC' and os.path.exists(full_path):
                            # 尝试打开NetCDF文件获取变量
                            with xr.open_dataset(full_path) as ds:
                                variables = list(ds.variables.keys())
                                # 限制变量列表长度
                                if len(variables) > 5:
                                    variables = variables[:5]
                    except Exception as e:
                        print(f"无法读取文件变量: {rel_path}, 错误: {str(e)}")
                
                # 格式化时间
                created_time = datetime.datetime.fromtimestamp(file_info.st_ctime).strftime('%Y-%m-%d %H:%M:%S')
                modified_time = datetime.datetime.fromtimestamp(file_info.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                
                # 组装数据集信息
                dataset_info = {
                    "datasetId": dataset_id,
                    "title": title,
                    "description": description,
                    "fileFormat": file_ext,
                    "filePath": rel_path,
                    "createdTime": created_time,
                    "updatedTime": modified_time,
                    "fileSize": DataService._format_file_size(file_info.st_size),
                    "variables": [{"name": var} for var in variables],  # 转换为前端需要的格式
                    "actions": DataService._get_available_actions(file_ext),
                    # 添加前端适配的字段
                    "id": dataset_id,
                    "name": title,
                    "file_format": file_ext,
                    "file_location": rel_path,
                    "created_at": created_time,
                    "updated_at": modified_time,
                    "source_type": "MODEL" if "model" in folder_name.lower() else 
                                  "SATELLITE" if "satellite" in folder_name.lower() else
                                  "BUOY" if "buoy" in folder_name.lower() else "SURVEY",
                    "data_type": "FORECAST" if "forecast" in file_name.lower() else
                                "REANALYSIS" if "reanalysis" in file_name.lower() else "OBSERVATIONS"
                }
                
                result.append(DataService._convert_numpy_types(dataset_info)) # 递归转换 NumPy 类型
            except Exception as e:
                print(f"处理文件信息错误: {rel_path}, 其错误: {str(e)}")
        
        return result
    
    @staticmethod
    def get_dataset_by_id(dataset_id: str) -> Dict:
        """
        根据datasetId获取数据集信息
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集详细信息
        """
        # 首先检查processed目录
        processed_datasets = DataService.get_formatted_dataset_list(PROCESSED_DATA_ROOT)
        for dataset in processed_datasets:
            if dataset["datasetId"] == dataset_id:
                return DataService._get_detailed_metadata("processed", dataset)
        
        # 然后检查thredds目录
        thredds_datasets = DataService.get_formatted_dataset_list(THREDDS_DATA_ROOT)
        for dataset in thredds_datasets:
            if dataset["datasetId"] == dataset_id:
                return DataService._get_detailed_metadata("thredds", dataset)
        
        # 如果都找不到，抛出异常
        raise Exception(f"未找到ID为{dataset_id}的数据集")
    
    @staticmethod
    def _get_detailed_metadata(source_type: str, dataset_info: Dict) -> Dict:
        """
        获取数据集的详细元数据
        
        Args:
            source_type: 数据源类型，'processed' 或 'thredds'
            dataset_info: 基本数据集信息
            
        Returns:
            详细的元数据信息
        """
        # 获取路径
        rel_path = dataset_info["filePath"]
        if source_type == "processed":
            full_path = os.path.join(PROCESSED_DATA_ROOT, rel_path)
            # 获取本地文件元数据
            try:
                file_metadata = DataService.get_file_metadata(full_path)
                # 合并基本信息和元数据
                result = {**dataset_info, "metadata": file_metadata}
                # 添加下载链接
                result["downloadUrl"] = f"/api/v1/data/download/processed?relpath={rel_path}"
                return DataService._convert_numpy_types(result) # 递归转换 NumPy 类型
            except Exception as e:
                # 如果无法获取元数据，返回基本信息
                return DataService._convert_numpy_types({**dataset_info, "error": f"无法获取元数据: {str(e)}"}) # 递归转换 NumPy 类型
        elif source_type == "thredds":
            full_path = os.path.join(THREDDS_DATA_ROOT, rel_path)
            # 准备OPeNDAP URL
            opendap_url = f"{THREDDS_SERVER_URL}/{THREDDS_OPENDAP_PATH}/{rel_path}"
            
            try:
                # 首先尝试获取本地文件元数据
                file_metadata = {}
                if os.path.exists(full_path):
                    file_metadata = DataService.get_file_metadata(full_path)
                
                # 如果是NetCDF文件，尝试使OPeNDAP获取详细元数据
                if dataset_info["fileFormat"] in ["NC", "GRIB", "HDF"]:
                    try:
                        thredds_metadata = DataService.get_thredds_metadata(opendap_url)
                        # 合并基本信息和元数据
                        result = {**dataset_info, "metadata": thredds_metadata}
                    except Exception as e:
                        # 如果无法使OPeNDAP获取，使用本地文件元数据
                        result = {**dataset_info, "metadata": file_metadata}
                else:
                    # 非NetCDF文件直接使用本地文件元数据
                    result = {**dataset_info, "metadata": file_metadata}
                
                # 添加下载和在线OPeNDAP链接
                result["downloadUrl"] = f"/api/v1/data/download/thredds?relpath={rel_path}"
                result["opendapUrl"] = opendap_url
                result["httpUrl"] = f"{THREDDS_SERVER_URL}/thredds/fileServer/{rel_path}"
                
                return DataService._convert_numpy_types(result) # 递归转换 NumPy 类型
            except Exception as e:
                # 如果无法获取元数据，返回基本信息
                return DataService._convert_numpy_types({**dataset_info, "error": f"无法获取元数据: {str(e)}"}) # 递归转换 NumPy 类型
        else:
            raise ValueError(f"无效的数据源类型: {source_type}")
    
    @staticmethod
    async def get_thredds_catalog_datasets(catalog_url: str = None, depth: int = 2) -> List[Dict]:
        """
        解析THREDDS Catalog XML文件获取数据集信息
        
        Args:
            catalog_url: Catalog URL，默认使用THREDDS_CATALOG_URL
            depth: 递归深度，防止无限递归
            
        Returns:
            数据集列表，包含ID和URL
        """
        if catalog_url is None:
            catalog_url = THREDDS_CATALOG_URL
            
        if depth <= 0:
            return []
            
        try:
            # 下载Catalog XML
            async with httpx.AsyncClient() as client:
                response = await client.get(catalog_url, timeout=10.0)
                response.raise_for_status()
                xml_content = response.text
            
            # 解析XML
            root = ET.fromstring(xml_content)
            
            results = []
            
            # 查找数据集元素
            datasets = root.findall('.//thredds:dataset', XML_NAMESPACES)
            for dataset in datasets:
                dataset_id = dataset.get('ID')
                dataset_name = dataset.get('name')
                url_path = dataset.get('urlPath')
                
                # 只处理有ID和urlPath的数据集
                if dataset_id and url_path:
                    # 构建完整URL
                    dataset_url = f"{THREDDS_SERVER_URL}/thredds/dodsC/{url_path}"
                    
                    # 提取相对路径作为filePath
                    file_path = url_path
                    
                    # 生成本地ID
                    local_id = DataService.generate_dataset_id(file_path)
                    
                    # 添加到结果列表
                    results.append({
                        "id": local_id,
                        "threddsId": dataset_id,
                        "name": dataset_name,
                        "url": dataset_url,
                        "filePath": file_path
                    })
            
            # 处理子Catalog引用
            catalog_refs = root.findall('.//thredds:catalogRef', XML_NAMESPACES)
            for catalog_ref in catalog_refs:
                if depth > 1:  # 控制递归深度
                    href = catalog_ref.get('{http://www.w3.org/1999/xlink}href')
                    if href:
                        # 构建完整的子Catalog URL
                        base_url = '/'.join(catalog_url.split('/')[:-1])
                        sub_catalog_url = f"{base_url}/{href}"
                        
                        # 递归处理子Catalog
                        sub_results = await DataService.get_thredds_catalog_datasets(sub_catalog_url, depth - 1)
                        results.extend(sub_results)
            
            return DataService._convert_numpy_types(results) # 递归转换 NumPy 类型
        except Exception as e:
            print(f"获取THREDDS Catalog数据失败: {str(e)}")
            return []

    @staticmethod
    def extract_enhanced_metadata(opendap_url: str) -> Dict[str, Any]:
        # MODIFIED: Added logger and entry log
        logger.info(f"[DataService.extract_enhanced_metadata] Attempting to process OPeNDAP URL: {opendap_url}")

        parsed_url = urllib.parse.urlparse(opendap_url)
        file_path_in_url = parsed_url.path
        file_name_from_url = os.path.basename(file_path_in_url)
        file_ext = os.path.splitext(file_name_from_url)[1].lower()

        if file_ext not in ['.nc', '.hdf', '.hdf5', '.h5']:
            # MODIFIED: Added logger
            logger.warning(f"[DataService.extract_enhanced_metadata] Unsupported file extension '{file_ext}' for URL: {opendap_url}")
            return {
                "error": f"文件类型不受支持: {file_ext}. 此接口仅处理 .nc 和 .hdf/.hdf5/.h5 文件。",
                "title": file_name_from_url or opendap_url,
                "unsupported_file_type": True
            }

        try:
            # MODIFIED: Added logger before opening dataset
            logger.info(f"[DataService.extract_enhanced_metadata] Attempting to open dataset with xarray: {opendap_url}")
            # Ensure decode_times=True is appropriate, or handle time decoding carefully later
            ds = xr.open_dataset(opendap_url, engine='netcdf4', decode_times=True) 
            logger.info(f"[DataService.extract_enhanced_metadata] Successfully opened dataset: {opendap_url}")
            
            metadata = {}

            # 1. 数据集标题
            metadata['title'] = ds.attrs.get('title', ds.attrs.get('name', opendap_url.split('/')[-1]))

            # 2. 数据集描述
            metadata['description'] = ds.attrs.get('summary', ds.attrs.get('description', 'No description available.'))

            # 3. 时间范围 (尝试多种常用名称)
            time_var_names = ['time', 'TIME', 'Time', 't'] 
            time_coord = None
            for name in time_var_names:
                if name in ds.coords:
                    time_coord = ds.coords[name]
                    break
            
            if time_coord is not None and time_coord.size > 0:
                try:
                    if np.issubdtype(time_coord.dtype, np.datetime64) or \
                       (hasattr(time_coord.values[0], 'isoformat')) or \
                       isinstance(time_coord.values[0], (datetime.datetime, pd.Timestamp)):
                        
                        # Handle array of datetime objects or numpy.datetime64
                        min_val = pd.Timestamp(time_coord.min().values).isoformat()
                        max_val = pd.Timestamp(time_coord.max().values).isoformat()
                        metadata['time_range'] = {'start': min_val, 'end': max_val}
                    else: # Non-standard time, try cftime if units attribute present
                        if 'units' in time_coord.attrs and 'since' in time_coord.attrs['units']:
                            try:
                                import cftime
                                calendar_to_use = time_coord.attrs.get('calendar', 'standard')
                                logger.info(f"[DataService.extract_enhanced_metadata] Using cftime for time conversion. Units: {time_coord.attrs['units']}, Calendar: {calendar_to_use}")
                                dates = cftime.num2pydate(time_coord.values, units=time_coord.attrs['units'], calendar=calendar_to_use)
                                # Ensure dates are actual datetime objects before min/max
                                if not isinstance(dates, np.ndarray) or dates.size == 0: # if num2pydate returns single or no date
                                     metadata['time_range'] = {'error': 'Time conversion with cftime did not yield multiple dates.'}
                                else:
                                    metadata['time_range'] = {
                                        'start': pd.Timestamp(dates.min()).isoformat(),
                                        'end': pd.Timestamp(dates.max()).isoformat()
                                    }
                            except ImportError:
                                logger.warning("[DataService.extract_enhanced_metadata] cftime library not available for non-standard time conversion.")
                                metadata['time_range'] = {'error': 'cftime library not available for non-standard time conversion'}
                            except Exception as e_time_conv:
                                logger.error(f"[DataService.extract_enhanced_metadata] cftime conversion error: {e_time_conv}", exc_info=True)
                                metadata['time_range'] = {'error': f'Time conversion error: {str(e_time_conv)}'}
                        else:
                             logger.warning(f"[DataService.extract_enhanced_metadata] Non-standard time coordinate for {opendap_url} without parsable units attribute.")
                             metadata['time_range'] = {'error': 'Non-standard time coordinate without parsable units attribute.'}
                except Exception as e_time:
                    logger.error(f"[DataService.extract_enhanced_metadata] Could not parse time information for {opendap_url}: {e_time}", exc_info=True)
                    metadata['time_range'] = {'error': f'Could not parse time information: {str(e_time)}'}
            else: 
                start_attr = ds.attrs.get('time_coverage_start', ds.attrs.get('geospatial_time_min', None))
                end_attr = ds.attrs.get('time_coverage_end', ds.attrs.get('geospatial_time_max', None))
                if start_attr and end_attr:
                     metadata['time_range'] = {'start': str(start_attr), 'end': str(end_attr)}
                else:
                    logger.warning(f"[DataService.extract_enhanced_metadata] Time coordinate not found or empty for {opendap_url}.")
                    metadata['time_range'] = {'error': 'Time coordinate not found or empty.'}

            # 4. 空间范围
            lat_names = ['lat', 'latitude', 'LATITUDE', 'Latitude', 'lat_rho', 'nav_lat']
            lon_names = ['lon', 'longitude', 'LONGITUDE', 'Longitude', 'lon_rho', 'nav_lon']
            lat_coord, lon_coord = None, None
            for name in lat_names: 
                if name in ds.coords: lat_coord = ds.coords[name]; break
            for name in lon_names: 
                if name in ds.coords: lon_coord = ds.coords[name]; break

            if lat_coord is not None and lon_coord is not None and lat_coord.size > 0 and lon_coord.size > 0:
                metadata['spatial_range'] = {
                    'latitude': {'min': float(lat_coord.min()), 'max': float(lat_coord.max()), 'units': lat_coord.attrs.get('units', 'degrees_north')},
                    'longitude': {'min': float(lon_coord.min()), 'max': float(lon_coord.max()), 'units': lon_coord.attrs.get('units', 'degrees_east')}
                }
            else:
                min_lat_attr = ds.attrs.get('geospatial_lat_min', ds.attrs.get('southernmost_latitude', None))
                max_lat_attr = ds.attrs.get('geospatial_lat_max', ds.attrs.get('northernmost_latitude', None))
                min_lon_attr = ds.attrs.get('geospatial_lon_min', ds.attrs.get('westernmost_longitude', None))
                max_lon_attr = ds.attrs.get('geospatial_lon_max', ds.attrs.get('easternmost_longitude', None))
                if all([min_lat_attr, max_lat_attr, min_lon_attr, max_lon_attr]):
                    try:
                        metadata['spatial_range'] = {
                            'latitude': {'min': float(min_lat_attr), 'max': float(max_lat_attr), 'units': 'degrees_north'},
                            'longitude': {'min': float(min_lon_attr), 'max': float(max_lon_attr), 'units': 'degrees_east'}
                        }
                    except ValueError as e_spatial_attr_conv:
                        logger.warning(f"[DataService.extract_enhanced_metadata] Could not convert global spatial attributes to float for {opendap_url}: {e_spatial_attr_conv}")
                        metadata['spatial_range'] = {'error': f'Error converting global spatial attributes: {str(e_spatial_attr_conv)}'}
                else:
                    logger.warning(f"[DataService.extract_enhanced_metadata] Lat/Lon coordinates or global spatial attributes not found for {opendap_url}.")
                    metadata['spatial_range'] = {'error': 'Latitude or Longitude coordinates not found or empty.'}

            # 5. 变量信息
            variables_info = []
            for var_name, variable in ds.data_vars.items():
                var_info = {
                    'name': var_name,
                    'standard_name': variable.attrs.get('standard_name', ''),
                    'long_name': variable.attrs.get('long_name', var_name),
                    'units': variable.attrs.get('units', ''),
                    'dimensions': list(variable.dims),
                    'shape': [int(s) for s in variable.shape],
                    'attributes': dict(variable.attrs)
                }
                variables_info.append(var_info)
            metadata['variables'] = variables_info
            
            # 6. 数据生产者/机构等信息
            source_info = {}
            creator_keys = ['creator_name', 'creator', 'institution', 'source', 'publisher_name', 'project']
            for key in creator_keys:
                if key in ds.attrs:
                    source_info[key.replace('_name','').replace('publisher_', '')] = ds.attrs[key]
            if not source_info and 'Conventions' in ds.attrs:
                 source_info['institution_from_conventions'] = ds.attrs['Conventions']
            metadata['source_information'] = source_info if source_info else {"info":"No specific source/creator information found."}

            # 7. 数据创建/修改日期
            metadata['creation_date'] = ds.attrs.get('date_created', ds.attrs.get('history_date', ds.attrs.get('date_modified', None)))
            if metadata['creation_date'] is None:
                history = ds.attrs.get('history', '')
                if history:
                    import re
                    match = re.search(r'(\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}Z|\\d{4}-\\d{2}-\\d{2})', history)
                    if match: metadata['creation_date'] = match.group(0)

            metadata['global_attributes'] = dict(ds.attrs)
            
            # MODIFIED: Added logger before closing dataset and returning
            logger.info(f"[DataService.extract_enhanced_metadata] Successfully extracted metadata for: {opendap_url}. Title: {metadata.get('title')}")
            ds.close()
            return DataService._convert_numpy_types(metadata)

        except FileNotFoundError: 
            logger.error(f"[DataService.extract_enhanced_metadata] FileNotFoundError for OPeNDAP URL '{opendap_url}'. xarray might misinterpret a bad remote URL as a local file.", exc_info=True)
            return {
                "error": f"OPeNDAP URL 无法访问或文件不存在: {opendap_url}",
                "title": file_name_from_url or opendap_url,
                "file_not_found": True
            }

        except ValueError as ve:
            logger.warning(f"[DataService.extract_enhanced_metadata] ValueError processing OPeNDAP URL '{opendap_url}': {ve}", exc_info=True)
            if "File format not recognized" in str(ve) or "must be netCDF3, netCDF4, NCDAP, HDF5, or GRIB" in str(ve):
                 return {
                    "error": f"不支持的文件格式或无法通过OPeNDAP读取: {file_name_from_url}. 请确保文件是有效的NetCDF或HDF格式。原始错误: {str(ve)}",
                    "title": file_name_from_url or opendap_url,
                    "unsupported_file_type": True 
                }   
            return {
                "error": f"提取增强元数据时发生值错误: {str(ve)}",
                "title": file_name_from_url or opendap_url
            }

        except Exception as e:
            logger.error(f"[DataService.extract_enhanced_metadata] Generic error processing OPeNDAP URL '{opendap_url}': {e}", exc_info=True)
            # traceback.print_exc() # Already logged with exc_info=True
            return {
                "error": f"提取增强元数据时发生意外错误: {str(e)}", # Ensure this message is useful to frontend
                "title": file_name_from_url or opendap_url # Provide title for context if possible
            }