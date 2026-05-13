# -*- coding: utf-8 -*-
"""
Product Repository

CRUD operations for product library.
"""
import sqlite3
import json
import ast
from datetime import datetime
from typing import List, Optional, Dict, Any

from .db import get_connection, close_connection, init_db
from .models import Product


def _row_to_product(row: sqlite3.Row) -> Product:
    """Convert SQLite row to Product"""
    return Product.from_dict(dict(row))


def save_product(product: Product, update_if_exists: bool = True) -> int:
    """Save product (INSERT or UPDATE)
    
    Args:
        product: Product instance
        update_if_exists: If True, update existing; else skip
        
    Returns:
        product.id (new or existing)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        product.update_timestamp()
        
        # Check if exists
        cursor.execute(
            "SELECT id FROM products WHERE user_id = ? AND sku = ?",
            (product.user_id, product.sku)
        )
        existing = cursor.fetchone()
        
        if existing:
            if update_if_exists:
                # UPDATE
                cursor.execute("""
                    UPDATE products SET
                        name_zh = ?,
                        name_en = ?,
                        category = ?,
                        price_rmb = ?,
                        price_usd = ?,
                        moq = ?,
                        specs = ?,
                        spec_zh = ?,
                        image_path = ?,
                        source_file = ?,
                        carton_size = ?,
                        gross_weight = ?,
                        net_weight = ?,
                        cbm = ?,
                        units_per_carton = ?,
                        packing_type = ?,
                        updated_at = ?
                    WHERE user_id = ? AND sku = ?
                """, (
                    product.name_zh,
                    product.name_en,
                    product.category,
                    product.price_rmb,
                    product.price_usd,
                    product.moq,
                    json.dumps(product.specs, ensure_ascii=False) if product.specs else None,
                    product.spec_zh,
                    product.image_path,
                    product.source_file,
                    product.carton_size,
                    product.gross_weight,
                    product.net_weight,
                    product.cbm,
                    product.units_per_carton,
                    product.packing_type,
                    product.updated_at,
                    product.user_id,
                    product.sku,
                ))
                product.id = existing[0]
            else:
                product.id = existing[0]
        else:
            # INSERT
            cursor.execute("""
                INSERT INTO products (
                    user_id, sku, name_zh, name_en, category,
                    price_rmb, price_usd, moq, specs,
                    spec_zh, prices, image_path, source_file,
                    carton_size, gross_weight, net_weight, cbm,
                    units_per_carton, packing_type,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, product.to_row())
            product.id = cursor.lastrowid
        
        conn.commit()
        return product.id
    
    finally:
        close_connection(conn)


def get_product_by_id(product_id: int, user_id: str = "local") -> Optional[Product]:
    """Get product by ID
    
    Args:
        product_id: Product ID
        user_id: User ID (default: local)
        
    Returns:
        Product or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM products WHERE id = ? AND user_id = ?",
            (product_id, user_id)
        )
        row = cursor.fetchone()
        
        if row:
            return _row_to_product(row)
        return None
    
    finally:
        close_connection(conn)


def get_products_by_ids(product_ids: List[int], user_id: str = "local", order_by_source: bool = False) -> Dict[int, Product]:
    """Batch get products by IDs (one query, not N)
    
    Args:
        product_ids: List of product IDs
        user_id: User ID
        order_by_source: If True, order by source_file + created_at (group same source together)
    
    Returns:
        Dict mapping product_id -> Product
    """
    if not product_ids:
        return {}
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        placeholders = ",".join("?" * len(product_ids))
        
        # 排序逻辑
        if order_by_source:
            order_clause = "ORDER BY source_file, created_at"
        else:
            order_clause = "ORDER BY sku, CASE user_id WHEN 'ev_alls' THEN 0 WHEN 'local' THEN 1 ELSE 2 END"
        
        # 如果 user_id 为空或 None，不过滤用户，获取所有用户的产品
        # 但要按 sku 去重，优先用 ev_alls（原始数据更完整）
        if user_id:
            cursor.execute(
                f"SELECT * FROM products WHERE id IN ({placeholders}) AND user_id = ? {order_clause}",
                (*product_ids, user_id)
            )
        else:
            # 获取所有用户的产品，但按sku去重，优先ev_alls的记录
            cursor.execute(
                f"SELECT * FROM products WHERE id IN ({placeholders}) {order_clause}",
                (*product_ids,)
            )
        
        rows = cursor.fetchall()
        
        # 去重：同SKU优先ev_alls，如果ev_alls没有则保留任何存在的版本
        # 但要确保移除参数泄露到SKU的问题数据
        seen = {}
        result = {}
        for row in rows:
            sku = row['sku']
            # Skip SKUs that have params leaked (contain newline or early colon)
            if '\n' in str(sku) or (':' in sku and sku.index(':') < 15):
                continue
            if sku not in seen:
                seen[sku] = True
                result[row['id']] = _row_to_product(row)
        
        return result
    
    finally:
        close_connection(conn)


def get_products_by_skus(skus: List[str], user_id: str = "local") -> Dict[str, Product]:
    """Batch get products by SKUs (one query, not N)
    
    Args:
        skus: List of SKUs
        user_id: User ID
        
    Returns:
        Dict mapping sku -> Product
    """
    if not skus:
        return {}
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        placeholders = ",".join("?" * len(skus))
        cursor.execute(
            f"SELECT * FROM products WHERE sku IN ({placeholders}) AND user_id = ?",
            (*skus, user_id)
        )
        return {row["sku"]: _row_to_product(row) for row in cursor.fetchall()}
    
    finally:
        close_connection(conn)


def get_product_by_sku(sku: str, user_id: str = "local") -> Optional[Product]:
    """Get product by SKU
    
    Args:
        sku: Product SKU
        user_id: User ID
        
    Returns:
        Product or None
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM products WHERE sku = ? AND user_id = ?",
            (sku, user_id)
        )
        row = cursor.fetchone()
        
        if row:
            return _row_to_product(row)
        return None
    
    finally:
        close_connection(conn)


