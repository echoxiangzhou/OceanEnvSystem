from fastapi import APIRouter, HTTPException, Query, Path, Depends, UploadFile, File, Form
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
import uuid
import aiofiles
import shutil

from app.core.json import custom_jsonable_encoder  # 导入我们的JSON编码器
from app.schemas.dataset import (
    FileUploadResponse, DataPreview, MetadataConfig, ValidationResult, 
    ConversionResult, FileType, ParseStatus
)

from app.services.data_service import DataService, PROCESSED_DATA_ROOT, THREDDS_DATA_ROOT
from app.db.session import get_db
from app.services.data_import_service import DataImportService
from app.schemas.dataset import DataImportRecordCreate, DataImportRecordUpdate
from app.db.models import ImportStatusEnum, FileTypeEnum as DBFileTypeEnum, ValidationLevelEnum
from sqlalchemy.orm import Session
from app.services.parsers.csv_parser import parse_csv_file

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


# ===============================================================================
# 数据导入功能 API 端点
# ===============================================================================

# 临时文件存储配置
UPLOADS_ROOT = os.path.join(os.getcwd(),  "data", "uploads", "raw")
TEMP_FILES_CACHE = {}  # 临时文件信息缓存

# 确保上传目录存在
os.makedirs(UPLOADS_ROOT, exist_ok=True)

def get_file_type(filename: str) -> FileType:
    """根据文件扩展名确定文件类型"""
    ext = filename.lower().split('.')[-1]
    if ext == 'csv':
        return FileType.CSV
    elif ext in ['xlsx', 'xls']:
        return FileType.EXCEL
    elif ext == 'cnv':
        return FileType.CNV
    elif ext in ['nc', 'netcdf', 'nc4']:
        return FileType.NETCDF
    else:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

def detect_file_encoding(file_path: str) -> str:
    """检测文件编码"""
    import chardet
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(10000)  # 读取前10KB用于检测
            result = chardet.detect(raw_data)
            return result.get('encoding', 'utf-8')
    except:
        return 'utf-8'

