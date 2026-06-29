"""
Payment module — Creem.io integration.

- Create checkout session for Pro subscription
- Verify webhook signatures (HMAC-SHA256)
- Handle subscription lifecycle events
"""
import os
import hmac
import hashlib
import logging
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ─── Config ───

CREEM_API_KEY = os.getenv('CREEM_API_KEY', '')
CREEM_WEBHOOK_SECRET = os.getenv('CREEM_WEBHOOK_SECRET', '')
CREEM_PRODUCT_ID_PRO = os.getenv('CREEM_PRODUCT_ID_PRO', '')
CREEM_BASE_URL = os.getenv('CREEM_BASE_URL', 'https://api.creem.io/v1')
BASE_URL = os.getenv('BASE_URL', 'http://localhost:3000')

_HEADERS = {
    'x-api-key': CREEM_API_KEY,
    'Content-Type': 'application/json',
}


def _is_configured() -> bool:
    return bool(CREEM_API_KEY and CREEM_PRODUCT_ID_PRO)


# ─── Checkout ───


def create_checkout_session(
    user_id: int,
    email: str = '',
    success_url: str = None,
    cancel_url: str = None,
) -> Optional[dict]:
    """Create a Creem checkout session for Pro subscription.

    Returns dict with 'checkout_url' on success, None on failure.
    """
    if not _is_configured():
        logger.error("Creem not configured: missing API key or product ID")
        return None

    payload = {
        "product_id": CREEM_PRODUCT_ID_PRO,
        "success_url": success_url or f"{BASE_URL}/payment/success",
        "cancel_url": cancel_url or f"{BASE_URL}/pricing",
        "metadata": {
            "user_id": str(user_id),
        },
    }
    if email:
        payload["customer_email"] = email

    try:
        resp = requests.post(
            f"{CREEM_BASE_URL}/checkouts",
            json=payload,
            headers=_HEADERS,
            timeout=15,
        )
        if resp.ok:
            data = resp.json()
            logger.info(f"Creem checkout created for user {user_id}: {data.get('id')}")
            return data
        else:
            logger.error(f"Creem checkout error: {resp.status_code} {resp.text}")
            return None
    except Exception as e:
        logger.error(f"Creem checkout failed: {e}")
        return None


# ─── Webhook ───


def verify_webhook(payload: bytes, signature: str) -> bool:
    """Verify Creem webhook HMAC-SHA256 signature."""
    if not CREEM_WEBHOOK_SECRET:
        logger.warning("Creem webhook secret not configured, rejecting request")
        return False
    expected = hmac.new(
        CREEM_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def handle_webhook_event(event: str, data: dict) -> Optional[str]:
    """Process Creem webhook event. Returns action description or None.

    The data dict typically contains:
    - For checkout.completed: { id, status, metadata: { user_id } }
    - For subscription.*: { id, status, metadata: { user_id } }
    """
    event_type = event
    metadata = data.get('metadata', {}) or {}
    user_id_str = metadata.get('user_id', '')

    if not user_id_str:
        logger.warning(f"Webhook {event_type}: no user_id in metadata")
        return None

    user_id = int(user_id_str)

    if event_type == 'checkout.completed':
        return f"activate:{user_id}"
    elif event_type == 'subscription.active':
        return f"activate:{user_id}"
    elif event_type == 'subscription.canceled':
        return f"deactivate:{user_id}"
    elif event_type == 'subscription.past_due':
        return f"deactivate:{user_id}"
    elif event_type == 'subscription.expired':
        return f"deactivate:{user_id}"

    return None
