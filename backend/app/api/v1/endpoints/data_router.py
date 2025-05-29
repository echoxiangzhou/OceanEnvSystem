from fastapi import APIRouter, HTTPException, Query, Path, Depends
from typing import List, Dict, Optional, Any
import os
from fastapi.responses import FileResponse, JSONResponse
from enum import Enum
import httpx
import xml.etree.ElementTree as ET
import urllib.parse
import time
import logging
from pathlib import Path as PathlibPath
from datetime import datetime

from app.core.json import custom_jsonable_encoder  # 导入我们的JSON编码器

from app.services.data_service import DataService, PROCESSED_DATA_ROOT, THREDDS_DATA_ROOT

# Setup a logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 使用服务中定义的路径
PROCESSED_DATA_PATH = PROCESSED_DATA_ROOT
THREDDS_DATA_PATH = THREDDS_DATA_ROOT

# THREDDS服务器URL
THREDDS_SERVER_URL = os.environ.get("THREDDS_SERVER_URL", "http://localhost:8080")
THREDDS_CATALOG_PATH = "/thredds/catalog/catalog.xml"
THREDDS_OPENDAP_PATH = "/thredds/dodsC"
THREDDS_HTTP_PATH = "/thredds/fileServer"

# XML命名空间
XML_NAMESPACES = {
    'thredds': 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0',
    'xlink': 'http://www.w3.org/1999/xlink'
}

# 检查路径正确性
if not os.path.exists(PROCESSED_DATA_PATH):
    print(f"警告: 处理数据目录不存在: {PROCESSED_DATA_PATH}")
    
if not os.path.exists(THREDDS_DATA_PATH):
    print(f"警告: Thredds数据目录不存在: {THREDDS_DATA_PATH}")

router = APIRouter(
    prefix="/data",
    tags=["data"]
)

class DataLocation(str, Enum):
    PROCESSED = "processed"  # 处理过的原始数据
    THREDDS = "thredds"     # Thredds格式化数据

@router.get("/debug/catalog-path", summary="测试不同的catalog路径")
def test_different_catalog_paths():
    """测试不同的catalog路径"""
    import requests
    paths = [
        "http://localhost:8080/thredds/catalog.xml",
        "http://localhost:8080/thredds/catalog/catalog.xml",
        "http://localhost:8080/thredds/catalog/oceanenv/catalog.xml",
        "http://localhost:8080/thredds/catalog/catalog/catalog.xml"
    ]
    
    results = []
    for path in paths:
        try:
            print(f"Testing path: {path}")
            response = requests.get(path, timeout=5.0)
            result = {
                "path": path,
                "status": response.status_code,
                "success": response.status_code == 200
            }
            if response.status_code == 200:
                result["content_type"] = response.headers.get("content-type")
                result["length"] = len(response.text)
                result["preview"] = response.text[:100]
            results.append(result)
        except Exception as e:
            results.append({
                "path": path,
                "error": str(e),
                "success": False
            })
    
    return results
    
@router.get("/debug/url-build", summary="测试URL构建")
def test_url_building():
    """测试URL构建逻辑，用于调试路径重复问题"""
    test_cases = [
        # 基本情况
        {"catalog_url": f"{THREDDS_SERVER_URL}/thredds/catalog/catalog.xml", "href": "model/catalog.xml"},
        # 重复路径情况
        {"catalog_url": f"{THREDDS_SERVER_URL}/thredds/catalog/thredds/catalog/catalog.xml", "href": "model/catalog.xml"},
        # href已包含thredds/catalog
        {"catalog_url": f"{THREDDS_SERVER_URL}/thredds/catalog/catalog.xml", "href": "thredds/catalog/model/catalog.xml"},
        # 其他特殊情况
        {"catalog_url": f"{THREDDS_SERVER_URL}/thredds/catalog/", "href": "/model/catalog.xml"},
        {"catalog_url": f"{THREDDS_SERVER_URL}/thredds/catalog", "href": "model/catalog.xml"}
    ]
    
    results = []
    for case in test_cases:
        catalog_url = case["catalog_url"]
        href = case["href"]
        
        # 解析服务器URL和相对路径部分
        if catalog_url.startswith(THREDDS_SERVER_URL):
            server_url = THREDDS_SERVER_URL
            relative_path = catalog_url[len(THREDDS_SERVER_URL):]
            if relative_path.startswith('/'):
                relative_path = relative_path[1:]
        else:
            server_url = ""
            relative_path = catalog_url
        
        # 标准化href路径
        clean_href = href[1:] if href.startswith('/') else href
        
        # 构建子URL
        if clean_href.startswith('thredds/catalog/'):
            sub_url = f"{server_url}/{clean_href}"
        elif relative_path.endswith('/catalog.xml'):
            parent_path = relative_path.rsplit('/', 1)[0]
            sub_url = f"{server_url}/{parent_path}/{clean_href}"
        elif 'thredds/catalog' in relative_path:
            base_dir = '/'.join(relative_path.split('/')[:-1])
            sub_url = f"{server_url}/{base_dir}/{clean_href}"
        else:
            base_url = catalog_url.rsplit('/', 1)[0] if '/' in catalog_url else catalog_url
            sub_url = f"{base_url}/{clean_href}"
        
        # 修复重复的thredds/catalog
        fixed_url = sub_url
        if sub_url.count('thredds/catalog') > 1:
            parts = sub_url.split('thredds/catalog')
            fixed_url = f"{server_url}/thredds/catalog{parts[-1]}"
        
        # 规范化URL中的双斜杠
        normalized_url = fixed_url.replace('://', '$$PROTO$$')
        while '//' in normalized_url:
            normalized_url = normalized_url.replace('//', '/')
        normalized_url = normalized_url.replace('$$PROTO$$', '://')
        
        results.append({
            "input": {"catalog_url": catalog_url, "href": href},
            "parsed": {"server_url": server_url, "relative_path": relative_path, "clean_href": clean_href},
            "output": {
                "initial_url": sub_url,
                "fixed_url": fixed_url,
                "normalized_url": normalized_url
            }
        })
    
    return results

