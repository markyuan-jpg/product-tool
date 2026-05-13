# -*- coding: utf-8 -*-
"""Auto categorizer - classify products by keywords"""
import json
import os
import pandas as pd
from typing import List, Dict, Optional

DEFAULT_CATEGORIES_FILE = 'categories.json'

DEFAULT_CATEGORIES = {
    'Electric Vehicle': ['motor', 'battery', 'controller', 'charger', 'e-bike', 'e-motorcycle', 'electric'],
    'Auto Parts': ['auto', 'car', 'wheel', 'tire', 'brake', 'vehicle'],
    'Medical': ['medical', 'syringe', 'mask', 'glove', 'injection', 'hospital'],
    'Chemicals': ['chemical', 'material', 'powder', 'liquid', 'acid', 'solvent'],
    'Electronics': ['electronic', 'chip', 'pcb', 'circuit', 'power supply', 'component'],
    'Office': ['office', 'paper', 'stationery', 'desk', 'supply'],
    'Other': [],
}


def load_categories(file_path: str = None) -> Dict[str, List[str]]:
    """Load category config from JSON file"""
    if not file_path:
        search_paths = [DEFAULT_CATEGORIES_FILE, 'categories.json']
        for p in search_paths:
            if os.path.exists(p):
                file_path = p
                break
    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'Other' not in data:
                    data['Other'] = []
                return data
        except Exception:
            pass
    return DEFAULT_CATEGORIES.copy()


def predict_category(text: str, categories: Dict[str, List[str]] = None, default: str = 'Other') -> str:
    """Predict category for text based on keyword matching"""
    if not text:
        return default
    text = str(text).lower()
    if categories is None:
        categories = load_categories()
    category_scores = []
    for category, keywords in categories.items():
        if not keywords:
            continue
        score = 0
        for kw in keywords:
            kw_lower = str(kw).lower()
            if kw_lower in text:
                score += len(kw_lower)
        if score > 0:
            category_scores.append((score, category))
    if category_scores:
        category_scores.sort(reverse=True)
        return category_scores[0][1]
    return default


def predict_category_multi(row: Dict, fields: List[str] = None, categories: Dict = None) -> str:
    """Multi-field classification - combine model, name, spec for matching"""
    if fields is None:
        fields = ['model', 'name_zh', 'spec_zh']
    texts = []
    for field in fields:
        val = row.get(field)
        if val:
            texts.append(str(val))
    combined_text = ' '.join(texts)
    return predict_category(combined_text, categories)


def add_category_column(df: pd.DataFrame, categories: Dict = None) -> pd.DataFrame:
    """Add category column to DataFrame"""
    if categories is None:
        categories = load_categories()
    df = df.copy()
    df['category'] = df.apply(
        lambda row: predict_category_multi(row.to_dict(), categories=categories),
        axis=1
    )
    return df


def categorize_data(data: List[Dict], text_field: str = 'name_zh', categories: Dict = None) -> List[Dict]:
    """Categorize a list of product dicts"""
    if categories is None:
        categories = load_categories()
    result = []
    for item in data:
        text = item.get(text_field, '')
        for field in ['model', 'name_zh', 'spec_zh']:
            val = item.get(field)
            if val:
                text = f"{text} {val}"
        category = predict_category(text, categories)
        item['category'] = category
        result.append(item)
    return result


def get_category_stats(data: List[Dict]) -> Dict[str, int]:
    """Get category distribution stats"""
    stats = {}
    for item in data:
        cat = item.get('category', '')
        stats[cat] = stats.get(cat, 0) + 1
    return stats


def filter_by_category(data: List[Dict], category: str) -> List[Dict]:
    """Filter data by category"""
    return [item for item in data if item.get('category') == category]


def sort_by_category(data: List[Dict], category_order: List[str] = None) -> List[Dict]:
    """Sort data by category order"""
    if category_order is None:
        category_order = list(DEFAULT_CATEGORIES.keys())
    order_map = {cat: idx for idx, cat in enumerate(category_order)}
    def sort_key(item):
        cat = item.get('category', '')
        return order_map.get(cat, 999)
    return sorted(data, key=sort_key)


def categorize_dataframe(df, text_field: str = 'name_zh'):
    """Categorize DataFrame rows"""
    return add_category_column(df)
