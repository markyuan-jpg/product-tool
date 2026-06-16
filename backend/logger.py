# -*- coding: utf-8 -*-
"""结构化 JSON 日志 — 替换 root logging handler，不改变任何现有 log 调用"""

import logging, json, sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record):
        log = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "path": getattr(record, "pathname", None),
            "lineno": getattr(record, "lineno", None),
            "func": getattr(record, "funcName", None),
            "exc": self.formatException(record.exc_info) if record.exc_info else None,
        }
        return json.dumps(log, default=str, ensure_ascii=False)


def setup_structured_logging():
    """替换 root logger 的 handler 为 JSON 格式输出"""
    root = logging.getLogger()
    # 清掉 basicConfig 加的默认 handler
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)
