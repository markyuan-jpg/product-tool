# -*- coding: utf-8 -*-
"""
Product Library Database Module

SQLite connection management with configurable path.
Default: ~/.product_tool/products.db
Override: PRODUCT_TOOL_DB_PATH environment variable
"""
import os
import sqlite3
from pathlib import Path
from typing import Optional

# Default directory and file
DEFAULT_DIR = Path.home() / ".product_tool"
DEFAULT_DB_FILE = "products.db"
DEFAULT_DIR.mkdir(parents=True, exist_ok=True)

# Environment variable override
DB_PATH = os.environ.get("PRODUCT_TOOL_DB_PATH", str(DEFAULT_DIR / DEFAULT_DB_FILE))


def get_db_path() -> str:
    """Get database path"""
    return DB_PATH


def set_db_path(path: str) -> None:
    """Set custom database path (runtime only)"""
    global DB_PATH
    DB_PATH = path


def ensure_dir(path: str) -> None:
    """Ensure directory exists"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)


def init_db(conn: Optional[sqlite3.Connection] = None) -> sqlite3.Connection:
    """Initialize database schema
    
    Args:
        conn: Optional connection. If None, uses get_connection()
    
    Returns:
        Connection (same as input or new)
    """
    if conn is None:
        conn = get_connection()
    
    cursor = conn.cursor()
    
    # Products table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT DEFAULT 'local',
            sku TEXT NOT NULL,
            name_zh TEXT,
            name_en TEXT,
            category TEXT,
            price_rmb REAL,
            price_usd REAL,
            moq INTEGER DEFAULT 1,
            specs TEXT,
            spec_zh TEXT,
            prices TEXT DEFAULT '{}',
            price_migrated INTEGER DEFAULT 0,
            image_path TEXT,
            source_file TEXT,
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(user_id, sku)
        )
    """)
    
    # Index for faster search
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_name_zh ON products(name_zh)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_products_user_id ON products(user_id)
    """)
    
    conn.commit()
    
    # Add spec_zh column if not exists (migration)
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN spec_zh TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN prices TEXT DEFAULT '{}'")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE products ADD COLUMN price_migrated INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass
    # 包装字段迁移
    for col, dtype in [('carton_size', 'TEXT'), ('gross_weight', 'REAL DEFAULT 0'),
                        ('net_weight', 'REAL DEFAULT 0'), ('cbm', 'REAL DEFAULT 0'),
                        ('units_per_carton', 'INTEGER DEFAULT 0'), ('packing_type', 'TEXT')]:
        try:
            cursor.execute(f"ALTER TABLE products ADD COLUMN {col} {dtype}")
        except sqlite3.OperationalError:
            pass
    
    return conn


def get_connection() -> sqlite3.Connection:
    """Get database connection
    
    Each call returns a new connection for thread safety.
    Caller MUST close the connection after use.
    
    Returns:
        sqlite3.Connection
    """
    ensure_dir(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn


def close_connection(conn: sqlite3.Connection) -> None:
    """Safely close connection
    
    Args:
        conn: sqlite3.Connection to close
    """
    if conn:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Test: initialize database
    print(f"Database path: {get_db_path()}")
    conn = get_connection()
    init_db(conn)
    
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    conn.close()
    print("Database initialized successfully")
