import json
import numpy as np
import pandas as pd
import datetime
from fastapi.encoders import jsonable_encoder

class NumpyEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理 NumPy 数据类型"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, (pd.Timestamp, datetime.datetime, datetime.date)):
            return obj.isoformat()
        if isinstance(obj, np.datetime64):
            return pd.Timestamp(obj).isoformat()
        if isinstance(obj, np.bool_):
            return bool(obj)
        # 处理复数类型
        if isinstance(obj, np.complex_):
            return str(obj)
        if isinstance(obj, (np.bytes_, np.string_)):
            return str(obj, 'utf-8') if isinstance(obj, np.bytes_) else str(obj)
        return super().default(obj)

def custom_jsonable_encoder(obj, **kwargs):
    """增强版的 jsonable_encoder，处理 NumPy 类型"""
    # 预处理 NumPy 类型
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {k: custom_jsonable_encoder(v, **kwargs) for k, v in obj.items()}
    if isinstance(obj, list):
        return [custom_jsonable_encoder(i, **kwargs) for i in obj]
    if isinstance(obj, (pd.Timestamp, datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, np.datetime64):
        return pd.Timestamp(obj).isoformat()
    
    # 对于其他类型，尝试使用标准 jsonable_encoder
    try:
        return jsonable_encoder(obj, **kwargs)
    except Exception:
        # 如果 jsonable_encoder 失败，尝试使用 NumpyEncoder
        return json.loads(json.dumps(obj, cls=NumpyEncoder))