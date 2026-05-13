# -*- coding: utf-8 -*-
"""
自然语言筛选 - 简单规则筛选
"""
import re
from typing import List, Dict, Callable, Optional
import pandas as pd


class Filter:
    """筛选器基类"""
    def match(self, item: dict) -> bool:
        raise NotImplementedError


class PriceRangeFilter(Filter):
    """价格区间筛选"""
    def __init__(self, min_price: float = None, max_price: float = None):
        self.min_price = min_price
        self.max_price = max_price
    
    def match(self, item: dict) -> bool:
        price = item.get('price_rmb')
        if price is None:
            return False
        if self.min_price and price < self.min_price:
            return False
        if self.max_price and price > self.max_price:
            return False
        return True


class KeywordFilter(Filter):
    """关键词筛选"""
    def __init__(self, keywords: List[str], field: str = 'name_zh', include: bool = True):
        self.keywords = [k.lower() for k in keywords]
        self.field = field
        self.include = include
    
    def match(self, item: dict) -> bool:
        text = str(item.get(self.field, '')).lower()
        has_keyword = any(kw in text for kw in self.keywords)
        return has_keyword if self.include else not has_keyword


class CertificationFilter(Filter):
    """认证筛选"""
    def __init__(self, certs: List[str]):
        self.certs = [c.upper() for c in certs]
    
    def match(self, item: dict) -> bool:
        # 检查认证字段
        cert_text = str(item.get('cert', '')).upper()
        for cert in self.certs:
            if cert in cert_text:
                return True
        return False


class RegexFilter(Filter):
    """正则表达式筛选"""
    def __init__(self, pattern: str, field: str = 'spec_zh'):
        self.pattern = re.compile(pattern)
        self.field = field
    
    def match(self, item: dict) -> bool:
        text = str(item.get(self.field, ''))
        return bool(self.pattern.search(text))


class FilterChain:
    """筛选链"""
    def __init__(self):
        self.filters = []
    
    def add(self, filter_obj: Filter) -> 'FilterChain':
        self.filters.append(filter_obj)
        return self
    
    def apply(self, data: List[Dict]) -> List[Dict]:
        result = []
        for item in data:
            if all(f.match(item) for f in self.filters):
                result.append(item)
        return result


# 便捷函数
def filter_by_price(data: List[Dict], min_price: float = None, max_price: float = None) -> List[Dict]:
    """按价格筛选"""
    f = PriceRangeFilter(min_price, max_price)
    return [item for item in data if f.match(item)]


def filter_by_keyword(data: List[Dict], keywords: List[str], field: str = 'name_zh') -> List[Dict]:
    """按关键词筛选"""
    f = KeywordFilter(keywords, field)
    return [item for item in data if f.match(item)]


def filter_by_cert(data: List[Dict], certs: List[str]) -> List[Dict]:
    """按认证筛选"""
    f = CertificationFilter(certs)
    return [item for item in data if f.match(item)]


if __name__ == '__main__':
    # 测试
    data = [
        {'model': 'A1', 'name_zh': '手套', 'price_rmb': 10.0, 'spec_zh': 'L码'},
        {'model': 'A2', 'name_zh': '口罩', 'price_rmb': 5.0, 'spec_zh': 'M码'},
        {'model': 'A3', 'name_zh': '防护服', 'price_rmb': 50.0, 'spec_zh': 'XL码'},
    ]
    
    # 筛选10元以下
    result = filter_by_price(data, max_price=10)
    print(f"10元以下: {result}")
    
    # 关键词筛选
    result = filter_by_keyword(data, ['口', '罩'])
    print(f"口罩: {result}")