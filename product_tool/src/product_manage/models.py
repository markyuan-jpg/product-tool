# -*- coding: utf-8 -*-
"""
Product Data Model

Product dataclass for type-safe product representation.
"""
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple


@dataclass
class Product:
    """Product data model"""
    
    sku: str
    name_zh: str = ""
    name_en: str = ""
    category: str = ""
    price_rmb: float = 0.0
    price_usd: float = 0.0
    moq: int = 1
    specs: Dict[str, Any] = field(default_factory=dict)
    spec_zh: str = ""
    prices: Dict[str, List[Tuple[float, str]]] = field(default_factory=dict)
    image_path: str = ""
    source_file: str = ""
    # 包装字段
    carton_size: str = ""
    gross_weight: float = 0.0
    net_weight: float = 0.0
    cbm: float = 0.0
    units_per_carton: int = 0
    packing_type: str = ""
    
    # Auto-filled
    id: int = 0
    user_id: str = "local"
    created_at: str = ""
    updated_at: str = ""
    
    def __post_init__(self):
        """Auto-fill timestamps"""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (for SQLite insert)
        
        Returns:
            dict with serializable values
        """
        data = asdict(self)
        if self.specs:
            data['specs'] = json.dumps(self.specs, ensure_ascii=False)
        else:
            data['specs'] = None
        if self.prices:
            data['prices'] = json.dumps(self.prices, ensure_ascii=False)
        else:
            data['prices'] = None
        data['spec_zh'] = self.spec_zh
        return data
    
    def try_parse_numeric(self, val, default=0.0):
        """Try to parse a value as float, return default on failure"""
        if val is None or val == '':
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Product":
        """Create Product from dictionary (from SQLite select)
        
        Args:
            data: Dictionary with column values
            
        Returns:
            Product instance
        """
        # Extract known fields
        kwargs = {
            'id': data.get('id', 0),
            'user_id': data.get('user_id', 'local'),
            'sku': data.get('sku', ''),
            'name_zh': data.get('name_zh', ''),
            'name_en': data.get('name_en', ''),
            'category': data.get('category', ''),
            'price_rmb': data.get('price_rmb', 0.0) or 0.0,
            'price_usd': data.get('price_usd', 0.0) or 0.0,
            'moq': data.get('moq', 1) or 1,
            'specs': data.get('specs', {}),
            'spec_zh': data.get('spec_zh') or data.get('spec_zh', '') or '',
            'prices': data.get('prices', {}),
            'image_path': data.get('image_path') or data.get('_image_path', ''),
            'source_file': data.get('source_file') or data.get('_source_file', ''),
            # 包装字段
            'carton_size': data.get('carton_size', '') or '',
            'gross_weight': data.get('gross_weight', 0.0) or 0.0,
            'net_weight': data.get('net_weight', 0.0) or 0.0,
            'cbm': data.get('cbm', 0.0) or 0.0,
            'units_per_carton': data.get('units_per_carton', 0) or 0,
            'packing_type': data.get('packing_type', '') or '',
            'created_at': data.get('created_at', ''),
            'updated_at': data.get('updated_at', ''),
        }
        
        # Parse specs JSON if string
        specs = data.get('specs')
        if specs:
            if isinstance(specs, str):
                try:
                    kwargs['specs'] = json.loads(specs)
                except Exception:
                    try:
                        import ast
                        kwargs['specs'] = ast.literal_eval(specs)
                    except Exception:
                        kwargs['specs'] = {}
            elif isinstance(specs, dict):
                kwargs['specs'] = specs
        
        # Parse prices JSON
        prices_raw = data.get('prices')
        if prices_raw:
            if isinstance(prices_raw, str):
                try:
                    kwargs['prices'] = json.loads(prices_raw)
                except Exception:
                    kwargs['prices'] = {}
            elif isinstance(prices_raw, dict):
                kwargs['prices'] = prices_raw
        
        return cls(**kwargs)
    
    def to_row(self) -> tuple:
        """Convert to tuple for SQLite INSERT
        
        Returns:
            Tuple of values in table order
        """
        return (
            self.user_id,
            self.sku,
            self.name_zh,
            self.name_en,
            self.category,
            self.price_rmb,
            self.price_usd,
            self.moq,
            json.dumps(self.specs, ensure_ascii=False) if self.specs else None,
            self.spec_zh,
            json.dumps(self.prices, ensure_ascii=False) if self.prices else None,
            self.image_path,
            self.source_file,
            self.carton_size,
            self.gross_weight,
            self.net_weight,
            self.cbm,
            self.units_per_carton,
            self.packing_type,
            self.created_at,
            self.updated_at,
        )
    
    def update_timestamp(self) -> None:
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now().isoformat()
    
    def __repr__(self) -> str:
        return f"Product(sku={self.sku}, name_zh={self.name_zh}, price_rmb={self.price_rmb})"


def create_product_from_parse_result(row: Dict[str, Any], category: str = "") -> Product:
    """Create Product from parse result (param_price_parser output)
    
    Args:
        row: Dictionary from parsed data
        category: Category to assign
        
    Returns:
        Product instance
    """
    # Extract SKU from model
    sku = row.get('model', '')
    if not sku:
        raise ValueError("Missing 'model' field in parse result")
    
    # Extract name (prefer name_zh, fallback to model)
    name_zh = row.get('name_zh', sku)
    
    # Parse specs from spec_zh
    specs = {}
    spec_zh = row.get('spec_zh', '')
    if spec_zh:
        # Split by semicolon and parse key:value pairs
        for part in spec_zh.split(';'):
            part = part.strip()
            if ':' in part:
                key, value = part.split(':', 1)
                specs[key.strip()] = value.strip()
    
    return Product(
        sku=sku,
        name_zh=name_zh,
        name_en=row.get('name_en', ''),
        category=category,
        price_rmb=row.get('price_rmb', 0.0) or 0.0,
        price_usd=row.get('price_usd', 0.0) or 0.0,
        moq=row.get('moq', 1) or 1,
        specs=specs,
        prices=row.get('prices', {}),
        image_path=row.get('_image_path', ''),
        source_file=row.get('_source', ''),
        carton_size=row.get('carton_size', ''),
        gross_weight=row.get('gross_weight', 0.0) or 0.0,
        net_weight=row.get('net_weight', 0.0) or 0.0,
        cbm=row.get('cbm', 0.0) or 0.0,
        units_per_carton=row.get('units_per_carton', 0) or 0,
        packing_type=row.get('packing_type', ''),
    )
