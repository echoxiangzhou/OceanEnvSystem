#!/usr/bin/env python3
"""
OceanEnvSystem - 数据访问服务测试脚本
用于快速测试数据服务功能
"""

import os
import sys
from pathlib import Path
import shutil

# 添加项目根目录到路径
BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.append(str(BASE_DIR))

from app.services.data_service import DataService, PROCESSED_DATA_ROOT, THREDDS_DATA_ROOT

def ensure_test_data():
    """确保测试数据存在于指定目录中"""
    # 创建测试数据目录
    model_dir = os.path.join(THREDDS_DATA_ROOT, "model")
    os.makedirs(model_dir, exist_ok=True)
    
    # 创建一个测试文件在model目录中
    test_file = os.path.join(model_dir, "test_model.nc.txt")
    with open(test_file, "w") as f:
        f.write("This is a test file in the model directory.\n")
        f.write("It mimics a NetCDF file for testing purposes.\n")
    
    print(f"测试文件创建完成: {test_file}")
    return test_file

def test_data_service():
    """测试数据服务基本功能"""
    print("===== 测试数据服务 =====")
    print(f"PROCESSED_DATA_ROOT: {PROCESSED_DATA_ROOT}")
    print(f"THREDDS_DATA_ROOT: {THREDDS_DATA_ROOT}")
    
    # 确保测试数据存在
    test_file = ensure_test_data()
    
    # 检查目录是否存在
    print(f"\nPROCESSED_DATA_ROOT 存在: {os.path.exists(PROCESSED_DATA_ROOT)}")
    print(f"THREDDS_DATA_ROOT 存在: {os.path.exists(THREDDS_DATA_ROOT)}")
    print(f"Model 目录存在: {os.path.exists(os.path.join(THREDDS_DATA_ROOT, 'model'))}")
    
    # 列出处理后的数据文件
    print("\n== 处理数据目录文件列表 ==")
    try:
        processed_files = DataService.get_processed_data_list()
        for file in processed_files[:10]:  # 限制显示条数
            print(f"- {file}")
        if len(processed_files) > 10:
            print(f"... 共{len(processed_files)}个文件")
        if not processed_files:
            print("没有找到文件")
    except Exception as e:
        print(f"获取处理数据文件列表出错: {e}")
    
    # 列出Thredds数据文件
    print("\n== Thredds数据目录文件列表 ==")
    try:
        thredds_files = DataService.get_thredds_data_list()
        for file in thredds_files[:15]:  # 限制显示条数
            print(f"- {file}")
        if len(thredds_files) > 15:
            print(f"... 共{len(thredds_files)}个文件")
        if not thredds_files:
            print("没有找到文件")
    except Exception as e:
        print(f"获取Thredds数据文件列表出错: {e}")
    
    # 特别检查model目录
    print("\n== 特别检查model目录 ==")
    model_files = DataService.list_files(os.path.join(THREDDS_DATA_ROOT, "model"))
    if model_files:
        print(f"Model目录文件列表:")
        for file in model_files:
            print(f"- {file}")
        
        # 检查测试文件是否在完整列表中
        test_file_rel = os.path.relpath(test_file, THREDDS_DATA_ROOT)
        found = any(file == test_file_rel for file in thredds_files)
        print(f"\n测试文件 {test_file_rel} 在完整列表中: {found}")
    else:
        print("Model目录中没有文件")
    
    # 手动递归检查目录结构
    print("\n== 递归目录结构检查 ==")
    _recursive_dir_check(THREDDS_DATA_ROOT, "", 0)

def _recursive_dir_check(dir_path, prefix, level):
    """递归检查目录结构并打印树状图"""
    if level > 5:  # 限制递归深度
        print(f"{prefix}... (限制递归深度)")
        return
        
    try:
        items = os.listdir(dir_path)
        dirs = []
        files = []
        
        for item in items:
            if item.startswith('.'):
                continue
                
            full_path = os.path.join(dir_path, item)
            if os.path.isdir(full_path):
                dirs.append(item)
            else:
                files.append(item)
        
        # 先显示目录
        for d in sorted(dirs):
            print(f"{prefix}[{d}]/")
            _recursive_dir_check(
                os.path.join(dir_path, d), 
                prefix + "  ", 
                level + 1
            )
        
        # 再显示文件
        for f in sorted(files)[:5]:  # 限制每个目录显示礅5个文件
            print(f"{prefix}- {f}")
            
        if len(files) > 5:
            print(f"{prefix}... (还有 {len(files)-5} 个文件)")
    except Exception as e:
        print(f"{prefix}[ERROR] {str(e)}")

if __name__ == "__main__":
    test_data_service()
    print("\n测试完成")
