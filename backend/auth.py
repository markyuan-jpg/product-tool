"""
Auth module — JWT authentication, user management, tier control.

SQLAlchemy async ORM + PostgreSQL (Supabase).
"""
import os
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Header, HTTPException, Depends
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import jwt as pyjwt
import bcrypt as _bcrypt

from database import get_session, User

logger = logging.getLogger(__name__)

# ─── Config ───

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY environment variable is required")

ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 15      # short-lived access token
REFRESH_TOKEN_EXPIRE_DAYS = 7         # long-lived refresh token
FREE_MONTHLY_LIMIT = 20
FREE_PRODUCT_LIMIT = 200


# ─── Password ───

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return _bcrypt.checkpw(password.encode(), password_hash.encode())


# ─── JWT Tokens ───

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": str(user_id), "exp": expire, "type": "refresh"}
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_reset_token(user_id: int) -> str:
    """一次性密码重置 token，15 分钟有效"""
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {"sub": str(user_id), "exp": expire, "type": "reset"}
    return pyjwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_reset_token(token: str) -> Optional[int]:
    """解码密码重置 token，返回 user_id 或 None"""
    payload = decode_token(token)
    if payload is None:
        return None
    if payload.get('type') != 'reset':
        return None
    return int(payload['sub'])


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT. Returns payload dict or None on failure."""
    try:
        return pyjwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        return None
    except pyjwt.InvalidTokenError:
        return None


# ─── User queries ───

async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


# ─── FastAPI dependencies ───

async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_session),
) -> User:
    """Require valid access token. Raises 401 if missing/invalid."""
    if not authorization:
        raise HTTPException(401, "未登录")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise ValueError
    except (ValueError, AttributeError):
        raise HTTPException(401, "Token 格式错误")

    payload = decode_token(token)
    if payload is None:
        raise HTTPException(401, "登录已过期，请重新登录")
    if payload.get('type') != 'access':
        raise HTTPException(401, "Token 类型错误")

    user_id = int(payload['sub'])
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(401, "用户不存在")
    return user


async def get_current_user_optional(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_session),
) -> Optional[User]:
    """Optional auth — returns None instead of raising on failure.
    
    支持两种调用方式：
    1. Depends(get_current_user_optional) → FastAPI 注入 db session
    2. await get_current_user_optional(authorization) → 直接调用，无 session 时不查库
    """
    if not authorization:
        return None
    # 直接调用时 db 可能未解析（Depends 对象），无法用于查询
    if db is None or not isinstance(db, AsyncSession):
        return None
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


# ─── Tier / quota ───

def require_pro(user: User):
    if user.tier != 'pro':
        raise HTTPException(403, "此功能仅限专业版（Pro）用户使用")


def _current_month() -> str:
    return datetime.utcnow().strftime('%Y-%m')


def _is_new_month(user: User) -> bool:
    return user.upload_month != _current_month()


async def check_upload_limit(user: User, db: AsyncSession) -> bool:
    """Check and reset monthly upload count. Returns True if allowed."""
    if user.tier == 'pro':
        return True
    if _is_new_month(user):
        user.upload_count = 0
        user.upload_month = _current_month()
        await db.commit()
    return user.upload_count < FREE_MONTHLY_LIMIT


async def increment_upload(user: User, db: AsyncSession):
    if _is_new_month(user):
        user.upload_count = 0
        user.upload_month = _current_month()
    user.upload_count += 1
    await db.commit()
