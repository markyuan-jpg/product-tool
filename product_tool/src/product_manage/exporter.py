# -*- coding: utf-8 -*-
"""
Product Exporter

Export products to Excel/CSV.
"""
import pandas as pd
from typing import Optional

from .db import init_db
from .repository import list_products, search_products


def export_to_excel(
    output_path: str,
    category: Optional[str] = None,
    user_id: str = "local",
    include_specs: bool = True
) -> str:
    """Export products to Excel
    
    Args:
        output_path: Output Excel path
        category: Filter by category (None = all)
        user_id: User ID
        include_specs: Include specs JSON column
        
    Returns:
        output_path
    """
    init_db()
    
    products = list_products(category=category, user_id=user_id, limit=10000)
    
    if not products:
        # Create empty DataFrame
        df = pd.DataFrame(columns=[
            "id", "sku", "name_zh", "name_en", "category",
            "price_rmb", "price_usd", "moq", "image_path", "source_file"
        ])
    else:
        rows = []
        for p in products:
            row = {
                "id": p.id,
                "sku": p.sku,
                "name_zh": p.name_zh,
                "name_en": p.name_en,
                "category": p.category,
                "price_rmb": p.price_rmb,
                "price_usd": p.price_usd,
                "moq": p.moq,
                "image_path": p.image_path,
                "source_file": p.source_file,
            }
            if include_specs and p.specs:
                import json
                row["specs"] = json.dumps(p.specs, ensure_ascii=False)
            rows.append(row)
        
        df = pd.DataFrame(rows)
    
    df.to_excel(output_path, index=False, engine='openpyxl')
    return output_path


def export_to_csv(
    output_path: str,
    category: Optional[str] = None,
    user_id: str = "local"
) -> str:
    """Export products to CSV
    
    Args:
        output_path: Output CSV path
        category: Filter by category (None = all)
        user_id: User ID
        
    Returns:
        output_path
    """
    init_db()
    
    products = list_products(category=category, user_id=user_id, limit=10000)
    
    if not products:
        df = pd.DataFrame(columns=[
            "id", "sku", "name_zh", "name_en", "category",
            "price_rmb", "price_usd", "moq", "image_path", "source_file"
        ])
    else:
        rows = []
        for p in products:
            rows.append({
                "id": p.id,
                "sku": p.sku,
                "name_zh": p.name_zh,
                "name_en": p.name_en,
                "category": p.category,
                "price_rmb": p.price_rmb,
                "price_usd": p.price_usd,
                "moq": p.moq,
                "image_path": p.image_path,
                "source_file": p.source_file,
            })
        
        df = pd.DataFrame(rows)
    
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    return output_path


if __name__ == "__main__":
    # Test export
    export_to_excel("output/test_products.xlsx")
    print("Exported to output/test_products.xlsx")