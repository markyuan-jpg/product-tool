"""
轻量级用户行为埋点 — SQLite 存储, fire-and-forget

用法:
    from analytics import track_event
    track_event('upload_success', session_id='abc123', payload={'format': 'xlsx'})
"""

import sqlite3
import json
import os
import time
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / ".product_tool" / "analytics.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

_conn = None

def _get_conn():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                session_id TEXT DEFAULT '',
                payload TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        _conn.execute("CREATE INDEX IF NOT EXISTS idx_events_event ON events(event)")
        _conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at)")
        _conn.commit()
    return _conn


def track_event(event: str, session_id: str = '', payload: dict = None):
    """记录事件 (fire-and-forget, 不阻塞)"""
    try:
        conn = _get_conn()
        payload_str = json.dumps(payload or {}, ensure_ascii=False)
        conn.execute(
            "INSERT INTO events (event, session_id, payload) VALUES (?, ?, ?)",
            (event, session_id, payload_str)
        )
        conn.commit()
    except Exception:
        pass  # 埋点失败不影响主流程


def get_stats(days: int = 7) -> dict:
    """获取最近 N 天的统计摘要"""
    try:
        conn = _get_conn()
        cutoff = (datetime.now().timestamp() - days * 86400)
        cutoff_str = datetime.fromtimestamp(cutoff).strftime('%Y-%m-%d %H:%M:%S')
        
        # 总事件数
        total = conn.execute(
            "SELECT COUNT(*) FROM events WHERE created_at >= ?", (cutoff_str,)
        ).fetchone()[0]
        
        # 各事件计数
        rows = conn.execute(
            "SELECT event, COUNT(*) as cnt FROM events WHERE created_at >= ? GROUP BY event ORDER BY cnt DESC",
            (cutoff_str,)
        ).fetchall()
        by_event = {row[0]: row[1] for row in rows}
        
        # 独立 session 数
        sessions = conn.execute(
            "SELECT COUNT(DISTINCT session_id) FROM events WHERE created_at >= ? AND session_id != ''",
            (cutoff_str,)
        ).fetchone()[0]
        
        # 每日趋势
        daily = conn.execute("""
            SELECT date(created_at) as d, COUNT(*) as cnt 
            FROM events 
            WHERE created_at >= ? 
            GROUP BY d ORDER BY d
        """, (cutoff_str,)).fetchall()
        daily_trend = [{'date': row[0], 'count': row[1]} for row in daily]
        
        return {
            'days': days,
            'total_events': total,
            'unique_sessions': sessions,
            'by_event': by_event,
            'daily_trend': daily_trend,
        }
    except Exception:
        return {'days': days, 'total_events': 0, 'unique_sessions': 0, 'by_event': {}, 'daily_trend': []}
