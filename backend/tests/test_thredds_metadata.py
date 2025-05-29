#!/usr/bin/env python3
"""
OceanEnvSystem - 测试Thredds元数据API
"""

import requests
import json
import sys
from urllib.parse import urlencode

# API基础URL
API_BASE = "http://localhost:8000/api/v1"

def test_thredds_metadata_api():
    """测试Thredds元数据API"""
    print("===== 测试Thredds元数据API =====")
    
    # 设置一个示例Thredds URL - 实际使用时需要替换为真实的URL
    thredds_url = "http://localhost:8080/thredds/dodsC/oceanenv/model/test_model.nc"
    
    # 构建API请求
    endpoint = f"{API_BASE}/data/thredds/metadata"
    params = {"url": thredds_url}
    
    print(f"请求URL: {endpoint}?{urlencode(params)}")
    print(f"Thredds数据URL: {thredds_url}")
    
    try:
        response = requests.get(endpoint, params=params)
        
        if response.status_code == 200:
            data = response.json()
            print(f"状态: 成功 ({response.status_code})")
            print("收到元数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
            
            # 分析返回的元数据
            if "variables" in data:
                print(f"\n变量数量: {len(data['variables'])}")
                if data['variables']:
                    print(f"示例变量: {', '.join(data['variables'][:5])}")
            
            if "dims" in data:
                print(f"\n维度: {data['dims']}")
            
            if "coordinate_ranges" in data:
                print(f"\n坐标范围信息:")
                for coord, info in data["coordinate_ranges"].items():
                    print(f"  - {coord}: {info}")
        else:
            print(f"状态: 失败 ({response.status_code})")
            print(f"错误信息: {response.text}")
    except Exception as e:
        print(f"请求出错: {str(e)}")
    
    print("-" * 50)

if __name__ == "__main__":
    print("注意: 此测试需要先启动后端服务(uvicorn app.main:app --reload)")
    print("同时需要确保Thredds服务器正在运行且可以访问")
    
    confirmation = input("是否继续测试？(y/n): ")
    if confirmation.lower() != "y":
        print("测试已取消")
        sys.exit(0)
    
    test_thredds_metadata_api()
    print("\n测试完成")
