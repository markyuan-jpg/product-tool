# -*- coding: utf-8 -*-
"""Products API tests."""

import json
import pytest


class TestProducts:
    async def test_save_products(self, client, auth_headers):
        """保存产品成功"""
        headers, _ = auth_headers
        products = [
            {"model": "ABC-001", "name_zh": "测试产品1", "price_rmb": 100.5},
            {"model": "ABC-002", "name_zh": "测试产品2", "price_rmb": 200},
        ]
        res = await client.post("/api/products/save", data={"products": json.dumps(products)}, headers=headers)
        assert res.status_code == 200
        assert res.json()["inserted"] == 2

    async def test_save_empty(self, client, auth_headers):
        """保存空列表返回 400"""
        headers, _ = auth_headers
        res = await client.post("/api/products/save", data={"products": "[]"}, headers=headers)
        assert res.status_code == 400

    async def test_save_no_model(self, client, auth_headers):
        """产品无 model 返回 400"""
        headers, _ = auth_headers
        res = await client.post("/api/products/save", data={"products": json.dumps([{"name_zh": "x"}])}, headers=headers)
        assert res.status_code == 400

    async def test_save_unauthorized(self, client):
        """无 token 返回 401"""
        res = await client.post("/api/products/save", data={"products": json.dumps([{"model": "X"}])})
        assert res.status_code == 401

    async def test_get_products(self, client, auth_headers):
        """获取产品列表"""
        headers, _ = auth_headers
        products = [{"model": "GET-001", "price_rmb": 50}]
        await client.post("/api/products/save", data={"products": json.dumps(products)}, headers=headers)
        res = await client.get("/api/products", headers=headers)
        assert res.status_code == 200
        data = res.json()
        items = data.get("products", data if isinstance(data, list) else [])
        assert len(items) > 0

    async def test_delete_product(self, client, auth_headers):
        """删除单个产品"""
        headers, _ = auth_headers
        products = [{"model": "DEL-001", "price_rmb": 10}]
        save_res = await client.post("/api/products/save", data={"products": json.dumps(products)}, headers=headers)
        assert save_res.status_code == 200

        get_res = await client.get("/api/products", headers=headers)
        data = get_res.json()
        items = data.get("products", data if isinstance(data, list) else [])
        assert len(items) > 0
        pid = items[0]["id"]

        del_res = await client.delete(f"/api/products/{pid}", headers=headers)
        assert del_res.status_code == 200

    async def test_batch_delete(self, client, auth_headers):
        """批量删除产品"""
        headers, _ = auth_headers
        products = [{"model": f"BD-{i:03d}", "price_rmb": i} for i in range(3)]
        await client.post("/api/products/save", data={"products": json.dumps(products)}, headers=headers)
        get_res = await client.get("/api/products", headers=headers)
        data = get_res.json()
        items = data.get("products", data if isinstance(data, list) else [])
        ids = [str(p["id"]) for p in items]
        res = await client.post("/api/products/batch-delete", data={"product_ids": json.dumps(ids)}, headers=headers)
        assert res.status_code == 200

    async def test_xss_sanitization(self, client, auth_headers):
        """XSS 尝试应被清洗"""
        headers, _ = auth_headers
        products = [{"model": "<script>alert(1)</script>", "name_zh": "safe", "price_rmb": 100}]
        res = await client.post("/api/products/save", data={"products": json.dumps(products)}, headers=headers)
        assert res.status_code == 200

        get_res = await client.get("/api/products", headers=headers)
        data = get_res.json()
        saved = data.get("products", data if isinstance(data, list) else [])
        assert len(saved) > 0
        # model 应被转义
        assert "&lt;script&gt;" in saved[0]["model"] or saved[0]["model"] == "&lt;script&gt;alert(1)&lt;/script&gt;"
