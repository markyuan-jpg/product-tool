# -*- coding: utf-8 -*-
"""Payment endpoint tests."""

import json
import pytest
from unittest.mock import patch, AsyncMock


class TestPaymentWebhook:
    async def test_webhook_activate(self, client, auth_headers, session):
        """Webhook 升级用户为 pro"""
        from database import User
        from sqlalchemy import select

        headers, user = auth_headers
        assert user.tier == "free"

        # Mock verify_webhook 返回 True（测试环境无密钥）
        payload = json.dumps({
            "type": "checkout.completed",
            "data": {
                "metadata": {"user_id": str(user.id)},
                "subscription_id": "sub_test_123",
            }
        })
        with patch("main.verify_webhook", return_value=True):
            res = await client.post("/api/payment/webhook", content=payload, headers={
                "creem-signature": "test-sig",
                "Content-Type": "application/json",
            })
        assert res.status_code == 200

        # 验证用户已升级
        await session.refresh(user)
        assert user.tier == "pro"

    async def test_webhook_deactivate(self, client, auth_headers, session):
        """Webhook 降级用户为 free"""
        headers, user = auth_headers

        # 先升级
        user.tier = "pro"
        await session.commit()

        payload = json.dumps({
            "type": "subscription.expired",
            "data": {"metadata": {"user_id": str(user.id)}}
        })
        with patch("main.verify_webhook", return_value=True):
            res = await client.post("/api/payment/webhook", content=payload, headers={
                "creem-signature": "test-sig",
                "Content-Type": "application/json",
            })
        assert res.status_code == 200

        await session.refresh(user)
        assert user.tier == "free"

    async def test_webhook_unauthorized_no_secret(self, client, auth_headers, session):
        """未配置 webhook secret 时拒绝请求"""
        headers, user = auth_headers
        payload = json.dumps({
            "type": "checkout.completed",
            "data": {"metadata": {"user_id": str(user.id)}}
        })
        res = await client.post("/api/payment/webhook", content=payload, headers={
            "creem-signature": "test-sig",
            "Content-Type": "application/json",
        })
        assert res.status_code == 400

    async def test_webhook_invalid_json(self, client):
        """无效 JSON 返回 400"""
        with patch("main.verify_webhook", return_value=True):
            res = await client.post("/api/payment/webhook", content="not json", headers={
                "creem-signature": "test-sig",
            })
        assert res.status_code == 400

    async def test_create_checkout_requires_auth(self, client, auth_headers):
        """创建 checkout 需要登录"""
        headers, _ = auth_headers
        # 未配 Creem 密钥时返回 502
        res = await client.post("/api/payment/create-checkout", headers=headers)
        assert res.status_code == 502
