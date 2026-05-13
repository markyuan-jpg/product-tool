"""
Data Migration Script: SQLite → PostgreSQL (Supabase)

Usage:
    python migrate_data.py

Reads from:
    - backend/auth.db (users table)
    - ~/.product_tool/products.db (web_products, web_quotations tables)

Writes to:
    - PostgreSQL via DATABASE_URL env var

Safe to run multiple times (upserts by id).
"""
import os
import sys
import sqlite3
import asyncio
from datetime import datetime
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import async_session_factory, User, Product, Quotation


async def migrate_users(sqldb: str):
    """Migrate users from auth.db to Supabase."""
    src = sqlite3.connect(sqldb)
    src.row_factory = sqlite3.Row
    rows = src.execute("SELECT * FROM users").fetchall()
    src.close()

    async with async_session_factory() as session:
        count = 0
        for row in rows:
            exists = await session.get(User, row['id'])
            if exists:
                # Update existing
                exists.username = row['username']
                exists.password_hash = row['password_hash']
                exists.tier = row.get('tier', 'free')
                exists.upload_count = row.get('upload_count', 0)
                exists.upload_month = row.get('upload_month', '')
            else:
                user = User(
                    id=row['id'],
                    username=row['username'],
                    password_hash=row['password_hash'],
                    tier=row.get('tier', 'free'),
                    upload_count=row.get('upload_count', 0),
                    upload_month=row.get('upload_month', ''),
                )
                session.add(user)
            count += 1
        await session.commit()
        print(f"Migrated {count} users")


async def migrate_products(sqldb: str):
    """Migrate web_products from products.db to Supabase."""
    if not Path(sqldb).exists():
        print(f"Products DB not found: {sqldb}, skipping")
        return

    src = sqlite3.connect(sqldb)
    src.row_factory = sqlite3.Row

    # Check if table exists
    tables = src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='web_products'").fetchall()
    if not tables:
        print("web_products table not found, skipping")
        src.close()
        return

    rows = src.execute("SELECT * FROM web_products").fetchall()
    src.close()

    async with async_session_factory() as session:
        count = 0
        for row in rows:
            exists = await session.get(Product, row['id'])
            if not exists:
                product = Product(
                    id=row['id'],
                    user_id=int(row['user_id']) if row['user_id'] else 0,
                    model=row.get('model', '') or '',
                    name_zh=row.get('name_zh', '') or '',
                    spec_zh=row.get('spec_zh', '') or '',
                    price_rmb=row.get('price_rmb') or 0,
                    price_cny=row.get('price_cny') or 0,
                    currency=row.get('currency', 'RMB') or 'RMB',
                    image_path=row.get('image_path', '') or '',
                    category=row.get('category', '') or '',
                    carton_size=row.get('carton_size', '') or '',
                    gross_weight=row.get('gross_weight') or 0,
                    net_weight=row.get('net_weight') or 0,
                    cbm=row.get('cbm') or 0,
                    units_per_carton=row.get('units_per_carton') or 0,
                    packing_type=row.get('packing_type', '') or '',
                )
                session.add(product)
                count += 1
        await session.commit()
        print(f"Migrated {count} products")


async def migrate_quotations(sqldb: str):
    """Migrate web_quotations from products.db to Supabase."""
    if not Path(sqldb).exists():
        return

    src = sqlite3.connect(sqldb)
    src.row_factory = sqlite3.Row

    tables = src.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='web_quotations'").fetchall()
    if not tables:
        print("web_quotations table not found, skipping")
        src.close()
        return

    rows = src.execute("SELECT * FROM web_quotations").fetchall()
    src.close()

    async with async_session_factory() as session:
        count = 0
        for row in rows:
            exists = await session.get(Quotation, row['id'])
            if not exists:
                q = Quotation(
                    id=row['id'],
                    user_id=int(row['user_id']) if row['user_id'] else 0,
                    product_ids=row.get('product_ids', '') or '',
                    file_name=row.get('file_name', '') or '',
                    file_path=row.get('file_path', '') or '',
                )
                session.add(q)
                count += 1
        await session.commit()
        print(f"Migrated {count} quotations")


async def main():
    auth_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')
    products_db = os.getenv('PRODUCT_TOOL_DB_PATH', str(Path.home() / '.product_tool' / 'products.db'))

    print(f"Auth DB: {auth_db}")
    print(f"Products DB: {products_db}")
    print(f"Target: {os.getenv('DATABASE_URL', 'postgresql+asyncpg://...')[:50]}...")
    print()

    await migrate_users(auth_db)
    await migrate_products(products_db)
    await migrate_quotations(products_db)

    print("\nMigration complete!")


if __name__ == '__main__':
    asyncio.run(main())
