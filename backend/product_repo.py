"""
product_repo.py — Product & Quotation data access layer.

Auto-detects SQLite (local dev) vs PostgreSQL (production) from DATABASE_URL.
Returns data as list[dict] — same format as old sqlite3.Row.
"""
import os
import json
from pathlib import Path
from typing import Optional

# ─── Backend detection ───

def _is_sqlite() -> bool:
    from database import DATABASE_URL
    return DATABASE_URL.startswith('sqlite')

def _get_sqlite_conn():
    """Open raw sqlite3 connection to products.db. Auto-create tables if missing."""
    import sqlite3
    _DEFAULT_DB = Path.home() / ".product_tool" / "products.db"
    db_path = Path(os.environ.get("PRODUCT_TOOL_DB_PATH", str(_DEFAULT_DB)))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS web_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL, model TEXT, name_zh TEXT, spec_zh TEXT,
            price_rmb REAL, image_path TEXT, category TEXT, currency TEXT,
            carton_size TEXT, gross_weight REAL, net_weight REAL, cbm REAL,
            units_per_carton INTEGER, packing_type TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            price_cny REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS web_quotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL, product_ids TEXT, file_name TEXT,
            file_path TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

def _get_pg_session():
    """Return SQLAlchemy sync session for PostgreSQL."""
    from database import SyncSession
    return SyncSession()

def _rows_to_dicts(rows) -> list[dict]:
    """Convert SQLAlchemy Row objects or sqlite3.Row to plain dicts."""
    result = []
    for r in rows:
        if hasattr(r, '_mapping'):
            result.append(dict(r._mapping))
        elif hasattr(r, 'keys'):
            result.append(dict(r))
        else:
            result.append(dict(r))
    return result

def _row_to_dict(row) -> Optional[dict]:
    if row is None:
        return None
    if hasattr(row, '_mapping'):
        return dict(row._mapping)
    elif hasattr(row, 'keys'):
        return dict(row)
    return dict(row)

# ─── Products ───

def get_products(user_id: int) -> dict:
    """Return {"products": [...], "total": N, "limited": bool}."""
    uid = user_id  # int

    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            total = conn.execute("SELECT COUNT(*) FROM web_products WHERE user_id=?", [uid]).fetchone()[0]
            rows = conn.execute(
                "SELECT * FROM web_products WHERE user_id=? ORDER BY created_at DESC", [uid]
            ).fetchall()
            return {"products": [dict(r) for r in rows], "total": total, "limited": False}
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            total = session.execute(text("SELECT COUNT(*) FROM web_products WHERE user_id=:uid"), {"uid": uid}).scalar()
            rows = session.execute(
                text("SELECT * FROM web_products WHERE user_id=:uid ORDER BY created_at DESC"),
                {"uid": uid}
            ).fetchall()
            return {"products": _rows_to_dicts(rows), "total": total or 0, "limited": False}
        finally:
            session.close()


