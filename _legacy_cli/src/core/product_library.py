# -*- coding: utf-8 -*-
"""
Product Library Manager

产品库管理 - 跟踪历史产品价格和配置变化
"""
import os
import json
import datetime
import hashlib
import pandas as pd
from typing import Dict, List, Optional, Any


def generate_product_key(
    model: str,
    spec_dict: dict = None,
    key_params: List[str] = None,
) -> str:
    """
    根据型号和关键配置参数生成唯一标识
    
    Args:
        model: 产品型号
        spec_dict: 产品规格字典
        key_params: 关键配置参数列表
    
    Returns:
        唯一标识字符串 (MD5 哈希)
    """
    if key_params is None:
        key_params = [
            "电机功率", "Motor power", "功率", "Power",
            "电池", "Battery", "电池类型", "Battery type",
            "刹车", "Brake", "刹车类型",
            "控制器", "Controller",
            "版本", "Version", "配置", "Config",
        ]
    
    # 收集关键参数
    key_values = [str(model).strip()]
    
    if spec_dict and isinstance(spec_dict, dict):
        for param in key_params:
            if param in spec_dict:
                key_values.append(f"{param}={spec_dict[param]}")
    
    # 生成哈希
    key_string = "|".join(key_values)
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()[:12]


def load_library(library_path: str = "product_library.json") -> Dict[str, dict]:
    """
    读取产品库
    
    Args:
        library_path: 库文件路径
    
    Returns:
        产品字典 {product_key: product_info}
    """
    if not os.path.exists(library_path):
        return {}
    
    try:
        with open(library_path, 'r', encoding='utf-8') as f:
            library = json.load(f)
        print(f"  已加载产品库: {len(library)} 个产品")
        return library
    except Exception as e:
        print(f"  警告: 无法加载产品库: {e}")
        return {}