@router.get("/debug/requests", summary="使用requests测试访问Catalog")
def test_requests_catalog_access():
    """使用requests测试访问Catalog XML"""
    import requests
    try:
        catalog_url = "http://localhost:8080/thredds/catalog/catalog.xml"
        print(f"Testing catalog access with requests: {catalog_url}")
        
        response = requests.get(catalog_url, timeout=10.0)
            
        if response.status_code != 200:
            return {"error": f"Failed to access catalog: {response.status_code}"}
            
        return {
            "success": True,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type"),
            "content_length": len(response.text),
            "first_200_chars": response.text[:200]
        }
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

@router.get("/debug/catalog", summary="测试直接访问Catalog")
async def test_catalog_access():
    """测试直接访问Catalog XML"""
    try:
        catalog_url = "http://localhost:8080/thredds/catalog/catalog.xml"
        print(f"Testing catalog access: {catalog_url}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(catalog_url, timeout=10.0)
            
        if response.status_code != 200:
            return {"error": f"Failed to access catalog: {response.status_code}"}
            
        return {
            "success": True,
            "status_code": response.status_code,
            "content_type": response.headers.get("content-type"),
            "content_length": len(response.text),
            "first_200_chars": response.text[:200]
        }
    except Exception as e:
        return {"error": f"Exception: {str(e)}"}

@router.get("/list", summary="获取所有 NetCDF 数据集文件（递归子目录）")
async def list_all_datasets(ext: str = "nc") -> List[str]:
    """
    获取所有指定类型的数据文件（默认.nc），返回相对路径
    兼容现有前端功能，使用THREDDS服务器
    """
    try:
        # 获取Thredds数据集
        datasets = await get_thredds_datasets()
        
        # 根据扩展名过滤并返回文件路径
        if ext:
            filtered_paths = [
                ds["urlPath"] for ds in datasets 
                if ds["urlPath"].lower().endswith(f".{ext.lower()}")
            ]
        else:
            filtered_paths = [ds["urlPath"] for ds in datasets]
            
        return filtered_paths
    except Exception as e:
        # 出错时返回空列表而不是错误
        print(f"获取数据文件列表失败: {str(e)}")
        return []

@router.get("/list/standard", summary="获取standard目录中已转换的数据文件列表", response_model=List[Dict])
async def list_standard_datasets(
    ext: Optional[str] = Query(None, description="文件扩展名过滤(不含点号，默认nc)")
):
    """
    获取standard目录中已转换的CF规范数据文件列表
    仅返回通过CF规范检查和转换的数据文件
    """
    try:
        # 获取standard目录路径
        # 当前文件位于: backend/app/api/v1/endpoints/data_router.py
        # 目标路径: backend/docker/thredds/data/oceanenv/standard
        # 从当前文件位置向上5级到达项目根目录，然后进入目标路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))))
        standard_dir = os.path.join(project_root, "backend", "docker", "thredds", "data", "oceanenv", "standard")
        
        logger.info(f"正在查找standard目录: {standard_dir}")
        logger.info(f"目录是否存在: {os.path.exists(standard_dir)}")
        
        if not os.path.exists(standard_dir):
            logger.warning(f"Standard目录不存在: {standard_dir}")
            return []
        
        # 设置文件扩展名过滤
        target_ext = ext if ext else "nc"
        logger.info(f"查找文件扩展名: {target_ext}")
        
        # 递归查找符合条件的文件
        datasets = []
        standard_path = PathlibPath(standard_dir)
        
        # 查找所有NetCDF文件
        for pattern in [f"**/*.{target_ext}", f"**/*.{target_ext.upper()}"]:
            logger.info(f"使用模式查找文件: {pattern}")
            files_found = list(standard_path.glob(pattern))
            logger.info(f"模式 {pattern} 找到 {len(files_found)} 个文件")
            
            for file_path in files_found:
                logger.info(f"处理文件: {file_path}")
                try:
                    # 获取文件信息
                    stat_info = file_path.stat()
                    rel_path = file_path.relative_to(standard_path)
                    
                    # 构建数据集信息
                    file_name = file_path.name
                    dataset_id = str(rel_path).replace(os.sep, '_').replace('.', '_')
                    
                    dataset_info = {
                        "id": dataset_id,
                        "datasetId": dataset_id,
                        "name": file_name,
                        "title": file_name.replace('.nc', '').replace('_', ' ').title(),
                        "description": f"CF-1.8规范转换后的数据文件: {file_name}",
                        "urlPath": f"oceanenv/standard/{rel_path}",
                        "opendapUrl": f"{THREDDS_SERVER_URL}{THREDDS_OPENDAP_PATH}/oceanenv/standard/{rel_path}",
                        "httpUrl": f"{THREDDS_SERVER_URL}{THREDDS_HTTP_PATH}/oceanenv/standard/{rel_path}",
                        "fileFormat": target_ext.upper(),
                        "file_format": target_ext.upper(),
                        "file_location": str(rel_path),
                        "filePath": str(rel_path),
                        "source_type": "CF_CONVERTED",
                        "data_type": "STANDARD",
                        "variables": [],
                        "created_at": datetime.fromtimestamp(stat_info.st_ctime).isoformat(),
                        "updated_at": datetime.fromtimestamp(stat_info.st_mtime).isoformat(),
                        "file_size": stat_info.st_size,
                        "threddsId": dataset_id
                    }
                    
                    # 根据文件路径推断数据类型
                    path_lower = str(rel_path).lower()
                    if "model" in path_lower:
                        dataset_info["source_type"] = "MODEL"
                        if "forecast" in path_lower:
                            dataset_info["data_type"] = "FORECAST"
                        elif "reanalysis" in path_lower:
                            dataset_info["data_type"] = "REANALYSIS"
                        else:
                            dataset_info["data_type"] = "MODEL_OUTPUT"
                    elif "satellite" in path_lower:
                        dataset_info["source_type"] = "SATELLITE"
                        dataset_info["data_type"] = "SATELLITE_DATA"
                    elif "buoy" in path_lower:
                        dataset_info["source_type"] = "BUOY"
                        dataset_info["data_type"] = "OBSERVATIONS"
                    elif "survey" in path_lower or "ctd" in path_lower:
                        dataset_info["source_type"] = "SURVEY"
                        dataset_info["data_type"] = "OBSERVATIONS"
                    
                    datasets.append(dataset_info)
                    
                except Exception as e:
                    logger.warning(f"处理文件时出错 {file_path}: {e}")
                    continue
        
        # 按修改时间排序（最新的在前面）
        datasets.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        logger.info(f"在standard目录中找到 {len(datasets)} 个已转换的数据文件")
        return datasets
        
    except Exception as e:
        logger.error(f"获取standard目录数据文件列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取已转换数据文件列表失败: {str(e)}")

@router.get("/list/{location}", summary="获取指定目录下的数据文件列表")
def list_datasets(
    location: DataLocation = Path(..., description="数据目录位置: processed或thredds"), 
    ext: Optional[str] = Query(None, description="文件扩展名过滤(不含点号)")) -> List[str]:
    """
    获取指定位置下的所有数据文件，可选按扩展名过滤
    """
    try:
        if location == DataLocation.PROCESSED:
            return DataService.get_processed_data_list(ext)
        elif location == DataLocation.THREDDS:
            return DataService.get_thredds_data_list(ext)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据位置: {location}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metadata/{location}", summary="获取指定数据文件的元数据")
def get_metadata(
    location: DataLocation,
    relpath: str = Query(..., description="数据文件相对路径")
):
    """
    获取指定位置和路径数据文件的元数据信息
    
    - **location**: 数据位置 (processed或thredds)
    - **relpath**: 数据文件相对路径 
    """
    try:
        if location == DataLocation.PROCESSED:
            file_path = os.path.join(PROCESSED_DATA_PATH, relpath)
        elif location == DataLocation.THREDDS:
            file_path = os.path.join(THREDDS_DATA_PATH, relpath)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据位置: {location}")
            
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {relpath}")
            
        # 获取元数据并确保所有NumPy类型都被正确处理
        metadata = DataService.get_file_metadata(file_path)
        serialized_metadata = custom_jsonable_encoder(metadata)
        return serialized_metadata
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取元数据失败: {str(e)}")

@router.get("/thredds/metadata", summary="获取Thredds服务器上数据集的元数据")
def get_thredds_metadata(
    url: str = Query(..., description="Thredds数据集URL，如http://localhost:8080/thredds/dodsC/path/to/dataset.nc")
):
    """
    从 Thredds 服务器上运行的 OPeNDAP 服务中获取数据集的元数据
    
    - **url**: Thredds数据集的URL地址
    
    返回数据集的详细元数据，包括变量、维度、坐标系和属性等信息。
    """
    try:
        # 获取元数据并确保使用自定义编码器转换NumPy类型
        metadata = DataService.get_thredds_metadata(url)
        serialized_metadata = custom_jsonable_encoder(metadata)
        return serialized_metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thredds元数据失败: {str(e)}")

@router.get("/thredds/metadata/{dataset_id}", summary="根据数据集ID获取Thredds元数据")
async def get_thredds_metadata_by_id(
    dataset_id: str = Path(..., description="数据集ID")
):
    """
    根据数据集ID获取Thredds元数据
    
    - **dataset_id**: 数据集ID
    
    返回数据集的详细元数据，包括变量、维度、坐标系和属性等信息。
    """
    try:
        # 获取所有数据集列表
        datasets = await get_thredds_datasets()
        
        # 查找匹配的数据集
        dataset = next((d for d in datasets if d["id"] == dataset_id), None)
        
        if not dataset:
            raise HTTPException(status_code=404, detail=f"未找到ID为{dataset_id}的数据集")
        
        # 如果数据集没有OPeNDAP URL，尝试构造
        if "opendapUrl" not in dataset and "urlPath" in dataset:
            dataset["opendapUrl"] = f"{THREDDS_SERVER_URL}{THREDDS_OPENDAP_PATH}/{dataset['urlPath']}"
        
        # 获取OPeNDAP元数据
        result = {}
        if "opendapUrl" in dataset:
            try:
                metadata = DataService.get_thredds_metadata(dataset["opendapUrl"])
                result = {
                    "dataset": dataset,
                    "metadata": metadata
                }
            except Exception as e:
                # 如果OPeNDAP获取失败，返回基本信息
                result = {
                    "dataset": dataset,
                    "error": f"获取OPeNDAP元数据失败: {str(e)}"
                }
        else:
            # 如果没有OPeNDAP URL，返回基本信息
            result = {
                "dataset": dataset
            }
            
        # 使用我们的自定义JSON编码器处理NumPy类型
        serialized_result = custom_jsonable_encoder(result)
        return serialized_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thredds元数据失败: {str(e)}")

@router.get("/download/{location}", summary="下载指定数据文件")
def download_dataset(
    location: DataLocation,
    relpath: str = Query(..., description="数据文件相对路径")
):
    """
    下载指定位置和路径的数据文件
    
    - **location**: 数据位置 (processed或thredds)
    - **relpath**: 数据文件相对路径
    """
    try:
        if location == DataLocation.PROCESSED:
            file_path = os.path.join(PROCESSED_DATA_PATH, relpath)
        elif location == DataLocation.THREDDS:
            file_path = os.path.join(THREDDS_DATA_PATH, relpath)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的数据位置: {location}")
            
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {relpath}")
            
        filename = os.path.basename(file_path)
        media_type = "application/octet-stream"
        
        # 根据文件扩展名设置适当的媒体类型
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".nc":  
            media_type = "application/x-netcdf"
        elif ext == ".csv":
            media_type = "text/csv"
        elif ext == ".json":
            media_type = "application/json"
            
        return FileResponse(
            file_path, 
            filename=filename, 
            media_type=media_type
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载文件失败: {str(e)}")

@router.get("/thredds/datasets", summary="获取Thredds服务器上的所有数据集")
async def get_thredds_datasets(
    catalog_path: str = Query("catalog.xml", description="Catalog路径，相对于Thredds服务器根目录"),
    recursive: bool = Query(True, description="是否递归获取子目录下的数据集")
):
    overall_start_time = time.perf_counter()
    logger.info(f"[get_thredds_datasets] Initiated for catalog_path: '{catalog_path}', recursive: {recursive}")
    try:
        logger.info(f"[get_thredds_datasets] Processing catalog_path: {catalog_path}")
        
        clean_path = catalog_path.strip()
        if clean_path.startswith('/'):
            clean_path = clean_path[1:]
            
        has_thredds_prefix = clean_path.startswith('thredds/')
        has_catalog_prefix = has_thredds_prefix and ('thredds/catalog/' in clean_path or clean_path == 'thredds/catalog')
        
        if clean_path == "catalog.xml":
            base_url = f"{THREDDS_SERVER_URL}/thredds/catalog/catalog.xml"
        elif has_catalog_prefix:
            base_url = f"{THREDDS_SERVER_URL}/{clean_path}"
            if not base_url.endswith(".xml"):
                if not base_url.endswith("/"): base_url += "/"
                base_url += "catalog.xml"
        elif has_thredds_prefix:
            parts = clean_path.split('/', 1)
            if len(parts) > 1:
                base_url = f"{THREDDS_SERVER_URL}/{parts[0]}/catalog/{parts[1]}"
                if not base_url.endswith(".xml"):
                    if not base_url.endswith("/"): base_url += "/"
                    base_url += "catalog.xml"
            else:
                base_url = f"{THREDDS_SERVER_URL}/thredds/catalog/catalog.xml"
        else:
            base_url = f"{THREDDS_SERVER_URL}/thredds/catalog/{clean_path}"
            if not base_url.endswith(".xml"):
                if not base_url.endswith("/"): base_url += "/"
                base_url += "catalog.xml"
        
        if base_url.count('thredds/catalog') > 1:
            parts = base_url.split('thredds/catalog')
            base_url = f"{THREDDS_SERVER_URL}/thredds/catalog{parts[-1]}"
            
        normalized_url = base_url.replace('://', '$$PROTO$$')
        while '//' in normalized_url:
            normalized_url = normalized_url.replace('//', '/')
        normalized_url = normalized_url.replace('$$PROTO$$', '://')
        
        url_options = [normalized_url] 
        logger.info(f"[get_thredds_datasets] Constructed Catalog URL to parse: {url_options[0]}")
        
        datasets_from_parse = []
        errors_from_parse = []
        
        for catalog_to_try_url in url_options:
            parse_call_start_time = time.perf_counter()
            logger.info(f"[get_thredds_datasets] Calling parse_thredds_catalog for URL: {catalog_to_try_url}")
            try:
                current_datasets = await parse_thredds_catalog(catalog_to_try_url, recursive, depth=3) 
                parse_call_duration = time.perf_counter() - parse_call_start_time
                if current_datasets:
                    logger.info(f"[get_thredds_datasets] Success from parse_thredds_catalog for {catalog_to_try_url} in {parse_call_duration:.4f}s. Found {len(current_datasets)} raw datasets.")
                    datasets_from_parse.extend(current_datasets)
                    break 
                else:
                    errors_from_parse.append(f"No datasets found at {catalog_to_try_url} (call took {parse_call_duration:.4f}s)")
            except Exception as e_parse:
                parse_call_duration = time.perf_counter() - parse_call_start_time
                logger.error(f"[get_thredds_datasets] Exception from parse_thredds_catalog for {catalog_to_try_url} in {parse_call_duration:.4f}s: {e_parse}", exc_info=True)
                errors_from_parse.append(f"Exception with {catalog_to_try_url}: {str(e_parse)}")
        
        if not datasets_from_parse and errors_from_parse:
            for err_msg in errors_from_parse:
                logger.warning(f"[get_thredds_datasets] Catalog parsing attempt failed: {err_msg}")
        
        formatting_start_time = time.perf_counter()
        formatted_datasets = []
        for ds_raw in datasets_from_parse:
            file_name = os.path.basename(ds_raw.get("urlPath", "unknown"))
            file_ext = os.path.splitext(file_name)[1].upper().lstrip('.') or "NC"
            # Ensure DataService is available or mock this part if DataService is complex to set up for this test
            dataset_id = ds_raw.get("urlPath", ds_raw.get("name", "")) # Simplified ID for now
            if 'DataService' in globals() and hasattr(DataService, 'generate_dataset_id'):
                dataset_id = DataService.generate_dataset_id(ds_raw.get("urlPath", ds_raw.get("name", "")))

            
            formatted_ds = {
                "id": dataset_id, "datasetId": dataset_id,
                "name": ds_raw.get("name", "Unknown Dataset"), "title": ds_raw.get("name", "Unknown Dataset"),
                "description": ds_raw.get("description", f"Thredds数据集: {ds_raw.get('name', 'Unknown')}"),
                "urlPath": ds_raw.get("urlPath", ""),
                "opendapUrl": f"{THREDDS_SERVER_URL}{THREDDS_OPENDAP_PATH}/{ds_raw.get('urlPath', '')}" if "urlPath" in ds_raw else None,
                "httpUrl": f"{THREDDS_SERVER_URL}{THREDDS_HTTP_PATH}/{ds_raw.get('urlPath', '')}" if "urlPath" in ds_raw else None,
                "fileFormat": file_ext, "file_format": file_ext,
                "file_location": ds_raw.get("urlPath", ""), "filePath": ds_raw.get("urlPath", ""),
                "source_type": "MODEL", "data_type": "OBSERVATIONS", 
                "variables": [], "created_at": "", "updated_at": "",
                "threddsId": ds_raw.get("id", "")
            }
            url_path_lower = ds_raw.get("urlPath", "").lower()
            if "model" in url_path_lower:
                formatted_ds["source_type"] = "MODEL"
                if "forecast" in url_path_lower: formatted_ds["data_type"] = "FORECAST"
                elif "reanalysis" in url_path_lower: formatted_ds["data_type"] = "REANALYSIS"
            elif "satellite" in url_path_lower: formatted_ds["source_type"] = "SATELLITE"
            elif "buoy" in url_path_lower: formatted_ds["source_type"] = "BUOY"
            elif "survey" in url_path_lower or "ctd" in url_path_lower: formatted_ds["source_type"] = "SURVEY"
            formatted_datasets.append(formatted_ds)
        
        formatting_duration = time.perf_counter() - formatting_start_time
        logger.info(f"[get_thredds_datasets] Dataset formatting took {formatting_duration:.4f}s. Number of formatted datasets: {len(formatted_datasets)}")
        
        overall_duration = time.perf_counter() - overall_start_time
        logger.info(f"[get_thredds_datasets] Completed successfully in {overall_duration:.4f}s. Returning {len(formatted_datasets)} datasets.")
        return formatted_datasets
        
    except Exception as e_main:
        overall_duration = time.perf_counter() - overall_start_time
        logger.error(f"[get_thredds_datasets] Failed in {overall_duration:.4f}s: {e_main}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取Thredds数据集失败: {str(e_main)}")

async def parse_thredds_catalog(
    catalog_url: str, 
    recursive: bool = True, 
    depth: int = 3 
) -> List[Dict]:
    func_start_time = time.perf_counter()
    logger.info(f"[parse_thredds_catalog depth={depth}] Parsing catalog: {catalog_url}")

    if depth <= 0:
        logger.warning(f"[parse_thredds_catalog depth={depth}] Max recursion depth reached for {catalog_url}. Returning empty list.")
        return []
        
    try:
        http_request_start_time = time.perf_counter()
        async with httpx.AsyncClient() as client:
            response = await client.get(catalog_url, timeout=20.0) # Increased timeout
        http_request_duration = time.perf_counter() - http_request_start_time
        
        if response.status_code != 200:
            logger.error(f"[parse_thredds_catalog depth={depth}] Failed to fetch catalog: {catalog_url}, status: {response.status_code}, took: {http_request_duration:.4f}s")
            return []
        
        logger.info(f"[parse_thredds_catalog depth={depth}] Successfully fetched {catalog_url}, status: {response.status_code}, took: {http_request_duration:.4f}s")
        xml_content = response.text
        
        xml_parse_start_time = time.perf_counter()
        try:
            root = ET.fromstring(xml_content)
            xml_parse_duration = time.perf_counter() - xml_parse_start_time
            logger.info(f"[parse_thredds_catalog depth={depth}] XML parsed for {catalog_url} in {xml_parse_duration:.4f}s. Root tag: {root.tag}")
        except Exception as xml_error:
            xml_parse_duration = time.perf_counter() - xml_parse_start_time
            logger.error(f"[parse_thredds_catalog depth={depth}] XML parsing error for {catalog_url} in {xml_parse_duration:.4f}s: {xml_error}. Content preview: {xml_content[:200]}", exc_info=True)
            return []
            
        results: List[Dict] = []
        
        datasets_found_xml = root.findall('.//thredds:dataset', XML_NAMESPACES)
        if not datasets_found_xml:
            datasets_found_xml = root.findall('.//dataset')
        
        logger.info(f"[parse_thredds_catalog depth={depth}] Found {len(datasets_found_xml)} <dataset> elements in {catalog_url}")
        
        for dataset_element in datasets_found_xml:
            url_path = dataset_element.get('urlPath')
            if url_path: 
                dataset_info = {
                    "id": dataset_element.get('ID'), "name": dataset_element.get('name'), "urlPath": url_path
                }
                documentation_elements = dataset_element.findall('.//thredds:documentation', XML_NAMESPACES)
                if not documentation_elements:
                    documentation_elements = dataset_element.findall('.//documentation')
                if documentation_elements:
                    dataset_info["description"] = ' '.join(doc.text or '' for doc in documentation_elements)
                results.append(dataset_info)
        
        logger.info(f"[parse_thredds_catalog depth={depth}] Found {len(results)} direct datasets in {catalog_url}")
        
        if recursive:
            logger.info(f"[parse_thredds_catalog depth={depth}] Processing catalogRefs for {catalog_url}...")
            catalog_ref_elements = root.findall('.//thredds:catalogRef', XML_NAMESPACES)
            if not catalog_ref_elements:
                catalog_ref_elements = root.findall('.//catalogRef')
            
            logger.info(f"[parse_thredds_catalog depth={depth}] Found {len(catalog_ref_elements)} <catalogRef> elements in {catalog_url}")

            for catalog_ref_element in catalog_ref_elements:
                href = catalog_ref_element.get('{http://www.w3.org/1999/xlink}href')
                if not href: href = catalog_ref_element.get('href')
                
                if href:
                    from urllib.parse import urljoin, urlparse, urlunparse # Local import for safety
                    
                    sub_catalog_url_raw = urljoin(catalog_url, href)
                    parsed_main_server = urlparse(THREDDS_SERVER_URL)
                    final_sub_path = sub_catalog_url_raw # Default to joined, then try to refine
                    
                    # Refined logic to handle various href and catalog_url structures more robustly
                    # Goal: Construct a URL that is absolute, starting with THREDDS_SERVER_URL,
                    # and correctly points to the sub-catalog.
                    
                    current_catalog_parsed = urlparse(catalog_url)
                    href_parsed = urlparse(href)

                    if href_parsed.scheme and href_parsed.netloc: # href is already an absolute URL
                        sub_catalog_url = href
                    else: # href is relative
                        sub_catalog_url = urljoin(f"{current_catalog_parsed.scheme}://{current_catalog_parsed.netloc}{current_catalog_parsed.path}", href)

                    # Ensure the path الجزء is correct relative to THREDDS_SERVER_URL's structure
                    # This part is tricky because 'thredds/catalog' might be part of THREDDS_SERVER_URL or part of the path
                    
                    # Attempt to normalize: Ensure it starts with THREDDS_SERVER_URL and contains /thredds/catalog/ once correctly.
                    # This is a simplified normalization. A more robust one would analyze THREDDS_SERVER_URL structure.
                    if THREDDS_SERVER_URL.endswith('/thredds/catalog') or THREDDS_SERVER_URL.endswith('/thredds/catalog/'):
                        server_base_for_join = THREDDS_SERVER_URL
                    elif THREDDS_SERVER_URL.endswith('/thredds') or THREDDS_SERVER_URL.endswith('/thredds/'):
                        server_base_for_join = f"{THREDDS_SERVER_URL.rstrip('/')}/catalog/"
                    else: # Assuming THREDDS_SERVER_URL is just scheme+host
                        server_base_for_join = f"{THREDDS_SERVER_URL.rstrip('/')}/thredds/catalog/"

                    path_part_of_sub = urlparse(sub_catalog_url).path
                    
                    # Remove server_base_for_join prefix if it's accidentally duplicated by urljoin
                    # This logic needs to be very careful not to break valid paths.
                    # For now, we'll rely on urljoin and a simple path cleanup.

                    temp_url = urlparse(sub_catalog_url)
                    clean_path = os.path.normpath(temp_url.path).replace("\\\\", "/") # Normalize .. and . and slashes
                    if clean_path.startswith('/') and len(clean_path) > 1: # Avoid making it "//"
                        clean_path = clean_path[1:]
                    
                    # Reconstruct with the main server and cleaned path.
                    # This assumes sub-catalog is always under the same THREDDS_SERVER_URL domain.
                    # And tries to ensure the /thredds/catalog/ part is correctly formed.
                    
                    # If href was absolute (e.g. "thredds/catalog/foo/catalog.xml") it might already be fine.
                    # If href was relative (e.g. "foo/catalog.xml"), urljoin handles it.
                    # The main challenge is ensuring no duplicate /thredds/catalog/ or missing it.

                    # Let's try to ensure the path starts with a single "thredds/catalog/" after the server base.
                    path_segments = clean_path.split('/')
                    if "thredds" in path_segments and "catalog" in path_segments:
                        try:
                            thredds_idx = path_segments.index("thredds")
                            catalog_idx = path_segments.index("catalog", thredds_idx)
                            if catalog_idx == thredds_idx + 1:
                                clean_path = "/".join(path_segments[thredds_idx:])
                            else: # thredds and catalog are separated, unusual
                               pass # Keep clean_path as is, might be an issue
                        except ValueError: # one of them not found after split, though 'in' check passed
                            pass
                    else: # if "thredds/catalog" is not in the path, prepend it (assuming it's missing)
                        # This might be too aggressive if THREDDS_SERVER_URL already has it.
                        # A better way is to rely on urljoin and then ensure the full URL is what we expect.
                        # For now, stick to the simpler urljoin result for sub_catalog_url
                        pass


                    # Final URL reconstruction with urljoin's result, then normalize slashes
                    final_sub_catalog_url = sub_catalog_url # Use urljoin's direct result mostly
                    
                    # Normalize slashes after protocol
                    proto_marker = "$$PROTO$$"
                    final_sub_catalog_url = final_sub_catalog_url.replace("://", proto_marker)
                    while '//' in final_sub_catalog_url:
                        final_sub_catalog_url = final_sub_catalog_url.replace('//', '/')
                    final_sub_catalog_url = final_sub_catalog_url.replace(proto_marker, '://')

                    logger.info(f"[parse_thredds_catalog depth={depth}] Recursing into (href='{href}', joined='{sub_catalog_url_raw}', final='{final_sub_catalog_url}')")
                    
                    recursion_call_start_time = time.perf_counter()
                    sub_results = await parse_thredds_catalog(final_sub_catalog_url, recursive, depth - 1)
                    recursion_call_duration = time.perf_counter() - recursion_call_start_time
                    logger.info(f"[parse_thredds_catalog depth={depth}] Recursive call to {final_sub_catalog_url} (depth {depth-1}) took {recursion_call_duration:.4f}s, found {len(sub_results)} items.")
                    results.extend(sub_results)
        
        func_duration = time.perf_counter() - func_start_time
        logger.info(f"[parse_thredds_catalog depth={depth}] Finished parsing {catalog_url} in {func_duration:.4f}s. Total direct+recursive datasets: {len(results)}")
        return results
        
    except httpx.TimeoutException as e_timeout:
        func_duration = time.perf_counter() - func_start_time
        logger.error(f"[parse_thredds_catalog depth={depth}] Timeout fetching {catalog_url} after {func_duration:.4f}s: {e_timeout}", exc_info=True)
        return [] 
    except Exception as e_generic:
        func_duration = time.perf_counter() - func_start_time
        logger.error(f"[parse_thredds_catalog depth={depth}] Failed parsing {catalog_url} in {func_duration:.4f}s: {e_generic}", exc_info=True)
        return []

@router.get("/list/thredds/formatted", summary="获取Thredds数据集格式化列表", response_model=List[Dict])
async def list_thredds_formatted_datasets(
    ext: Optional[str] = Query(None, description="文件扩展名过滤(不含点号)"),
    catalog_path: str = Query("catalog.xml", description="Catalog路径，相对于Thredds服务器根目录"),
    recursive: bool = Query(True, description="是否递归获取子目录下的数据集")
):
    # !!!!!!!!!! DEBUG PRINT !!!!!!!!!!!!!!
    print("!!!!!!!!!! [DEBUG] list_thredds_formatted_datasets ENTERED !!!!!!!!!!") 
    # !!!!!!!!!! END DEBUG PRINT !!!!!!!!!!!!!!
    
    overall_start_time = time.perf_counter()
    logger.info(f"[list_thredds_formatted_datasets] Initiated. ext: {ext}, catalog_path: {catalog_path}, recursive: {recursive}")
    try:
        get_datasets_call_start_time = time.perf_counter()
        all_datasets_raw = await get_thredds_datasets(catalog_path, recursive)
        get_datasets_call_duration = time.perf_counter() - get_datasets_call_start_time
        logger.info(f"[list_thredds_formatted_datasets] Call to get_thredds_datasets took {get_datasets_call_duration:.4f}s. Received {len(all_datasets_raw)} raw datasets.")
        
        if ext:
            filter_start_time = time.perf_counter()
            final_datasets = [ds for ds in all_datasets_raw if ds.get("fileFormat", "").lower() == ext.lower()]
            filter_duration = time.perf_counter() - filter_start_time
            logger.info(f"[list_thredds_formatted_datasets] Filtering by ext '{ext}' took {filter_duration:.4f}s. Filtered down to {len(final_datasets)} datasets.")
        else:
            final_datasets = all_datasets_raw
        
        if not final_datasets:
            logger.info("[list_thredds_formatted_datasets] No datasets found after filtering (or initially). Returning empty list.")
            # Do not return [], let it proceed to return final_datasets which would be []
            # return [] # This was causing empty list instead of 500 if get_thredds_datasets errored and returned empty.
                       # However, get_thredds_datasets now raises HTTPException on its own errors.

        overall_duration = time.perf_counter() - overall_start_time
        logger.info(f"[list_thredds_formatted_datasets] Completed successfully in {overall_duration:.4f}s. Returning {len(final_datasets)} datasets.")
        return final_datasets # If empty, will return empty list. If error in get_thredds_datasets, that will raise 500.
        
    except HTTPException as http_exc: 
        logger.error(f"[list_thredds_formatted_datasets] HTTPException occurred: {http_exc.detail}", exc_info=True)
        raise http_exc
    except Exception as e_main:
        overall_duration = time.perf_counter() - overall_start_time
        logger.error(f"[list_thredds_formatted_datasets] Failed in {overall_duration:.4f}s: {e_main}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取格式化Thredds数据集列表失败: {str(e_main)}")

@router.get("/debug/test-model-url", summary="测试模型URL")
async def test_model_url():
    """专门用于测试模型URL是否正确构建，避免路径重复问题"""
    # 模拟之前导致问题的情况
    problematic_path = "model/catalog.xml"
    
    # 1. 使用旧逻辑构建URL（模拟问题）
    old_url = f"{THREDDS_SERVER_URL}/thredds/catalog/thredds/catalog/{problematic_path}"
    
    # 2. 使用新逻辑构建URL
    # 清理路径
    clean_path = problematic_path.strip()
    if clean_path.startswith('/'):
        clean_path = clean_path[1:]
        
    # 构建基本URL
    base_url = f"{THREDDS_SERVER_URL}/thredds/catalog/{clean_path}"
    if not base_url.endswith(".xml"):
        if not base_url.endswith("/"):
            base_url += "/"
        base_url += "catalog.xml"
    
    # 修复重复的thredds/catalog
    if base_url.count('thredds/catalog') > 1:
        parts = base_url.split('thredds/catalog')
        base_url = f"{THREDDS_SERVER_URL}/thredds/catalog{parts[-1]}"
        
    # 修复URL中的双斜杠
    normalized_url = base_url.replace('://', '$$PROTO$$')
    while '//' in normalized_url:
        normalized_url = normalized_url.replace('//', '/')
    normalized_url = normalized_url.replace('$$PROTO$$', '://')
    
    new_url = normalized_url
    
    # 3. 创建比较结果
    comparison = {
        "input_path": problematic_path,
        "old_url": old_url,
        "new_url": new_url,
        "is_fixed": old_url != new_url,
        "explanation": "新URL逻辑成功修复了路径重复问题" if old_url != new_url else "URL构建逻辑仍有问题"
    }
    
    # 4. 实际测试对应的URL
    success = False
    error = None
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(new_url, timeout=5.0)
            success = response.status_code == 200
            if success:
                comparison["test_result"] = "成功访问URL"
            else:
                comparison["test_result"] = f"访问失败: HTTP {response.status_code}"
    except Exception as e:
        error = str(e)
        comparison["test_result"] = f"访问出错: {error}"
    
    return comparison

@router.get("/thredds/enhanced_metadata", summary="通过OPeNDAP链接获取Thredds数据集丰富元数据（xarray）")
def get_thredds_enhanced_metadata(
    url: str = Query(..., description="Thredds数据集OPeNDAP URL，如http://localhost:8080/thredds/dodsC/path/to/dataset.nc")
):
    """
    使用xarray通过OPeNDAP链接读取数据，返回丰富的元数据信息（标题、时间范围、空间范围、变量、生产者等）。
    """
    try:
        # 提取元数据并确保NumPy数据类型转换
        metadata = DataService.extract_enhanced_metadata(url)
        return DataService._convert_numpy_types(metadata)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取Thredds增强元数据失败: {str(e)}")