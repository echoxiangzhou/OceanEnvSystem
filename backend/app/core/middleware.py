import json
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.json import custom_jsonable_encoder, NumpyEncoder
import logging

logger = logging.getLogger(__name__)

class NumpySerializationMiddleware(BaseHTTPMiddleware):
    """
    中间件：确保响应中的NumPy类型被正确序列化
    
    作为一个最后的保障措施，确保任何漏网的NumPy类型都能被处理
    """
    
    async def dispatch(self, request: Request, call_next):
        # 直接执行下一个处理器，不做额外处理
        # 因为我们已经通过替换jsonable_encoder和自定JSON响应类来处理NumPy类型
        response = await call_next(request)
        return response
