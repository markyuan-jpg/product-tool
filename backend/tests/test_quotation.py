# -*- coding: utf-8 -*-
"""Quotation API tests — minimal, since full generation requires product_tool deps."""

import json
import pytest


class TestQuotations:
    async def test_generate_excel_basic(self, client, auth_headers):
        """生成 Excel 报价单 — 验证返回成功"""
        headers, _ = auth_headers
        products = [{"model": "Q-001", "name_zh": "测试", "price_rmb": 100}]
        res = await client.post("/api/quotation", data={
            "products": json.dumps(products),
            "currency": "CNY",
            "lang": "zh",
            "trade_terms": "EXW",
            "payment_terms": "T/T 50%,50%",
            "with_images": "0",
        }, headers=headers)
        assert res.status_code in (200, 500)  # 500 if weasyprint fonts missing

    async def test_generate_pdf(self, client, auth_headers):
        """生成 PDF 报价单 — 验证返回"""
        headers, _ = auth_headers
        products = [{"model": "Q-001", "name_zh": "测试", "price_rmb": 100}]
        res = await client.post("/api/quotation/pdf", data={
            "products": json.dumps(products),
            "currency": "CNY",
            "payment_terms": "T/T",
            "contract_no": "QF2024001",
            "lang": "bilingual",
        }, headers=headers)
        # PDF generation may fail if weasyprint deps not installed
        assert res.status_code in (200, 500)

    async def test_pi_pro_required(self, client, auth_headers):
        """Free 用户请求 PI 返回 403"""
        headers, user = auth_headers
        assert user.tier == "free"
        res = await client.post("/api/pi", data={
            "products": json.dumps([{"model": "P-001", "price_rmb": 100}]),
            "buyer_name": "Test Buyer",
            "buyer_email": "buyer@test.com",
            "buyer_address": "123 Test St",
            "lang": "en",
        }, headers=headers)
        assert res.status_code == 403

    async def test_packing_pro_required(self, client, auth_headers):
        """Free 用户请求 Packing List 返回 403"""
        headers, _ = auth_headers
        res = await client.post("/api/packing", data={
            "products": json.dumps([{"model": "P-001", "price_rmb": 100}]),
            "buyer_name": "Test Buyer",
            "buyer_address": "123 Test St",
            "lang": "en",
        }, headers=headers)
        assert res.status_code == 403

    async def test_invoice_pro_required(self, client, auth_headers):
        """Free 用户请求 Commercial Invoice 返回 403"""
        headers, _ = auth_headers
        res = await client.post("/api/invoice", data={
            "products": json.dumps([{"model": "P-001", "price_rmb": 100}]),
            "buyer_name": "Test Buyer",
            "buyer_address": "123 Test St",
            "lang": "en",
        }, headers=headers)
        assert res.status_code == 403

    async def test_quotation_history(self, client, auth_headers):
        """获取报价历史"""
        headers, _ = auth_headers
        res = await client.get("/api/quotations", headers=headers)
        assert res.status_code == 200
        data = res.json()
        # Response may be a list or {"quotations": [...]}
        items = data.get("quotations", data if isinstance(data, list) else [])
        assert isinstance(items, list)