def save_library(
    library: Dict[str, dict],
    library_path: str = "product_library.json",
) -> bool:
    """
    保存产品库
    
    Args:
        library: 产品字典
        library_path: 库文件路径
    
    Returns:
        是否成功
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(library_path) or ".", exist_ok=True)
        
        with open(library_path, 'w', encoding='utf-8') as f:
            json.dump(library, f, ensure_ascii=False, indent=2)
        
        print(f"  产品库已保存: {library_path} ({len(library)} 个产品)")
        return True
    except Exception as e:
        print(f"  错误: 无法保存产品库: {e}")
        return False


def get_product_info(
    row: pd.Series,
    key_params: List[str] = None,
) -> dict:
    """
    从 DataFrame 行提取产品信息
    
    Args:
        row: DataFrame 行
        key_params: 关键配置参数
    
    Returns:
        产品信息字典
    """
    model = row.get('model', '')
    spec_dict = row.get('spec_dict', {})
    
    if not isinstance(spec_dict, dict):
        spec_dict = {}
    
    return {
        'model': model,
        'name_zh': row.get('name_zh', ''),
        'spec_zh': row.get('spec_zh', ''),
        'spec_dict': spec_dict,
        'key': generate_product_key(model, spec_dict, key_params),
        'price_rmb': row.get('price_rmb'),
        'price_usd': row.get('price_usd'),
        'color': row.get('color'),
        'package': row.get('package'),
        'last_updated': datetime.datetime.now().isoformat(),
    }


def merge_with_library(
    new_df: pd.DataFrame,
    library: Dict[str, dict],
    key_params: List[str] = None,
    interactive: bool = True,
) -> tuple:
    """
    将新产品与产品库合并
    
    对于库中已存在的产品:
    - 比较价格、规格变化
    - 询问用户是否更新
    
    Args:
        new_df: 新产品 DataFrame
        library: 历史产品库
        key_params: 关键配置参数
        interactive: 是否交互模式
    
    Returns:
        (updated_df, updated_library)
    """
    import sys
    
    if key_params is None:
        key_params = [
            "电机功率", "Motor power", "功率", "Power",
            "电池", "Battery", "电池类型", "Battery type",
            "刹车", "Brake", "刹车类型",
            "控制器", "Controller",
            "版本", "Version", "配置", "Config",
        ]
    
    updated_library = library.copy()
    updated_df = new_df.copy()
    updated_df["_is_new"] = True
    updated_df["_price_changed"] = False
    updated_df["_price_history"] = None
    
    new_count = 0
    update_count = 0
    unchanged_count = 0
    
    for idx in new_df.index:
        product_info = get_product_info(new_df.loc[idx], key_params)
        product_key = product_info['key']
        
        if product_key in updated_library:
            # 产品已存在
            old_info = updated_library[product_key]
            
            # 比较价格
            old_price = old_info.get('price_usd', 0)
            new_price = product_info.get('price_usd', 0)
            
            if old_price != new_price:
                # 价格有变化
                if interactive and sys.stdin.isatty():
                    print(f"\n发现价格变化: {product_info['model']}")
                    print(f"  旧价格: ${old_price:.2f}")
                    print(f"  新价格: ${new_price:.2f}")
                    choice = input("  更新库中的价格? (y/n): ").strip().lower()
                    
                    if choice in ['y', 'yes', '是']:
                        updated_library[product_key] = product_info
                        update_count += 1
                        updated_df.loc[idx, "_price_changed"] = True
                else:
                    # 非交互模式 - 自动更新
                    updated_library[product_key] = product_info
                    update_count += 1
                    updated_df.loc[idx, "_price_changed"] = True
            else:
                unchanged_count += 1
            
            # 记录价格历史
            if old_price:
                price_history = old_info.get('price_history', [])
                if not isinstance(price_history, list):
                    price_history = []
                price_history.append({
                    'date': old_info.get('last_updated', ''),
                    'price': old_price,
                })
                updated_df.loc[idx, "_price_history"] = price_history
            
            updated_df.loc[idx, "_is_new"] = False
        else:
            # 新产品
            new_count += 1
            updated_library[product_key] = product_info
    
    # 统计信息
    print(f"\n产品库同步完成:")
    print(f"  新产品: {new_count}")
    print(f"  价格更新: {update_count}")
    print(f"  价格不变: {unchanged_count}")
    
    return updated_df, updated_library


def add_library_columns(
    df: pd.DataFrame,
    library: Dict[str, dict],
) -> pd.DataFrame:
    """
    从��品库添加历史信息到 DataFrame
    
    添加列:
    - last_price: 上次价格
    - price_change: 价格变化百分比
    - days_since_update: 距上次更新的天数
    
    Args:
        df: 产品 DataFrame
        library: 产品库
    
    Returns:
        添加了历史信息的 DataFrame
    """
    result = df.copy()
    
    # 初始化新列
    result["last_price"] = None
    result["price_change"] = None
    result["days_since_update"] = None
    
    for idx in result.index:
        product_info = get_product_info(result.loc[idx])
        product_key = product_info['key']
        
        if product_key in library:
            old_info = library[product_key]
            
            # 上次价格
            last_price = old_info.get('price_usd')
            if last_price:
                result.loc[idx, "last_price"] = last_price
                
                # 价格变化
                new_price = result.loc[idx, "price_usd"]
                if new_price and last_price:
                    change = (new_price - last_price) / last_price * 100
                    result.loc[idx, "price_change"] = round(change, 1)
            
            # 距上次更新天数
            last_updated = old_info.get('last_updated', '')
            if last_updated:
                try:
                    last_date = datetime.datetime.fromisoformat(last_updated)
                    days = (datetime.datetime.now() - last_date).days
                    result.loc[idx, "days_since_update"] = days
                except:
                    pass
    
    return result


# 默认列配置
LIBRARY_COLUMNS = [
    "model",
    "name_zh",
    "spec_zh",
    "key",
    "price_rmb",
    "price_usd",
    "color",
    "package",
    "last_updated",
]


if __name__ == "__main__":
    # Test
    test_df = pd.DataFrame([
        {"model": "S1", "name_zh": "电动滑板车 S1", "spec_dict": {"电机功率": "500W"}, "price_usd": 500},
        {"model": "M031", "name_zh": "电动自行车 M031", "spec_dict": {"电机功率": "800W"}, "price_usd": 800},
    ])
    
    test_library = {}
    
    # Test generate key
    for idx in test_df.index:
        key = generate_product_key(
            test_df.loc[idx, "model"],
            test_df.loc[idx, "spec_dict"]
        )
        print(f"Key for {test_df.loc[idx, 'model']}: {key}")
    
    # Test merge
    merged_df, merged_lib = merge_with_library(test_df, test_library, interactive=False)
    print(f"\nMerged library: {len(merged_lib)} products")