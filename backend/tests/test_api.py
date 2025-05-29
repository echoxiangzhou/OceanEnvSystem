#!/usr/bin/env python3
"""
OceanEnvSystem - API 验证脚本
测试API能否正确访问数据目录和文件
"""

import os
import sys
from pathlib import Path
import requests
import json
from urllib.parse import urljoin

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.append(str(BASE_DIR))

# 假设API服务器已启动
API_BASE_URL = "http://localhost:8000/api/v1"

def test_api():
    """测试API接口"""
    print("===== 测试API接口 =====")
    
    # 1. 测试获取数据列表
    print("\n== 测试获取数据列表 ==")
    
    # 兼容旧接口
    test_endpoint(f"{API_BASE_URL}/data/list", params={"ext": "nc"})
    
    # 新接口 - processed 目录
    test_endpoint(f"{API_BASE_URL}/data/list/processed")
    
    # 新接口 - thredds 目录
    test_endpoint(f"{API_BASE_URL}/data/list/thredds")
    
    # 2. 测试获取元数据
    print("\n== 测试获取元数据 ==")
    
    # 假设有一个示例文件
    sample_file = "examples/sample.nc.txt"
    
    # 测试获取元数据
    test_endpoint(f"{API_BASE_URL}/data/metadata/thredds", params={"relpath": sample_file})
    
    # 3. 测试文件下载接口
    print("\n== 测试文件下载接口 ==")
    test_download_endpoint(f"{API_BASE_URL}/data/download/thredds", params={"relpath": sample_file})

def test_endpoint(url, params=None):
    """测试GET接口"""
    print(f"测试接口: {url}")
    print(f"参数: {params}")
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            print(f"状态: 成功 (200)")
            print(f"数据类型: {type(data).__name__}")
            
            if isinstance(data, list):
                print(f"列表长度: {len(data)}")
                print(f"前3项: {data[:3]}")
            else:
                # 限制输出长度，避免过多数据
                print(f"部分数据: {json.dumps(data, indent=2, ensure_ascii=False)[:300]}...")
        else:
            print(f"状态: 失败 ({response.status_code})")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")
    
    print("-" * 50)

def test_download_endpoint(url, params=None):
    """测试文件下载接口"""
    print(f"测试下载接口: {url}")
    print(f"参数: {params}")
    
    try:
        response = requests.get(url, params=params, stream=True)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            content_length = response.headers.get('content-length', 'unknown')
            content_disposition = response.headers.get('content-disposition', '')
            
            print(f"状态: 成功 (200)")
            print(f"内容类型: {content_type}")
            print(f"内容长度: {content_length}")
            print(f"内容处置: {content_disposition}")
            
            # 读取部分内容
            content = response.content[:200]  # 只读取前200字节
            try:
                decoded = content.decode('utf-8')
                print(f"内容预览: {decoded[:100]}...")
            except:
                print(f"内容预览: {content[:50]}...")
        else:
            print(f"状态: 失败 ({response.status_code})")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")
    
    print("-" * 50)

if __name__ == "__main__":
    print("注意: 此测试需要先启动后端服务(uvicorn app.main:app --reload)")
    print("如果服务未启动或端口不是8000，请修改API_BASE_URL变量")
    input("按回车继续...")
    
    test_api()
    print("\n测试完成")
