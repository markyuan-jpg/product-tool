# -*- coding: utf-8 -*-
"""邮件发送模块 — 支持 Resend API / SMTP / Noop 三种模式

优先级：RESEND_API_KEY > SMTP_HOST > noop（仅日志）
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

_FROM = "QuoteFlow <no-reply@quoteflow.it.com>"


def _send_via_resend(to: str, subject: str, html: str) -> bool:
    """通过 Resend API 发送邮件"""
    try:
        import resend
        resend.api_key = os.getenv("RESEND_API_KEY")
        resend.Emails.send({
            "from": _FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        logger.info(f"Email sent via Resend to {to}")
        return True
    except Exception as e:
        logger.error(f"Resend send failed: {e}")
        return False


def _send_via_smtp(to: str, subject: str, html: str) -> bool:
    """通过 SMTP 发送邮件"""
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not host or not user or not password:
        logger.warning("SMTP not configured, skipping")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = _FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        logger.info(f"Email sent via SMTP to {to}")
        return True
    except Exception as e:
        logger.error(f"SMTP send failed: {e}")
        return False


def _send_noop(to: str, subject: str, html: str) -> bool:
    """开发模式：仅打日志，不真发"""
    preview = html[:200].replace("\n", " ")
    logger.info(f"[NOOP EMAIL] to={to} | subject={subject} | preview={preview}")
    return True


async def send_email(to: str, subject: str, html: str) -> bool:
    """统一发送入口：按优先级尝试各渠道"""
    if os.getenv("RESEND_API_KEY"):
        return _send_via_resend(to, subject, html)
    if os.getenv("SMTP_HOST"):
        return _send_via_smtp(to, subject, html)
    return _send_noop(to, subject, html)


# === 预置邮件模板 ===

WELCOME_HTML = """<!DOCTYPE html>
<html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
  <h1 style="color:#1a365d">🎉 欢迎加入 QuoteFlow！</h1>
  <p>您的账号已创建成功。现在可以开始：</p>
  <ol>
    <li>上传产品文件（Excel / PDF / Word）</li>
    <li>系统自动解析产品信息</li>
    <li>一键生成报价单</li>
  </ol>
  <a href="https://quoteflow.it.com/workspace" style="display:inline-block;padding:12px 24px;background:#1a365d;color:#fff;text-decoration:none;border-radius:8px">进入工作台</a>
  <p style="margin-top:24px;color:#666;font-size:13px">如有疑问，请联系客服。</p>
</body></html>"""

UPGRADE_HTML = """<!DOCTYPE html>
<html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
  <h1 style="color:#1a365d">🚀 升级成功！</h1>
  <p>您现在已经是 QuoteFlow Pro 用户，可以享受：</p>
  <ul>
    <li>✅ 智能粘贴 — 任意文本一键提取产品</li>
    <li>✅ PI 形式发票</li>
    <li>✅ 无限制上传次数</li>
  </ul>
  <a href="https://quoteflow.it.com/workspace" style="display:inline-block;padding:12px 24px;background:#1a365d;color:#fff;text-decoration:none;border-radius:8px">开始使用 Pro 功能</a>
</body></html>"""

RESET_HTML_TEMPLATE = """<!DOCTYPE html>
<html><body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
  <h1 style="color:#1a365d">🔑 密码重置</h1>
  <p>您请求了密码重置。请点击下方链接设置新密码（有效期 15 分钟）：</p>
  <a href="{reset_url}" style="display:inline-block;padding:12px 24px;background:#1a365d;color:#fff;text-decoration:none;border-radius:8px">重置密码</a>
  <p style="margin-top:24px;color:#666;font-size:13px">如果这不是您发起的，请忽略此邮件。</p>
</body></html>"""


def make_reset_html(reset_url: str) -> str:
    return RESET_HTML_TEMPLATE.format(reset_url=reset_url)