def list_products(
    category: Optional[str] = None,
    user_id: str = "local",
    limit: int = 100,
    offset: int = 0
) -> List[Product]:
    """List products
    
    Args:
        category: Filter by category (None = all)
        user_id: User ID
        limit: Max results
        offset: Pagination offset
        
    Returns:
        List of Products
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if category:
            cursor.execute("""
                SELECT * FROM products 
                WHERE user_id = ? AND category = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, category, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM products 
                WHERE user_id = ?
                ORDER BY updated_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        
        return [_row_to_product(row) for row in cursor.fetchall()]
    
    finally:
        close_connection(conn)


def search_products(
    keyword: str,
    user_id: str = "local",
    limit: int = 50
) -> List[Product]:
    """Search products by keyword
    
    Searches in sku, name_zh, name_en.
    
    Args:
        keyword: Search keyword
        user_id: User ID
        limit: Max results
        
    Returns:
        List of matching Products
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        pattern = f"%{keyword}%"
        cursor.execute("""
            SELECT * FROM products 
            WHERE user_id = ? AND (
                sku LIKE ? OR 
                name_zh LIKE ? OR 
                name_en LIKE ?
            )
            ORDER BY 
                CASE 
                    WHEN sku LIKE ? THEN 1
                    WHEN name_zh LIKE ? THEN 2
                    ELSE 3
                END
            LIMIT ?
        """, (user_id, pattern, pattern, pattern, pattern, pattern, limit))
        
        return [_row_to_product(row) for row in cursor.fetchall()]
    
    finally:
        close_connection(conn)


def delete_product(product_id: int, user_id: str = "local") -> bool:
    """Delete product
    
    Args:
        product_id: Product ID
        user_id: User ID
        
    Returns:
        True if deleted, False if not found
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM products WHERE id = ? AND user_id = ?",
            (product_id, user_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    
    finally:
        close_connection(conn)


def get_categories(user_id: str = "local") -> List[str]:
    """Get list of categories
    
    Args:
        user_id: User ID
        
    Returns:
        List of category names
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT DISTINCT category 
            FROM products 
            WHERE user_id = ? AND category IS NOT NULL AND category != ''
            ORDER BY category
        """, (user_id,))
        
        return [row[0] for row in cursor.fetchall()]
    
    finally:
        close_connection(conn)


def get_product_count(user_id: str = "local") -> int:
    """Get total product count
    
    Args:
        user_id: User ID
        
    Returns:
        Number of products
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM products WHERE user_id = ?",
            (user_id,)
        )
        return cursor.fetchone()[0]
    
    finally:
        close_connection(conn)


def update_price(
    product_id: int,
    price_rmb: Optional[float] = None,
    price_usd: Optional[float] = None,
    user_id: str = "local"
) -> bool:
    """Update product price
    
    Args:
        product_id: Product ID
        price_rmb: New RMB price
        price_usd: New USD price
        user_id: User ID
        
    Returns:
        True if updated
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if price_rmb is not None:
            updates.append("price_rmb = ?")
            params.append(price_rmb)
        if price_usd is not None:
            updates.append("price_usd = ?")
            params.append(price_usd)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([product_id, user_id])
        
        cursor.execute(f"""
            UPDATE products 
            SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
        """, params)

        conn.commit()
        return cursor.rowcount > 0

    finally:
        close_connection(conn)


def update_product(
    product_id: int,
    name_zh: Optional[str] = None,
    name_en: Optional[str] = None,
    category: Optional[str] = None,
    price_rmb: Optional[float] = None,
    price_usd: Optional[float] = None,
    moq: Optional[int] = None,
    specs: Optional[Dict] = None,
    image_path: Optional[str] = None,
    user_id: str = "local"
) -> bool:
    """Update product fields
    
    Args:
        product_id: Product ID
        name_zh: New Chinese name
        name_en: New English name
        category: New category
        price_rmb: New RMB price
        price_usd: New USD price
        moq: New MOQ
        specs: New specs dict
        image_path: New image path
        user_id: User ID
        
    Returns:
        True if updated
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        fields = {
            'name_zh': name_zh,
            'name_en': name_en,
            'category': category,
            'price_rmb': price_rmb,
            'price_usd': price_usd,
            'moq': moq,
            'specs': json.dumps(specs, ensure_ascii=False) if specs else None,
            'image_path': image_path,
        }
        
        for field, value in fields.items():
            if value is not None:
                updates.append(f"{field} = ?")
                params.append(value)
        
        if not updates:
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.extend([product_id, user_id])
        
        cursor.execute(f"""
            UPDATE products 
            SET {', '.join(updates)}
            WHERE id = ? AND user_id = ?
        """, params)

        conn.commit()
        return cursor.rowcount > 0

    finally:
        close_connection(conn)


if __name__ == "__main__":
    # Test: CRUD operations
    init_db()
    
    # Create test product
    p = Product(
        sku="TEST-001",
        name_zh="测试产品",
        name_en="Test Product",
        category="测试分类",
        price_rmb=1000.0,
        price_usd=140.0,
        moq=10
    )
    
    # Save
    pid = save_product(p)
    print(f"Saved: {pid}")
    
    # Get
    p2 = get_product_by_id(pid)
    print(f"Retrieved: {p2}")
    
    # List
    products = list_products()
    print(f"Count: {len(products)}")
    
    # Search
    results = search_products("测试")
    print(f"Search results: {len(results)}")
    
    # Delete
    deleted = delete_product(pid)
    print(f"Deleted: {deleted}")