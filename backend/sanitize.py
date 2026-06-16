# -*- coding: utf-8 -*-
"""输入清洗 — 防止 XSS / 注入"""

import html
import re


def sanitize_text(val: str) -> str:
    """HTML 转义，防 XSS"""
    if not isinstance(val, str):
        return val
    return html.escape(val, quote=True)


def sanitize_number(val, default=0.0):
    """强制转为 float，失败返回 default"""
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def sanitize_product(prod: dict) -> dict:
    """清洗单个产品数据"""
    text_fields = ['model', 'name', 'name_zh', 'spec', 'spec_zh', 'description', 'category']
    for f in text_fields:
        if prod.get(f):
            prod[f] = sanitize_text(prod[f])

    num_fields = ['price', 'price_rmb', 'price_cny', 'price_usd', 'qty', 'moq']
    for f in num_fields:
        if prod.get(f):
            prod[f] = sanitize_number(prod[f])

    return prod


def sanitize_products(products: list) -> list:
    """清洗产品列表"""
    return [sanitize_product(p) for p in products if isinstance(p, dict)]
