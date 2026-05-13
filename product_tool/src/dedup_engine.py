# -*- coding: utf-8 -*-
"""
DedupEngine V1.0
DedupEngine V1.0"""
import re
import hashlib
import pandas as pd
import numpy as np
from difflib import SequenceMatcher
from collections import defaultdict


def _safe_float(val):
    """Dedup util"""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace(',', '').replace(' ', ''))
    except (ValueError, TypeError):
        return None


def normalize_for_hash(text: str) -> str:
    """Dedup util"""
    if not text:
        return ''
    s = str(text).lower().strip()
    s = s.replace('-', ':')
    s = s.replace(' ', '')
    s = re.sub(r'[\-_]', '', s)
    s = re.sub(r'\s+', '', s)
    return s


def normalize_spec(spec: str) -> str:
    """Normalize spec value"""
    if not spec:
        return ''
    s = str(spec).lower().strip()
    s = s.replace('-', ':')
    s = re.sub(r'\s+', '', s)
    s = re.sub(r'(mm|cm|m|kg|g)\b', lambda m: m.group(1).lower(), s)
    return s


def fuzzy_key(model: str) -> str:
    """Key normalization"""
    if not model:
        return ''
    s = str(model).lower().strip()
    s = re.sub(r'[\-_]', '', s)
    s = re.sub(r'\s+', '', s)
    return s


def normalized_key(model: str) -> str:
    """Dedup util"""
    if not model:
        return ''
    s = str(model).strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def spec_hash(spec: str) -> str:
    """Spec hash"""
    n = normalize_spec(spec)
    return hashlib.md5(n.encode()).hexdigest()[:8]


def price_cluster_key(price1, price2, threshold=0.20) -> str:
    """Dedup util"""
    try:
        p1 = float(price1) if price1 else 0
        p2 = float(price2) if price2 else 0
        if p1 == 0 or p2 == 0:
            return 'unknown'
        diff = abs(p1 - p2) / max(p1, p2)
        if diff > threshold:
            return 'version_split'
        return 'same_cluster'
    except Exception:
        return 'unknown'


def score_product(row) -> int:
    """Dedup util"""
    score = 0
    
    model = str(row.get('model', ''))
    spec = str(row.get('spec_zh', ''))
    
    if model and len(model) > 2:
        score += 1
    
    product_keywords = ['charger', 'battery', 'motor',
                    'power', 'kw', 'voltage', 'ev']
    if any(kw in spec.lower() for kw in product_keywords):
        score += 2
    
    noise_words = ['warning', 'note', 'remark', 'spec', 'parameter']
    for nw in noise_words:
        if nw in spec:
            score -= 1
            break
    
    return score


