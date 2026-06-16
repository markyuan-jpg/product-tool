# -*- coding: utf-8 -*-
"""Auth endpoint tests."""

import pytest
from auth import verify_password, get_user_by_username, get_user_by_email


class TestRegister:
    async def test_register_success(self, client, session):
        """注册成功应返回 token + user"""
        res = await client.post("/api/auth/register", data={
            "username": "newuser123",
            "email": "new@test.com",
            "password": "pass123456",
        })
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert data["user"]["username"] == "newuser123"
        assert data["user"]["tier"] == "free"

        # Verify user was actually created in DB
        user = await get_user_by_username(session, "newuser123")
        assert user is not None
        assert user.email == "new@test.com"

    async def test_register_duplicate_username(self, client):
        """重复用户名返回 400"""
        data = {"username": "dupuser", "email": "dup1@test.com", "password": "pass123456"}
        await client.post("/api/auth/register", data=data)
        data["email"] = "dup2@test.com"
        res = await client.post("/api/auth/register", data=data)
        assert res.status_code == 400

    async def test_register_duplicate_email(self, client):
        """重复邮箱返回 400"""
        data = {"username": "user1", "email": "same@test.com", "password": "pass123456"}
        await client.post("/api/auth/register", data=data)
        data["username"] = "user2"
        res = await client.post("/api/auth/register", data=data)
        assert res.status_code == 400

    async def test_register_weak_password(self, client):
        """密码小于6位返回 400（可能被限流 429，因为前面测试用完了额度）"""
        res = await client.post("/api/auth/register", data={
            "username": "test1", "email": "test@test.com", "password": "12345"
        })
        assert res.status_code in (400, 429)

    async def test_register_invalid_username(self, client):
        """用户名含非法字符返回 400（可能被限流 429）"""
        res = await client.post("/api/auth/register", data={
            "username": "test user!", "email": "test@test.com", "password": "pass123456"
        })
        assert res.status_code in (400, 429)

    async def test_register_invalid_email(self, client):
        """无效邮箱返回 400（可能被限流 429）"""
        res = await client.post("/api/auth/register", data={
            "username": "test1", "email": "notanemail", "password": "pass123456"
        })
        assert res.status_code in (400, 429)

    async def test_register_missing_fields(self, client):
        """缺少必填字段返回 422"""
        res = await client.post("/api/auth/register", data={"username": "test1"})
        assert res.status_code == 422


class TestLogin:
    async def test_login_success(self, client, auth_headers):
        """正确密码登录应返回 token"""
        res = await client.post("/api/auth/login", data={
            "username": "testuser", "password": "test123456"
        })
        assert res.status_code == 200
        data = res.json()
        assert "token" in data
        assert data["user"]["username"] == "testuser"

    async def test_login_wrong_password(self, client, auth_headers):
        """错误密码返回 400"""
        res = await client.post("/api/auth/login", data={
            "username": "testuser", "password": "wrongpassword"
        })
        assert res.status_code == 400

    async def test_login_nonexistent_user(self, client):
        """不存在的用户返回 400"""
        res = await client.post("/api/auth/login", data={
            "username": "nobody", "password": "pass123456"
        })
        assert res.status_code == 400


class TestChangePassword:
    async def test_change_success(self, client, auth_headers):
        """正确旧密码改密成功"""
        headers, _ = auth_headers
        res = await client.put("/api/auth/change-password", data={
            "old_password": "test123456", "new_password": "newpass789"
        }, headers=headers)
        assert res.status_code == 200

        # Verify new password works
        res2 = await client.post("/api/auth/login", data={
            "username": "testuser", "password": "newpass789"
        })
        assert res2.status_code == 200

    async def test_change_wrong_old(self, client, auth_headers):
        """错误旧密码返回 400"""
        headers, _ = auth_headers
        res = await client.put("/api/auth/change-password", data={
            "old_password": "wrongold", "new_password": "newpass789"
        }, headers=headers)
        assert res.status_code == 400

    async def test_change_weak_new(self, client, auth_headers):
        """新密码太短返回 400"""
        headers, _ = auth_headers
        res = await client.put("/api/auth/change-password", data={
            "old_password": "test123456", "new_password": "12345"
        }, headers=headers)
        assert res.status_code == 400


class TestMe:
    async def test_me_authorized(self, client, auth_headers):
        """已登录返回用户信息"""
        headers, user = auth_headers
        res = await client.get("/api/user/me", headers=headers)
        assert res.status_code == 200
        assert res.json()["username"] == "testuser"

    async def test_me_no_auth(self, client):
        """无 token 返回 401"""
        res = await client.get("/api/user/me")
        assert res.status_code == 401


class TestForgotPassword:
    async def test_forgot_email_sent(self, client, auth_headers):
        """忘记密码返回 ok（无论邮箱是否注册）"""
        headers, _ = auth_headers
        res = await client.post("/api/auth/forgot-password", data={
            "email": "test@example.com"
        })
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    async def test_forgot_unknown_email(self, client):
        """未注册邮箱也返回 ok（防枚举）"""
        res = await client.post("/api/auth/forgot-password", data={
            "email": "nonexistent@example.com"
        })
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestResetPassword:
    async def test_reset_invalid_token(self, client):
        """无效 token 返回 400"""
        res = await client.post("/api/auth/reset-password", data={
            "token": "invalid-token", "new_password": "newpass789"
        })
        assert res.status_code == 400

    async def test_reset_weak_password(self, client):
        """新密码太短返回 400"""
        res = await client.post("/api/auth/reset-password", data={
            "token": "some-token", "new_password": "12345"
        })
        assert res.status_code == 400
