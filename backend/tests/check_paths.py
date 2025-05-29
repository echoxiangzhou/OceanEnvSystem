#!/usr/bin/env python3
"""
OceanEnvSystem - 路径检查工具
检查数据目录路径和文件是否存在
"""

import os
import sys
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent.parent.absolute()
print(f"项目根目录 (BASE_DIR): {BASE_DIR}")

# 数据目录定义
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data/processed")
THREDDS_DATA_PATH = os.path.join(BASE_DIR, "docker/thredds/data/oceanenv")

# 检查目录
print("\n== 检查目录是否存在 ==")
print(f"处理数据目录: {PROCESSED_DATA_PATH}")
print(f"  - 存在: {os.path.exists(PROCESSED_DATA_PATH)}")
print(f"  - 是目录: {os.path.isdir(PROCESSED_DATA_PATH) if os.path.exists(PROCESSED_DATA_PATH) else False}")

print(f"Thredds数据目录: {THREDDS_DATA_PATH}")
print(f"  - 存在: {os.path.exists(THREDDS_DATA_PATH)}")
print(f"  - 是目录: {os.path.isdir(THREDDS_DATA_PATH) if os.path.exists(THREDDS_DATA_PATH) else False}")

# 检查特定子目录
MODEL_PATH = os.path.join(THREDDS_DATA_PATH, "model")
print(f"\nModel目录: {MODEL_PATH}")
print(f"  - 存在: {os.path.exists(MODEL_PATH)}")
print(f"  - 是目录: {os.path.isdir(MODEL_PATH) if os.path.exists(MODEL_PATH) else False}")

# 列出目录内容
print("\n== 目录内容 ==")
if os.path.exists(PROCESSED_DATA_PATH) and os.path.isdir(PROCESSED_DATA_PATH):
    print(f"\n处理数据目录内容:")
    for item in os.listdir(PROCESSED_DATA_PATH):
        item_path = os.path.join(PROCESSED_DATA_PATH, item)
        type_str = "目录" if os.path.isdir(item_path) else "文件"
        print(f"  - {item} ({type_str})")

if os.path.exists(THREDDS_DATA_PATH) and os.path.isdir(THREDDS_DATA_PATH):
    print(f"\nThredds数据目录内容:")
    for item in os.listdir(THREDDS_DATA_PATH):
        item_path = os.path.join(THREDDS_DATA_PATH, item)
        type_str = "目录" if os.path.isdir(item_path) else "文件"
        print(f"  - {item} ({type_str})")

if os.path.exists(MODEL_PATH) and os.path.isdir(MODEL_PATH):
    print(f"\nModel目录内容:")
    for item in os.listdir(MODEL_PATH):
        item_path = os.path.join(MODEL_PATH, item)
        type_str = "目录" if os.path.isdir(item_path) else "文件"
        print(f"  - {item} ({type_str})")

# 递归遍历目录
def list_files_recursively(root, indent=0):
    """递归列出目录中的所有文件和子目录"""
    if not os.path.exists(root) or not os.path.isdir(root):
        print(f"{' ' * indent}ERROR: {root} 不存在或不是目录")
        return
        
    for item in sorted(os.listdir(root)):
        if item.startswith("."):  # 跳过隐藏文件
            continue
            
        item_path = os.path.join(root, item)
        if os.path.isdir(item_path):
            print(f"{' ' * indent}[{item}]/")
            list_files_recursively(item_path, indent + 2)
        else:
            print(f"{' ' * indent}- {item}")

print("\n== 递归文件列表 ==")
print("\nThredds数据目录递归列表:")
list_files_recursively(THREDDS_DATA_PATH)

print("\n处理数据目录递归列表:")
list_files_recursively(PROCESSED_DATA_PATH)

print("\n检查完成")
