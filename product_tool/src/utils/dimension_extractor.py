# -*- coding: utf-8 -*-
"""尺寸结构化提取 — 从规格文本中提取 L×W×H / Dia×H 等尺寸信息"""

import re
from typing import Optional, Dict


# === 尺寸正则模式 ===

# 10×5×3cm, 100*50*30mm, 10 x 5 x 3 cm, 10cm×5cm×3cm
_PAT_LWH = re.compile(
    r'(?:L[:\s]*)?(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in|"|\'\')?\s*[*×xX]\s*'
    r'(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in|"|\'\')?\s*[*×xX]\s*'
    r'(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in|"|\'\')?',
    re.I
)

# Dia:10cm H:20cm / 直径10cm 高20cm / D10 H20cm
_PAT_DIA = re.compile(
    r'(?:Dia|D|直径|Ø)\s*[:\s]*(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?\s*'
    r'(?:[,\s]*H[:\s]*|[,，\s]*高\s*|[,，\s]*高度?\s*|[,，\s]*)\s*'
    r'(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?',
    re.I
)

# L:10 W:5 H:3 cm / Length:10 Width:5 Height:3
_PAT_LABEL = re.compile(
    r'(?:L|l[ength]*)[:\s]*(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?[,\s]*'
    r'(?:W|w[idth]*)[:\s]*(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?[,\s]*'
    r'(?:H|h[eight]*)[:\s]*(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?',
    re.I
)

# 单一尺寸: 10cm / 10 cm
_PAT_SINGLE = re.compile(
    r'^(?:size|尺寸|dimension)\s*[:\s]*(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?\s*$',
    re.I
)

# 简单两数: 10*10cm (square), 10×20cm (rectangle, assume L×W)
_PAT_2D = re.compile(
    r'^(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?\s*[*×xX]\s*'
    r'(\d+\.?\d*)\s*([c|m]m?|M|CM|MM|inch|in)?\s*$',
    re.I
)


def _normalize_unit(unit_match: Optional[str]) -> str:
    """标准化单位名称"""
    if not unit_match:
        return ''
    u = unit_match.lower().strip()
    unit_map = {
        'cm': 'cm', 'c': 'cm', 'm': 'mm', 'mm': 'mm',
        'inch': 'inch', 'in': 'inch', '"': 'inch', "''": 'inch',
    }
    return unit_map.get(u, u)


def _to_mm(value: float, unit: str) -> float:
    """统一转为 mm"""
    if unit == 'cm':
        return round(value * 10, 1)
    elif unit == 'inch':
        return round(value * 25.4, 1)
    return round(value, 1)  # already mm


def extract_dimensions(text: str, default_unit: str = 'mm') -> Dict:
    """
    从规格文本中提取结构化尺寸。
    
    返回:
        {
            'length': float,    # mm
            'width': float,     # mm
            'height': float,    # mm
            'diameter': float,  # mm
            'unit': str,        # 原始单位
            'raw': str,         # 原始匹配文本
            'found': bool       # 是否找到
        }
    """
    result = {
        'length': None, 'width': None, 'height': None,
        'diameter': None, 'unit': default_unit,
        'raw': '', 'found': False
    }
    
    if not text or not isinstance(text, str):
        return result
    
    t = text.strip()
    
    # 1. L×W×H 模式: "10×5×3cm"
    m = _PAT_LWH.search(t)
    if m:
        val1, u1, val2, u2, val3, u3 = m.groups()
        unit = _normalize_unit(u1 or u3) or default_unit
        result['length'] = _to_mm(float(val1), unit) if val1 else None
        result['width'] = _to_mm(float(val2), unit) if val2 else None
        result['height'] = _to_mm(float(val3), unit) if val3 else None
        result['unit'] = unit
        result['raw'] = m.group(0)
        result['found'] = True
        return result
    
    # 2. Dia×H 模式: "Dia:10cm H:20cm"
    m = _PAT_DIA.search(t)
    if m:
        d_val, d_u, h_val, h_u = m.groups()
        unit = _normalize_unit(d_u or h_u) or default_unit
        result['diameter'] = _to_mm(float(d_val), unit) if d_val else None
        result['height'] = _to_mm(float(h_val), unit) if h_val else None
        result['unit'] = unit
        result['raw'] = m.group(0)
        result['found'] = True
        return result
    
    # 3. 带标签模式: "L:10 W:5 H:3 cm"
    m = _PAT_LABEL.search(t)
    if m:
        l_val, l_u, w_val, w_u, h_val, h_u = m.groups()
        unit = _normalize_unit(l_u or w_u or h_u) or default_unit
        result['length'] = _to_mm(float(l_val), unit) if l_val else None
        result['width'] = _to_mm(float(w_val), unit) if w_val else None
        result['height'] = _to_mm(float(h_val), unit) if h_val else None
        result['unit'] = unit
        result['raw'] = m.group(0)
        result['found'] = True
        return result
    
    # 4. 简单两数: "10*10cm" (square)
    m = _PAT_2D.search(t)
    if m:
        val1, u1, val2, u2 = m.groups()
        unit = _normalize_unit(u1 or u2) or default_unit
        result['length'] = _to_mm(float(val1), unit) if val1 else None
        result['width'] = _to_mm(float(val2), unit) if val2 else None
        result['unit'] = unit
        result['raw'] = m.group(0)
        result['found'] = True
        return result
    
    return result


def enrich_products_with_dimensions(products: list) -> list:
    """为产品列表批量提取尺寸"""
    for p in products:
        if not isinstance(p, dict):
            continue
        # 优先从 spec_zh 提取
        spec = p.get('spec_zh', '') or p.get('spec', '') or ''
        dims = extract_dimensions(spec)
        if dims['found']:
            if dims['length'] is not None:
                p['length_mm'] = dims['length']
            if dims['width'] is not None:
                p['width_mm'] = dims['width']
            if dims['height'] is not None:
                p['height_mm'] = dims['height']
            if dims['diameter'] is not None:
                p['diameter_mm'] = dims['diameter']
            p['dimension_unit'] = dims['unit']
            p['dimension_raw'] = dims['raw']
    return products
