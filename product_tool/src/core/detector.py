# -*- coding: utf-8 -*-
"""
列检测模块 - 智能识别Model/Name/Spec/Price列
"""
import pandas as pd
from typing import Dict, Optional

# 关键词配置
COLUMN_KEYWORDS = {
    'price': ['价格', 'price', 'rmb', '/pc', '元', '单件', '单价'],
    'spec': ['规格', 'spec', '参数', 'description', '描述', '型号'],
    'name': ['名称', 'name', '品名', 'product', '产品', '品'],
    'model': ['型号', 'model', 'item', '编号', 'no.', 'code', 'sku'],
}


def detect_column_by_keyword(col_name: str) -> Optional[str]:
    """
    根据列名关键词检测列类型
    
    Args:
        col_name: 列名 (str)
    
    Returns:
        str: 'price'/'spec'/'name'/'model' 或 None
    """
    col_name = str(col_name).lower()
    
    for col_type, keywords in COLUMN_KEYWORDS.items():
        if any(kw in col_name for kw in keywords):
            return col_type
    
    return None


def smart_detect_columns(df: pd.DataFrame) -> Dict[str, int]:
    """
    智能检测核心列
    
    检测逻辑:
    1. 遍历前15列,匹配关键词
    2. 每种类型只取第一个匹配
    3. 未匹配的使用回退位置
    
    Returns:
        dict: {'model': 0, 'name': 1, 'spec': 2, 'price': 3}
    """
    result = {'model': 0, 'name': None, 'spec': None, 'price': None}
    detected = set()
    
    # 关键词检测
    for col_idx in range(1, min(15, df.shape[1])):
        col_name = str(df.columns[col_idx]).lower()
        
        for col_type in ['price', 'spec', 'name']:
            if col_type in detected:
                continue
            
            keywords = COLUMN_KEYWORDS[col_type]
            if any(kw in col_name for kw in keywords):
                result[col_type] = col_idx
                detected.add(col_type)
                break
    
    # 回退位置
    if result['name'] is None and df.shape[1] > 1:
        result['name'] = 1
    if result['spec'] is None and df.shape[1] > 2:
        result['spec'] = 2
    if result['price'] is None and df.shape[1] > 3:
        result['price'] = 3
    
    return result


def validate_columns(df: pd.DataFrame, col_map: Dict[str, int]) -> Dict[str, float]:
    """
    验证列提取质量
    
    Returns:
        dict: {'model': rate, 'name': rate, 'spec': rate, 'price': rate}
    """
    result = {}
    total = len(df)
    
    if total == 0:
        return {'model': 0, 'name': 0, 'spec': 0, 'price': 0}
    
    for col_type, col_idx in col_map.items():
        if col_idx is not None and col_idx < df.shape[1]:
            non_null = df.iloc[:, col_idx].notna().sum()
            result[col_type] = non_null / total
        else:
            result[col_type] = 0
    
    return result