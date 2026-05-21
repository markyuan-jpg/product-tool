"""
Database module — SQLAlchemy async ORM for PostgreSQL (Supabase).

Provides:
- AsyncEngine + async_session for FastAPI dependency injection
- ORM models: User, Product, Quotation
- DB initialization (create tables)
- Session dependency for route handlers
"""
import os
import logging
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, create_engine, event
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

logger = logging.getLogger(__name__)

# ─── Connection ───

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite+aiosqlite:///./app.db'
)

_is_sqlite = DATABASE_URL.startswith('sqlite')

# Async engine (for route handlers)
if _is_sqlite:
    engine = create_async_engine(DATABASE_URL, echo=False)
else:
    # statement_cache_size=0 required for Supavisor/PgBouncer pooler
    engine = create_async_engine(
        DATABASE_URL, echo=False, pool_size=5, max_overflow=10,
        connect_args={"statement_cache_size": 0}
    )
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

# Sync engine (for backward compatibility with legacy _get_products_db style)
if _is_sqlite:
    # SQLite fallback: use existing sqlite3 path
    SyncSession = None
else:
    _sync_db_url = DATABASE_URL.replace('+asyncpg', '+psycopg2')
    _sync_engine = create_engine(_sync_db_url, pool_size=3, max_overflow=5)
    SyncSession = sessionmaker(bind=_sync_engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Base ───

class Base(DeclarativeBase):
    pass


# ─── Models ───

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    tier = Column(String(20), default='free')          # free / pro
    upload_count = Column(Integer, default=0)
    upload_month = Column(String(7), default='')        # YYYY-MM
    stripe_customer_id = Column(String(100), nullable=True)   # Creem customer ID
    subscription_id = Column(String(100), nullable=True)      # Creem subscription ID
    subscription_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = 'web_products'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    model = Column(String(200), default='')
    name_zh = Column(Text, default='')
    name_en = Column(Text, default='')
    spec_zh = Column(Text, default='')
    spec_en = Column(Text, default='')
    price_rmb = Column(Float, default=0)
    price_cny = Column(Float, default=0)
    price_usd = Column(Float, default=0)
    currency = Column(String(10), default='RMB')
    image_path = Column(Text, default='')
    category = Column(String(100), default='')
    carton_size = Column(String(50), default='')
    gross_weight = Column(Float, default=0)
    net_weight = Column(Float, default=0)
    cbm = Column(Float, default=0)
    units_per_carton = Column(Integer, default=0)
    packing_type = Column(String(50), default='')
    created_at = Column(DateTime, default=datetime.utcnow)


class Quotation(Base):
    __tablename__ = 'web_quotations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    product_ids = Column(Text, default='')       # JSON array of product IDs
    file_name = Column(String(255), default='')
    file_path = Column(Text, default='')
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Init ───

async def init_db():
    """Create all tables. Safe to run repeatedly (CREATE IF NOT EXISTS)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created/verified")
