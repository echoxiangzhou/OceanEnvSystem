from fastapi import APIRouter, HTTPException, Query
from app.services.data_client import OpendapClient
from app.services.data_service import DataService # Import DataService for enhanced metadata
from typing import List, Optional, Any, Dict
import os
import logging # Added logging
from app.core.json import custom_jsonable_encoder, NumpyEncoder  # 导入我们的NumPy序列化工具

router = APIRouter(
    prefix="/opendap",
    tags=["opendap-client"]
)

# Setup a logger for this router
logger = logging.getLogger(__name__)
# Ensure basicConfig is called, preferably in your main app setup, but can add here if not already done
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# TDS服务基础URL
TDS_BASE_URL = os.environ.get("THREDDS_SERVER_URL", "http://localhost:8080")
# OpendapClient uses dodsC path within its logic
client = OpendapClient(f"{TDS_BASE_URL}/thredds/dodsC")

@router.get("/open", summary="通过OPeNDAP打开远程数据集，返回变量名、维度和全局属性")
def open_dataset_info(dataset_path: str):
    logger.info(f"[/opendap/open] Request for dataset_path: {dataset_path}")
    try:
        full_opendap_url = f"{client.base_url}/{dataset_path.lstrip('/')}"
        logger.info(f"[/opendap/open] Attempting to open OPeNDAP URL: {full_opendap_url} using OpendapClient")
        
        ds = client.open_dataset(dataset_path) 
        info = {
            "variables": list(ds.variables),
            "dims": dict(ds.dims),
            "attrs": dict(ds.attrs)
        }
        ds.close()
        logger.info(f"[/opendap/open] Successfully opened and got info for {full_opendap_url}")
        
        # 使用我们的自定义编码器处理NumPy类型
        serialized_info = custom_jsonable_encoder(info)
        return serialized_info
    except Exception as e:
        logger.error(f"[/opendap/open] OPeNDAP access failed for {dataset_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OPeNDAP访问失败: {str(e)}")

@router.get("/metadata", summary="获取OPeNDAP数据集的增强元数据")
def get_enhanced_opendap_metadata(dataset_path: str = Query(..., description="数据集的相对路径，例如 model/hycom/data.nc")) -> Dict[str, Any]:
    """
    获取OPeNDAP数据集的增强元数据，包括变量详情、坐标范围等。
    此接口旨在由前端DataBrowser调用以获取列表项的详细信息。
    """
    logger.info(f"[/opendap/metadata] Request for dataset_path: {dataset_path}")
    if not dataset_path:
        logger.warning("[/opendap/metadata] dataset_path is empty.")
        raise HTTPException(status_code=400, detail="dataset_path cannot be empty")

    try:
        full_opendap_url = f"{client.base_url}/{dataset_path.lstrip('/')}" 
        logger.info(f"[/opendap/metadata] Constructed OPeNDAP URL: {full_opendap_url}")
        
        # 使用OpendapClient的新get_enhanced_metadata方法获取元数据
        try:
            metadata = client.get_enhanced_metadata(dataset_path)
            logger.info(f"[/opendap/metadata] Successfully got enhanced metadata for {full_opendap_url} using OpendapClient")
            # 使用我们的自定义编码器处理NumPy类型
            serialized_metadata = custom_jsonable_encoder(metadata)
            return serialized_metadata
        except Exception as client_error:
            logger.warning(f"[/opendap/metadata] Error using OpendapClient.get_enhanced_metadata for {full_opendap_url}: {client_error}")
            logger.warning("[/opendap/metadata] Falling back to DataService.extract_enhanced_metadata")
            # 如果新方法失败，回退到原有的方法
            metadata = DataService.extract_enhanced_metadata(full_opendap_url)
            # 使用我们的自定义编码器处理NumPy类型
            serialized_metadata = custom_jsonable_encoder(metadata)
            
        if isinstance(serialized_metadata, dict) and serialized_metadata.get("error"):
            logger.warning(f"[/opendap/metadata] Error returned from metadata extraction for {full_opendap_url}: {serialized_metadata.get('error')}")
        else:
            logger.info(f"[/opendap/metadata] Successfully extracted metadata for {full_opendap_url}")
            
        return serialized_metadata
    except HTTPException as http_exc:
        logger.error(f"[/opendap/metadata] HTTPException for {dataset_path}: {http_exc.detail}", exc_info=True)
        raise http_exc
    except Exception as e:
        logger.error(f"[/opendap/metadata] Unhandled exception processing {dataset_path}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OPeNDAP增强元数据获取失败: {str(e)}")