class DedupEngine:
    """Dedup Engine"""
    
    def __init__(self, price_threshold=0.20, score_threshold=0):
        self.price_threshold = price_threshold
        self.score_threshold = score_threshold
        self.stats = {}
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run dedup pipeline"""
        if df.empty:
            return df
        
        df = df.copy()
        
        self.stats['total_input'] = len(df)
        
        # Step 1: 
        df = self._filter_by_score(df)
        
        # Step 2: eys
        df = self._normalize_keys(df)
        
        # Step 3: 
        groups = self._fuzzy_group(df)
        
        # Step 4: 
        groups = self._detect_conflicts(groups)
        
        # Step 5: 
        merged = self._merge_groups(groups)
        
        # Step 6: 
        result = self._split_by_price(merged)
        
        # Step 7: 
        self._report(result)
        
        return result
    
    def _filter_by_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Dedup util"""
        df['dedup_score'] = df.apply(score_product, axis=1)
        
        discarded = df[df['dedup_score'] < self.score_threshold]
        if not discarded.empty:
            self.stats['discarded'] = discarded
        
        df = df[df['dedup_score'] >= self.score_threshold]
        return df
    
    def _normalize_keys(self, df: pd.DataFrame) -> pd.DataFrame:
        """Dedup util"""
        df['fuzzy_key'] = df['model'].apply(fuzzy_key)
        df['normalized_key'] = df['model'].apply(normalized_key)
        df['spec_hash'] = df['spec_zh'].apply(spec_hash)
        return df
    
    def _fuzzy_group(self, df: pd.DataFrame) -> dict:
        """Key normalization"""
        groups = defaultdict(list)
        
        for idx, row in df.iterrows():
            fk = row['fuzzy_key']
            nk = row['normalized_key']
            
            item = {
                'idx': idx,
                'model': row['model'],
                'normalized_key': nk,
                'spec_zh': row['spec_zh'],
                'spec_hash': row['spec_hash'],
                'price_rmb': row.get('price_rmb'),
                'source': row.get('_source_file') or row.get('_source', ''),
                '_image_path': row.get('_image_path', ''),
            }
            #  ()
            for k, v in row.items():
                if k not in ['model', 'normalized_key', 'fuzzy_key', 'spec_zh', 'spec_hash', 'price_rmb', 'source', 'dedup_score', '_source', '_image_path', 'image_path']:
                    item[k] = v
            groups[fk].append(item)
        
        return groups
    
    def _detect_conflicts(self, groups: dict) -> dict:
        """Step 4: Conflict detection"""
        clean_groups = {}
        
        for key, items in groups.items():
            if len(items) == 1:
                clean_groups[key] = items
                continue
            
            spec_hashes = set(item['spec_hash'] for item in items)
            prices = [_safe_float(item['price_rmb']) for item in items if item.get('price_rmb')]
            prices = [p for p in prices if p is not None]
            
            if len(spec_hashes) > 1:
                # 同一规格下价格差异 <5%
                prices_clean = [p for p in prices if p]
                if len(prices_clean) >= 2:
                    price_ratio = max(prices_clean) / min(prices_clean) if min(prices_clean) > 0 else 999
                    if price_ratio < 1.05:
                        # Same spec
                        for item in items:
                            item['dedup_conflict'] = ''
                        clean_groups[key] = items
                        continue
                for i, item in enumerate(items):
                    item['dedup_conflict'] = 'spec_mismatch'
                    item['dedup_group'] = "{}_{}".format(key, i)
                clean_groups[key] = items
            else:
                clean_groups[key] = items
        
        return clean_groups
    
    def _merge_groups(self, groups: dict) -> list:
        """Dedup util"""
        result = []
        
        for key, items in groups.items():
            #  _image_path
            extra_fields = {}
            # 
            for item in items:
                img = item.get('_image_path') or item.get('image_path', '')
                if img and not extra_fields.get('_image_path'):
                    extra_fields['_image_path'] = img
            
            # 
            for item in items:
                for k, v in item.items():
                    if k not in ['model', 'normalized_key', 'spec_zh', 'price_rmb', 'source', 'spec_hash', 'idx', 'dedup_conflict', 'dedup_group', '_image_path', 'image_path']:
                        if k not in extra_fields:
                            extra_fields[k] = v
            
            if len(items) == 1:
                item = items[0]
                row = {
                    'model': item['model'],
                    'normalized_key': item['normalized_key'],
                    'spec_zh': item['spec_zh'],
                    'price_rmb': item['price_rmb'],
                    '_source': item.get('source', ''),
                    'dedup_status': 'single'
                }
                row.update(extra_fields)
                result.append(row)
                continue
            
            has_mismatch = any(item.get('dedup_conflict') == 'spec_mismatch' for item in items)
            
            if has_mismatch:
                # 
                active_mismatches = [item for item in items if item.get('dedup_conflict') == 'spec_mismatch']
                if not active_mismatches:
                    pass
                else:
                    for item in active_mismatches:
                        row = {
                            'model': item['model'],
                            'normalized_key': item['normalized_key'],
                            'spec_zh': item['spec_zh'],
                            'price_rmb': item['price_rmb'],
                            '_source': item.get('source', ''),
                            'dedup_status': 'multi_spec'
                        }
                        row.update(extra_fields)
                        result.append(row)
                    continue
            
            models = [item['model'] for item in items if item['model']]
            best_model = max(models, key=len) if models else ''
            
            specs = [item['spec_zh'] for item in items if item['spec_zh']]
            best_spec = max(specs, key=len) if specs else ''
            
            prices = [_safe_float(item['price_rmb']) for item in items if item.get('price_rmb')]
            prices = [p for p in prices if p is not None]
            if prices and len(prices) > 1:
                avg_price = float(np.mean(prices))
                # 去掉 0 价格后再比较
                clean_prices = [p for p in prices if p != 0]
                max_p = max(clean_prices) if clean_prices else 0
                min_p = min(clean_prices) if clean_prices else 0
                if len(clean_prices) >= 2 and min_p > 0 and max_p / min_p > 1.2:  #  >20%
                    # 
                    for item in items:
                        row = {
                            'model': item['model'],
                            'normalized_key': item['normalized_key'],
                            'spec_zh': item['spec_zh'],
                            'price_rmb': item['price_rmb'],
                            '_source': item.get('source', ''),
                            'dedup_status': 'price_split'
                        }
                        row.update(extra_fields)
                        result.append(row)
                    continue
            elif prices:
                avg_price = float(np.mean(prices))
            else:
                avg_price = None
            
            sources = [item.get('source', '') for item in items if item.get('source')]
            source = ','.join(set(sources)) if sources else ''
            
            row = {
                'model': best_model,
                'normalized_key': items[0]['normalized_key'],
                'spec_zh': best_spec,
                'price_rmb': avg_price,
                '_source': source,
                'dedup_status': 'merged'
            }
            row.update(extra_fields)
            result.append(row)
        
        return result
    
    def _split_by_price(self, merged: list) -> pd.DataFrame:
        """Dedup util"""
        if not merged:
            return pd.DataFrame()
        
        df = pd.DataFrame(merged)
        
        if 'price_rmb' not in df.columns:
            return df
        
        df = df.sort_values('normalized_key')
        
        split_rows = []
        processed_groups = set()
        
        for idx, row in df.iterrows():
            normalized_key = row.get('normalized_key', '')
            if normalized_key in processed_groups:
                continue
            
            price = row.get('price_rmb')
            if price is None:
                split_rows.append(row)
                processed_groups.add(normalized_key)
                continue
            
            same_key_rows = df[df['normalized_key'] == normalized_key]
            prices = [p for p in same_key_rows['price_rmb'] if p]
            
            if len(prices) > 1 and prices:
                # 过滤无效价格后比较
                clean_prices = [p for p in prices if p is not None and p != 0]
                max_p = max(clean_prices) if clean_prices else 0
                min_p = min(clean_prices) if clean_prices else 0
                if len(clean_prices) >= 2 and min_p > 0 and max_p / min_p > (1 + self.price_threshold):
                    # ??
                    for _, item_row in same_key_rows.iterrows():
                        new_row = item_row.copy()
                        new_row['dedup_status'] = 'price_split'
                        split_rows.append(new_row)
                else:
                    split_rows.append(row)
            else:
                split_rows.append(row)
            
            processed_groups.add(normalized_key)
        
        return pd.DataFrame(split_rows)
    
    def _report(self, df: pd.DataFrame):
        """Dedup util"""
        self.stats['status_counts'] = df['dedup_status'].value_counts().to_dict() if 'dedup_status' in df.columns else {}


def dedup_dataframe(df: pd.DataFrame, price_threshold=0.20) -> pd.DataFrame:
    """Dedup DataFrame"""
    engine = DedupEngine(price_threshold=price_threshold)
    return engine.run(df)