def save_products(user_id: int, items: list[dict]) -> int:
    """Insert multiple products. Returns count inserted."""
    uid = user_id
    inserted = 0

    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            for item in items:
                model_val = item.get("model", "").strip()
                if not model_val:
                    model_val = str(item.get("name_zh", "") or "").strip()[:20]
                if not model_val:
                    model_val = str(item.get("spec_zh", "") or "").strip()[:20]
                if not model_val:
                    model_val = f"Item_{item.get('_row', inserted + 1)}"
                if not model_val:
                    continue

                # Extract packaging info from spec_zh
                spec_zh = item.get("spec_zh", "")
                pkg = _extract_pkg(spec_zh)

                conn.execute(
                    """INSERT INTO web_products
                       (user_id, model, name_zh, spec_zh, price_rmb, price_cny, image_path,
                        currency, carton_size, gross_weight, net_weight, cbm, units_per_carton, packing_type)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    [uid, model_val, item.get("name_zh",""), spec_zh,
                     item.get("price_rmb"), item.get("price_cny", 0),
                     item.get("_image_path",""), item.get("currency","RMB"),
                     item.get("carton_size","") or pkg.get("carton_size",""),
                     float(item.get("gross_weight", 0) or 0) or pkg.get("gross_weight", 0),
                     float(item.get("net_weight", 0) or 0) or pkg.get("net_weight", 0),
                     float(item.get("cbm", 0) or 0) or pkg.get("cbm", 0),
                     int(item.get("units_per_carton", 0) or 0) or pkg.get("units_per_carton", 0),
                     item.get("packing_type","") or pkg.get("packing_type","")]
                )
                inserted += 1
            conn.commit()
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            for item in items:
                model_val = item.get("model", "").strip()
                if not model_val:
                    model_val = str(item.get("name_zh", "") or "").strip()[:20]
                if not model_val:
                    model_val = str(item.get("spec_zh", "") or "").strip()[:20]
                if not model_val:
                    model_val = f"Item_{item.get('_row', inserted + 1)}"
                if not model_val:
                    continue

                spec_zh = item.get("spec_zh", "")
                pkg = _extract_pkg(spec_zh)

                session.execute(
                    text("""INSERT INTO web_products
                       (user_id, model, name_zh, spec_zh, price_rmb, price_cny, image_path,
                        currency, carton_size, gross_weight, net_weight, cbm, units_per_carton, packing_type)
                       VALUES (:uid, :model, :nzh, :spec, :prmb, :pcny, :img,
                        :cur, :csize, :gw, :nw, :cbm, :upc, :ptype)"""),
                    {"uid": uid, "model": model_val, "nzh": item.get("name_zh",""),
                     "spec": spec_zh, "prmb": item.get("price_rmb"), "pcny": item.get("price_cny", 0),
                     "img": item.get("_image_path",""), "cur": item.get("currency","RMB"),
                     "csize": item.get("carton_size","") or pkg.get("carton_size",""),
                     "gw": float(item.get("gross_weight", 0) or 0) or pkg.get("gross_weight", 0),
                     "nw": float(item.get("net_weight", 0) or 0) or pkg.get("net_weight", 0),
                     "cbm": float(item.get("cbm", 0) or 0) or pkg.get("cbm", 0),
                     "upc": int(item.get("units_per_carton", 0) or 0) or pkg.get("units_per_carton", 0),
                     "ptype": item.get("packing_type","") or pkg.get("packing_type","")}
                )
                inserted += 1
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return inserted


def delete_product(product_id: int, user_id: int):
    """Delete single product."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            conn.execute("DELETE FROM web_products WHERE id=? AND user_id=?", [product_id, user_id])
            conn.commit()
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            session.execute(text("DELETE FROM web_products WHERE id=:pid AND user_id=:uid"),
                          {"pid": product_id, "uid": user_id})
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def batch_delete_products(product_ids: list[int], user_id: int) -> int:
    """Delete multiple products. Returns count deleted."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            count = 0
            for pid in product_ids:
                conn.execute("DELETE FROM web_products WHERE id=? AND user_id=?", [pid, user_id])
                count += 1
            conn.commit()
            return count
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            result = session.execute(
                text("DELETE FROM web_products WHERE id = ANY(:ids) AND user_id=:uid"),
                {"ids": list(product_ids), "uid": user_id}
            )
            count = result.rowcount
            session.commit()
            return count or 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def count_products(user_id: int) -> int:
    """Count products for a user."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            return conn.execute("SELECT COUNT(*) FROM web_products WHERE user_id=?", [user_id]).fetchone()[0]
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            return session.execute(text("SELECT COUNT(*) FROM web_products WHERE user_id=:uid"),
                                  {"uid": user_id}).scalar() or 0
        finally:
            session.close()


# ─── Quotations ───

def get_quotations(user_id: int) -> list[dict]:
    """Return all quotations for user."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            rows = conn.execute(
                "SELECT * FROM web_quotations WHERE user_id=? ORDER BY created_at DESC", [user_id]
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            rows = session.execute(
                text("SELECT * FROM web_quotations WHERE user_id=:uid ORDER BY created_at DESC"),
                {"uid": user_id}
            ).fetchall()
            return _rows_to_dicts(rows)
        finally:
            session.close()


def get_quotation(quotation_id: int, user_id: int) -> Optional[dict]:
    """Get single quotation."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            row = conn.execute(
                "SELECT * FROM web_quotations WHERE id=? AND user_id=?", [quotation_id, user_id]
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            row = session.execute(
                text("SELECT * FROM web_quotations WHERE id=:qid AND user_id=:uid"),
                {"qid": quotation_id, "uid": user_id}
            ).fetchone()
            return _row_to_dict(row)
        finally:
            session.close()


def save_quotation(user_id: int, product_ids: str, file_name: str, file_path: str) -> int:
    """Save quotation and return its ID."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            conn.execute(
                "INSERT INTO web_quotations (user_id, product_ids, file_name, file_path) VALUES (?,?,?,?)",
                [user_id, product_ids, file_name, file_path]
            )
            conn.commit()
            return conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            result = session.execute(
                text("""INSERT INTO web_quotations (user_id, product_ids, file_name, file_path)
                       VALUES (:uid, :pids, :fname, :fpath) RETURNING id"""),
                {"uid": user_id, "pids": product_ids, "fname": file_name, "fpath": file_path}
            )
            qid = result.scalar()
            session.commit()
            return qid
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def delete_quotation(quotation_id: int, user_id: int) -> Optional[str]:
    """Delete quotation, return file_path for cleanup (or None)."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            row = conn.execute(
                "SELECT * FROM web_quotations WHERE id=? AND user_id=?", [quotation_id, user_id]
            ).fetchone()
            if not row:
                return None
            file_path = row["file_path"]
            conn.execute("DELETE FROM web_quotations WHERE id=? AND user_id=?", [quotation_id, user_id])
            conn.commit()
            return file_path
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            row = session.execute(
                text("SELECT * FROM web_quotations WHERE id=:qid AND user_id=:uid"),
                {"qid": quotation_id, "uid": user_id}
            ).fetchone()
            if not row:
                return None
            r = _row_to_dict(row)
            file_path = r.get("file_path", "")
            session.execute(
                text("DELETE FROM web_quotations WHERE id=:qid AND user_id=:uid"),
                {"qid": quotation_id, "uid": user_id}
            )
            session.commit()
            return file_path
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def batch_delete_quotations(quotation_ids: list[int], user_id: int) -> int:
    """Delete multiple quotations. Returns count + cleans up files (caller handles)."""
    if _is_sqlite():
        conn = _get_sqlite_conn()
        try:
            count = 0
            for qid in quotation_ids:
                row = conn.execute(
                    "SELECT * FROM web_quotations WHERE id=? AND user_id=?", [qid, user_id]
                ).fetchone()
                if row:
                    if row["file_path"] and os.path.isfile(row["file_path"]):
                        try:
                            os.remove(row["file_path"])
                        except Exception:
                            pass
                    conn.execute("DELETE FROM web_quotations WHERE id=? AND user_id=?", [qid, user_id])
                    count += 1
            conn.commit()
            return count
        finally:
            conn.close()
    else:
        from sqlalchemy import text
        session = _get_pg_session()
        try:
            # Get all quotations first
            rows = session.execute(
                text("SELECT * FROM web_quotations WHERE id = ANY(:ids) AND user_id=:uid"),
                {"ids": list(quotation_ids), "uid": user_id}
            ).fetchall()
            quotations = _rows_to_dicts(rows)

            # Delete files
            for q in quotations:
                fp = q.get("file_path", "")
                if fp and os.path.isfile(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass

            # Bulk delete
            result = session.execute(
                text("DELETE FROM web_quotations WHERE id = ANY(:ids) AND user_id=:uid"),
                {"ids": list(quotation_ids), "uid": user_id}
            )
            count = result.rowcount
            session.commit()
            return count or 0
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# ─── Helpers (moved from main.py to avoid duplication) ───

def _extract_pkg(spec_zh: str) -> dict:
    """Extract packaging info from spec_zh."""
    import re
    result = {
        'carton_size': '', 'gross_weight': 0, 'net_weight': 0,
        'cbm': 0, 'units_per_carton': 0, 'packing_type': ''
    }
    if not spec_zh:
        return result
    parts = re.split(r'[;\n]', spec_zh)
    for part in parts:
        part = part.strip()
        if ':' not in part:
            continue
        key, val = part.split(':', 1)
        key = key.strip().lower()
        val = val.strip()
        if any(k in key for k in ['carton size', '外箱尺寸', 'packing size', 'package size', '包装尺寸', 'carton', '测量']):
            result['carton_size'] = part.split(':', 1)[1].strip()
        if any(k in key for k in ['gross weight', 'gw', '毛重']):
            try:
                result['gross_weight'] = float(re.sub(r'[^\d.]', '', val))
            except Exception:
                pass
        if any(k in key for k in ['net weight', 'nw', '净重']):
            try:
                result['net_weight'] = float(re.sub(r'[^\d.]', '', val))
            except Exception:
                pass
        if any(k in key for k in ['cbm', '体积', 'cub']):
            try:
                result['cbm'] = float(re.sub(r'[^\d.]', '', val))
            except Exception:
                pass
        if any(k in key for k in ['pcs/ctn', 'pcs/carton', 'pcs/', '/ctn', '数量', 'qty/ctn']):
            try:
                result['units_per_carton'] = int(re.sub(r'[^\d]', '', val))
            except Exception:
                pass
        if any(k in key for k in ['packing type', '包装方式', '包装类型']):
            result['packing_type'] = val
    return result