def parse_csv_preview(file_path: str, temp_id: str) -> Dict[str, Any]:
    """解析CSV文件预览（使用新的智能解析器）"""
    try:
        # 使用新的CSV解析器
        return parse_csv_file(file_path, temp_id)
    except Exception as e:
        logger.error(f"CSV文件解析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"解析CSV文件失败: {str(e)}")

def parse_cnv_preview(file_path: str, temp_id: str) -> Dict[str, Any]:
    """解析CNV文件预览（使用智能CNV解析器）"""
    try:
        from app.services.parsers.cnv_parser import parse_cnv_file
        return parse_cnv_file(file_path, temp_id)
    except Exception as e:
        logger.error(f"CNV文件解析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"解析CNV文件失败: {str(e)}")

@router.post("/import/upload", response_model=FileUploadResponse, summary="文件上传")
async def upload_data_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    上传数据文件进行导入处理
    支持格式：CSV、Excel、CNV、NetCDF
    """
    try:
        # 检查文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
            
        # 检查文件大小（限制100MB）
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="文件大小超过限制（100MB）")
            
        # 确定文件类型
        file_type = get_file_type(file.filename)
        
        # 生成临时文件ID
        temp_id = str(uuid.uuid4())
        
        # 保存文件
        file_path = os.path.join(UPLOADS_ROOT, f"{temp_id}_{file.filename}")
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
            
        # 初步解析检查
        parse_status = ParseStatus.SUCCESS
        parse_message = "文件上传成功"
        
        try:
            if file_type == FileType.CSV:
                # 简单检查CSV格式
                import pandas as pd
                encoding = detect_file_encoding(file_path)
                df = pd.read_csv(file_path, encoding=encoding, nrows=5)
                if len(df.columns) == 0:
                    parse_status = ParseStatus.ERROR
                    parse_message = "CSV文件格式无效"
            elif file_type == FileType.CNV:
                # 检查CNV文件格式
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    lines = f.readlines()
                    # 检查是否有CNV文件的特征标记
                    has_header = any(line.startswith('*') for line in lines[:20])
                    has_end_marker = any(line.strip() == '*END*' for line in lines)
                    if not (has_header or has_end_marker):
                        parse_status = ParseStatus.WARNING
                        parse_message = "文件可能不是标准CNV格式，但将尝试解析"
            elif file_type == FileType.NETCDF:
                # 检查NetCDF文件
                import xarray as xr
                ds = xr.open_dataset(file_path)
                ds.close()
        except Exception as e:
            parse_status = ParseStatus.WARNING
            parse_message = f"文件上传成功，但解析时遇到警告: {str(e)}"
            
        # 创建数据库记录
        record_data = DataImportRecordCreate(
            temp_id=temp_id,
            original_filename=file.filename,
            file_type=DBFileTypeEnum(file_type),
            file_size=len(content),
            import_status=ImportStatusEnum.UPLOADED,
            progress_percentage=10.0,
            user_id="default",  # 可以从认证系统获取
            user_name="数据导入用户"
        )
        
        db_record = DataImportService.create_import_record(db, record_data, file_path)
        
        # 缓存文件信息（保持向后兼容）
        file_info = {
            "temp_id": temp_id,
            "filename": file.filename,
            "file_type": file_type.value if hasattr(file_type, 'value') else str(file_type),
            "file_size": len(content),
            "file_path": file_path,
            "upload_time": datetime.now().isoformat(),
            "parse_status": parse_status.value if hasattr(parse_status, 'value') else str(parse_status),
            "parse_message": parse_message or "",
            "db_record_id": db_record.id
        }
        
        TEMP_FILES_CACHE[temp_id] = file_info
        
        logger.info(f"文件上传成功: {file.filename}, temp_id: {temp_id}, db_id: {db_record.id}")
        
        return FileUploadResponse(**file_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

@router.get("/import/preview/{temp_id}", response_model=DataPreview, summary="获取数据预览")
async def get_data_preview(temp_id: str = Path(..., description="临时文件标识"), db: Session = Depends(get_db)):
    """
    获取上传文件的数据预览和结构信息
    """
    try:
        # 更新数据库状态
        DataImportService.update_import_record(
            db, temp_id, 
            DataImportRecordUpdate(
                import_status=ImportStatusEnum.PARSING,
                progress_percentage=20.0
            )
        )
        
        # 检查临时文件是否存在
        if temp_id not in TEMP_FILES_CACHE:
            raise HTTPException(status_code=404, detail="临时文件不存在")
            
        file_info = TEMP_FILES_CACHE[temp_id]
        file_path = file_info["file_path"]
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件已被删除")
            
        # 根据文件类型进行预览
        if file_info["file_type"] == FileType.CSV:
            preview_data = parse_csv_preview(file_path, temp_id)
        elif file_info["file_type"] == FileType.CNV:
            preview_data = parse_cnv_preview(file_path, temp_id)
        else:
            # 其他文件类型的预览功能后续实现
            raise HTTPException(status_code=501, detail=f"暂不支持 {file_info['file_type']} 格式的预览")
        
        # 更新数据库记录
        DataImportService.update_import_record(
            db, temp_id,
            DataImportRecordUpdate(
                import_status=ImportStatusEnum.PARSED,
                progress_percentage=30.0,
                parse_config=preview_data["parsing_config"],
                column_count=preview_data["column_count"],
                row_count=preview_data["row_count"]
            )
        )
        
        # 创建解析操作记录
        db_record = DataImportService.get_import_record(db, temp_id)
        if db_record:
            file_type_name = file_info["file_type"].upper() if hasattr(file_info["file_type"], 'upper') else str(file_info["file_type"]).upper()
            DataImportService.create_file_operation(
                db, db_record.id, "parse", "completed",
                input_path=file_path,
                success=True,
                operation_log=f"{file_type_name}文件解析完成，共{preview_data['row_count']}行{preview_data['column_count']}列",
                operation_metadata={"parsing_config": preview_data["parsing_config"]}
            )
            
        return DataPreview(**preview_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取数据预览失败: {str(e)}", exc_info=True)
        # 更新错误状态
        try:
            DataImportService.update_import_record(
                db, temp_id,
                DataImportRecordUpdate(
                    import_status=ImportStatusEnum.FAILED,
                    error_message=f"数据预览失败: {str(e)}"
                )
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=f"获取数据预览失败: {str(e)}")

@router.get("/import/metadata/{temp_id}", summary="获取元数据配置")
async def get_metadata_config(temp_id: str = Path(..., description="临时文件标识"), db: Session = Depends(get_db)):
    """
    获取文件的元数据配置，包括智能建议的CF标准属性
    """
    try:
        # 检查临时文件是否存在
        if temp_id not in TEMP_FILES_CACHE:
            raise HTTPException(status_code=404, detail="临时文件不存在")
            
        # 首先获取数据预览（包含变量建议）
        preview_data = await get_data_preview(temp_id, db)
        
        # 构建变量属性配置
        variables = {}
        coordinate_variables = {}
        
        for col in preview_data.columns:
            var_attr = {
                "standard_name": col.suggested_cf_name,
                "long_name": col.name,
                "units": col.suggested_units,
                "description": f"Variable: {col.name}"
            }
            
            # 如果是坐标变量，特殊处理
            if col.suggested_cf_name in ["time", "latitude", "longitude", "depth"]:
                coordinate_variables[col.suggested_cf_name] = col.name
                
            variables[col.name] = var_attr
            
        # 生成全局属性建议
        file_info = TEMP_FILES_CACHE[temp_id]
        
        # 获取用户偏好设置
        user_preference = DataImportService.get_user_preference(db, "default")
        default_attrs = user_preference.default_global_attributes if user_preference else {}
        
        global_attributes = {
            "title": f"Imported data from {file_info['filename']}",
            "institution": default_attrs.get("institution", "Ocean Environment System"),
            "source": f"File import: {file_info['filename']}",
            "history": f"Imported on {datetime.now().isoformat()}",
            "summary": f"Data imported from {file_info['file_type']} file",
            "creator_name": default_attrs.get("creator_name", "Ocean Environment System User"),
            "creator_institution": default_attrs.get("creator_institution", "Ocean Environment System")
        }
        
        metadata_config = {
            "temp_id": temp_id,
            "variables": variables,
            "global_attributes": global_attributes,
            "coordinate_variables": coordinate_variables
        }
        
        # 更新数据库记录
        DataImportService.update_import_record(
            db, temp_id,
            DataImportRecordUpdate(metadata_config=metadata_config)
        )
        
        return metadata_config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取元数据配置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取元数据配置失败: {str(e)}")

@router.put("/import/metadata/{temp_id}", summary="更新元数据配置")
async def update_metadata_config(
    temp_id: str = Path(..., description="临时文件标识"),
    metadata_config: MetadataConfig = None,
    db: Session = Depends(get_db)
):
    """
    更新文件的元数据配置
    """
    try:
        # 检查临时文件是否存在
        if temp_id not in TEMP_FILES_CACHE:
            raise HTTPException(status_code=404, detail="临时文件不存在")
            
        # 更新缓存中的元数据配置
        TEMP_FILES_CACHE[temp_id]["metadata_config"] = metadata_config.dict()
        
        # 更新数据库记录
        DataImportService.update_import_record(
            db, temp_id,
            DataImportRecordUpdate(metadata_config=metadata_config.dict())
        )
        
        logger.info(f"元数据配置已更新: temp_id={temp_id}")
        
        return {"message": "元数据配置更新成功", "temp_id": temp_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新元数据配置失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新元数据配置失败: {str(e)}")

@router.post("/import/validate/{temp_id}", response_model=ValidationResult, summary="验证数据")
async def validate_data(temp_id: str = Path(..., description="临时文件标识"), db: Session = Depends(get_db)):
    """
    验证数据是否符合CF Convention标准
    """
    try:
        # 更新状态
        DataImportService.update_import_record(
            db, temp_id,
            DataImportRecordUpdate(
                import_status=ImportStatusEnum.VALIDATING,
                progress_percentage=50.0
            )
        )
        
        # 检查临时文件是否存在
        if temp_id not in TEMP_FILES_CACHE:
            raise HTTPException(status_code=404, detail="临时文件不存在")
            
        file_info = TEMP_FILES_CACHE[temp_id]
        
        # 获取元数据配置
        metadata_config = file_info.get("metadata_config", {})
        
        # 简单的验证逻辑（后续可扩展为更完整的CF验证）
        issues = []
        error_count = 0
        warning_count = 0
        info_count = 0
        
        # 获取数据库记录
        db_record = DataImportService.get_import_record(db, temp_id)
        
        # 检查必需的全局属性
        global_attrs = metadata_config.get("global_attributes", {})
        required_attrs = ["title", "institution", "source", "history"]
        
        for attr in required_attrs:
            if not global_attrs.get(attr):
                issue_data = {
                    "level": "warning",
                    "code": f"MISSING_GLOBAL_ATTR_{attr.upper()}",
                    "message": f"缺少推荐的全局属性: {attr}",
                    "location": "global_attributes",
                    "suggestion": f"建议添加 {attr} 属性"
                }
                issues.append(issue_data)
                warning_count += 1
                
                # 创建验证问题记录
                if db_record:
                    DataImportService.create_validation_issue(
                        db, db_record.id,
                        ValidationLevelEnum.WARNING,
                        f"MISSING_GLOBAL_ATTR_{attr.upper()}",
                        f"缺少推荐的全局属性: {attr}",
                        location="global_attributes",
                        suggestion=f"建议添加 {attr} 属性",
                        auto_fixable=True
                    )
                
        # 检查变量属性
        variables = metadata_config.get("variables", {})
        for var_name, var_attrs in variables.items():
            if not var_attrs.get("units"):
                issue_data = {
                    "level": "warning", 
                    "code": "MISSING_UNITS",
                    "message": f"变量 {var_name} 缺少单位属性",
                    "location": f"variables.{var_name}",
                    "suggestion": "建议为所有变量指定单位"
                }
                issues.append(issue_data)
                warning_count += 1
                
                # 创建验证问题记录
                if db_record:
                    DataImportService.create_validation_issue(
                        db, db_record.id,
                        ValidationLevelEnum.WARNING,
                        "MISSING_UNITS",
                        f"变量 {var_name} 缺少单位属性",
                        location=f"variables.{var_name}",
                        suggestion="建议为所有变量指定单位",
                        auto_fixable=True
                    )
                
            if not var_attrs.get("standard_name"):
                issue_data = {
                    "level": "info",
                    "code": "MISSING_STANDARD_NAME", 
                    "message": f"变量 {var_name} 缺少CF标准名称",
                    "location": f"variables.{var_name}",
                    "suggestion": "建议使用CF标准变量名"
                }
                issues.append(issue_data)
                info_count += 1
                
                # 创建验证问题记录
                if db_record:
                    DataImportService.create_validation_issue(
                        db, db_record.id,
                        ValidationLevelEnum.INFO,
                        "MISSING_STANDARD_NAME",
                        f"变量 {var_name} 缺少CF标准名称",
                        location=f"variables.{var_name}",
                        suggestion="建议使用CF标准变量名",
                        auto_fixable=True
                    )
                
        # 计算合规性评分
        total_checks = len(required_attrs) + len(variables) * 2  # 简化的检查项数量
        passed_checks = total_checks - len(issues)
        compliance_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 100
        
        # 判断是否通过验证（无错误即为通过）
        is_valid = error_count == 0
        
        result = {
            "temp_id": temp_id,
            "is_valid": is_valid,
            "cf_version": "CF-1.8",
            "total_issues": len(issues),
            "error_count": error_count,
            "warning_count": warning_count, 
            "info_count": info_count,
            "issues": issues,
            "compliance_score": compliance_score
        }
        
        # 更新数据库记录
        DataImportService.update_import_record(
            db, temp_id,
            DataImportRecordUpdate(
                import_status=ImportStatusEnum.VALIDATED,
                progress_percentage=70.0,
                validation_result=result,
                is_cf_compliant=is_valid,
                compliance_score=compliance_score
            )
        )
        
        # 创建验证操作记录
        if db_record:
            DataImportService.create_file_operation(
                db, db_record.id, "validate", "completed",
                success=True,
                operation_log=f"CF验证完成，合规性评分: {compliance_score:.1f}%",
                operation_metadata={"validation_result": result}
            )
        
        logger.info(f"数据验证完成: temp_id={temp_id}, is_valid={is_valid}, score={compliance_score:.1f}")
        
        return ValidationResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"数据验证失败: {str(e)}", exc_info=True)
        # 更新错误状态
        try:
            DataImportService.update_import_record(
                db, temp_id,
                DataImportRecordUpdate(
                    import_status=ImportStatusEnum.FAILED,
                    error_message=f"数据验证失败: {str(e)}"
                )
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=f"数据验证失败: {str(e)}")

@router.post("/import/convert/{temp_id}", response_model=ConversionResult, summary="转换为NetCDF")
async def convert_to_netcdf(temp_id: str = Path(..., description="临时文件标识"), db: Session = Depends(get_db)):
    """
    将数据文件转换为符合CF Convention的NetCDF格式
    """
    try:
        # 更新状态
        DataImportService.update_import_record(
            db, temp_id,
            DataImportRecordUpdate(
                import_status=ImportStatusEnum.CONVERTING,
                progress_percentage=80.0
            )
        )
        
        # 从数据库获取导入记录
        db_record = DataImportService.get_import_record(db, temp_id)
        if not db_record:
            raise HTTPException(status_code=404, detail="导入记录不存在")
        
        file_path = db_record.upload_path
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="源文件不存在")
        
        # 检查元数据配置（从数据库获取）
        metadata_config = db_record.metadata_config
        if not metadata_config:
            raise HTTPException(status_code=400, detail="请先配置元数据")
            
        # 准备输出路径
        output_dir = os.path.join(os.getcwd(), "docker", "thredds", "data", "oceanenv", "standard")
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = f"{temp_id}_{db_record.original_filename.rsplit('.', 1)[0]}_cf.nc"
        output_path = os.path.join(output_dir, output_filename)
        
        start_time = time.time()
        
        # 根据文件类型进行转换
        if db_record.file_type == DBFileTypeEnum.CSV:
            await convert_csv_to_netcdf(file_path, output_path, metadata_config)
        elif db_record.file_type == DBFileTypeEnum.CNV:
            await convert_cnv_to_netcdf(file_path, output_path, metadata_config)
        else:
            raise HTTPException(status_code=501, detail=f"暂不支持 {db_record.file_type} 格式的转换")
            
        processing_time = time.time() - start_time
        
        # 检查输出文件
        if not os.path.exists(output_path):
            raise HTTPException(status_code=500, detail="NetCDF文件生成失败")
            
        file_size = os.path.getsize(output_path)
        
        # 生成访问URL
        relative_path = os.path.relpath(output_path, os.path.join(os.getcwd(),  "docker", "thredds", "data"))
        tds_url = f"{THREDDS_SERVER_URL}/thredds/fileServer/{relative_path}"
        opendap_url = f"{THREDDS_SERVER_URL}/thredds/dodsC/{relative_path}"
        
        result = {
            "temp_id": temp_id,
            "success": True,
            "output_path": output_path,
            "tds_url": tds_url,
            "opendap_url": opendap_url,
            "file_size": file_size,
            "processing_time": processing_time,
            "message": "NetCDF文件转换成功"
        }
        
        # 更新数据库记录
        DataImportService.update_import_record(
            db, temp_id,
            DataImportRecordUpdate(
                import_status=ImportStatusEnum.COMPLETED,
                progress_percentage=100.0,
                output_file_path=output_path,
                tds_url=tds_url,
                opendap_url=opendap_url,
                conversion_time=processing_time
            )
        )
        
        # 提取并保存NetCDF元数据到netcdf_metadata表
        try:
            from app.services.metadata_extractor import MetadataExtractor
            
            metadata_extractor = MetadataExtractor()
            
            # 提取NetCDF文件元数据
            netcdf_metadata = metadata_extractor.extract_metadata(
                output_path, 
                processing_status="standard"
            )
            
            # 关联到导入记录
            netcdf_metadata["import_record_id"] = db_record.id
            
            # 保存到数据库
            metadata_record = metadata_extractor.save_metadata_to_db(
                netcdf_metadata, 
                db, 
                force_update=True
            )
            
            logger.info(f"NetCDF元数据已保存到数据库: metadata_id={metadata_record.id}, file={output_path}")
            
            # 在返回结果中添加元数据记录信息
            result["metadata_record_id"] = metadata_record.id
            result["metadata_extracted"] = True
            
        except Exception as e:
            logger.warning(f"NetCDF元数据提取失败，但转换已成功: {str(e)}")
            result["metadata_extracted"] = False
            result["metadata_error"] = str(e)
        
        # 创建转换操作记录
        DataImportService.create_file_operation(
            db, db_record.id, "convert", "completed",
            input_path=file_path,
            output_path=output_path,
            success=True,
            operation_log=f"NetCDF转换完成，文件大小: {file_size} 字节",
            operation_metadata={"conversion_result": result}
        )
        
        logger.info(f"NetCDF转换成功: temp_id={temp_id}, output={output_path}")
        
        # 清理临时文件缓存（如果存在）
        try:
            if temp_id in TEMP_FILES_CACHE:
                del TEMP_FILES_CACHE[temp_id]
        except:
            pass
            
        return ConversionResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"NetCDF转换失败: {str(e)}", exc_info=True)
        # 更新错误状态
        try:
            DataImportService.update_import_record(
                db, temp_id,
                DataImportRecordUpdate(
                    import_status=ImportStatusEnum.FAILED,
                    error_message=f"NetCDF转换失败: {str(e)}"
                )
            )
        except:
            pass
        raise HTTPException(status_code=500, detail=f"NetCDF转换失败: {str(e)}")

async def convert_csv_to_netcdf(csv_path: str, output_path: str, metadata_config: Dict[str, Any]):
    """
    将CSV文件转换为NetCDF格式
    """
    import pandas as pd
    import xarray as xr
    import numpy as np
    
    try:
        # 读取CSV数据
        encoding = detect_file_encoding(csv_path)
        df = pd.read_csv(csv_path, encoding=encoding)
        
        # 获取配置
        variables_config = metadata_config.get("variables", {})
        global_attrs = metadata_config.get("global_attributes", {})
        coord_vars = metadata_config.get("coordinate_variables", {})
        
        # 创建xarray数据集
        data_vars = {}
        coords = {}
        
        for col in df.columns:
            var_config = variables_config.get(col, {})
            data = df[col].values
            
            # 处理缺失值
            if data.dtype == 'object':
                # 尝试转换为数值类型
                try:
                    data = pd.to_numeric(data, errors='coerce').values
                except:
                    pass
                    
            # 如果是坐标变量
            if col in coord_vars.values():
                coords[col] = data
            else:
                # 创建数据变量的属性
                attrs = {}
                if var_config.get("standard_name"):
                    attrs["standard_name"] = var_config["standard_name"]
                if var_config.get("long_name"):
                    attrs["long_name"] = var_config["long_name"]
                if var_config.get("units"):
                    attrs["units"] = var_config["units"]
                if var_config.get("description"):
                    attrs["description"] = var_config["description"]
                    
                data_vars[col] = (["index"], data, attrs)
                
        # 创建数据集
        ds = xr.Dataset(data_vars, coords=coords)
        
        # 添加全局属性
        for attr, value in global_attrs.items():
            if value:
                ds.attrs[attr] = value
                
        # 添加CF Convention相关属性
        ds.attrs["Conventions"] = "CF-1.8"
        ds.attrs["featureType"] = "timeSeries"  # 默认类型，可根据实际数据调整
        
        # 保存为NetCDF文件
        ds.to_netcdf(output_path, format='NETCDF4', engine='netcdf4')
        ds.close()
        
        logger.info(f"CSV转NetCDF完成: {csv_path} -> {output_path}")
        
    except Exception as e:
        logger.error(f"CSV转NetCDF失败: {str(e)}", exc_info=True)
        raise

async def convert_cnv_to_netcdf(cnv_path: str, output_path: str, metadata_config: Dict[str, Any]):
    """
    将CNV文件转换为NetCDF格式
    """
    import pandas as pd
    import xarray as xr
    import numpy as np
    
    try:
        # 读取CNV数据
        encoding = detect_file_encoding(cnv_path)
        df = pd.read_csv(cnv_path, encoding=encoding)
        
        # 获取配置
        variables_config = metadata_config.get("variables", {})
        global_attrs = metadata_config.get("global_attributes", {})
        coord_vars = metadata_config.get("coordinate_variables", {})
        
        # 创建xarray数据集
        data_vars = {}
        coords = {}
        
        for col in df.columns:
            var_config = variables_config.get(col, {})
            data = df[col].values
            
            # 处理缺失值
            if data.dtype == 'object':
                # 尝试转换为数值类型
                try:
                    data = pd.to_numeric(data, errors='coerce').values
                except:
                    pass
                    
            # 如果是坐标变量
            if col in coord_vars.values():
                coords[col] = data
            else:
                # 创建数据变量的属性
                attrs = {}
                if var_config.get("standard_name"):
                    attrs["standard_name"] = var_config["standard_name"]
                if var_config.get("long_name"):
                    attrs["long_name"] = var_config["long_name"]
                if var_config.get("units"):
                    attrs["units"] = var_config["units"]
                if var_config.get("description"):
                    attrs["description"] = var_config["description"]
                    
                data_vars[col] = (["index"], data, attrs)
                
        # 创建数据集
        ds = xr.Dataset(data_vars, coords=coords)
        
        # 添加全局属性
        for attr, value in global_attrs.items():
            if value:
                ds.attrs[attr] = value
                
        # 添加CF Convention相关属性
        ds.attrs["Conventions"] = "CF-1.8"
        ds.attrs["featureType"] = "timeSeries"  # 默认类型，可根据实际数据调整
        
        # 保存为NetCDF文件
        ds.to_netcdf(output_path, format='NETCDF4', engine='netcdf4')
        ds.close()
        
        logger.info(f"CNV转NetCDF完成: {cnv_path} -> {output_path}")
        
    except Exception as e:
        logger.error(f"CNV转NetCDF失败: {str(e)}", exc_info=True)
        raise