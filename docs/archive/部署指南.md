# 部署指南

> 后端部署在阿里云轻量应用服务器（新加坡），前端托管在 Vercel。

---

## 1. 环境变量

在后端 `backend/.env` 中设置（完整清单）：

| 变量 | 必填 | 说明 |
|------|:---:|------|
| `JWT_SECRET_KEY` | ✅ | JWT 签名密钥 |
| `BASE_URL` | ✅ | 前端域名，用于 CORS |
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek AI（智能粘贴 + AI 列检测） |
| `DATABASE_URL` | 可选 | PostgreSQL 连接串（默认 SQLite） |
| `CREEM_API_KEY` | 可选 | Creem 支付 |
| `CREEM_WEBHOOK_SECRET` | 可选 | Creem Webhook 签名 |
| `CREEM_PRODUCT_ID_PRO` | 可选 | Creem 产品 ID |
| `SENTRY_DSN` | 可选 | Sentry 错误监控 DSN |
| `RESEND_API_KEY` | 可选 | Resend 邮件 API Key |
| `SMTP_HOST` | 可选 | SMTP 服务器地址（邮件备选方案） |
| `SMTP_PORT` | 可选 | SMTP 端口 (默认 587) |
| `SMTP_USER` | 可选 | SMTP 用户名 |
| `SMTP_PASSWORD` | 可选 | SMTP 密码 |
| `LOG_JSON` | 可选 | 设为 1 启用结构化 JSON 日志 |

---

## 2. 后端部署（阿里云 VPS）

| 步骤 | 操作 |
|------|------|
| 1 | 购买 VPS（推荐 2 vCPU / 2GB 内存以上） |
| 2 | 安装 Python 3.10+、pip、git |
| 3 | `git clone` 项目到服务器 |
| 4 | `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt` |
| 5 | 创建 `backend/.env`（见上方环境变量表） |
| 6 | `nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &` |
| 7 | 设置防火墙开放 8000 端口（TCP） |
| 8 | DNS：`api.quoteflow.it.com` → A 记录指向服务器 IP |
| 9 | 配置 nginx 反向代理 + SSL（Let's Encrypt） |

**更新部署：**
```bash
cd /home/admin/product-tool
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt   # 如有新依赖
pkill -f uvicorn && sleep 2
nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &
```

### 数据库迁移（PostgreSQL）

```bash
cd backend
python migrate_data.py
```

脚本会从 SQLite（`app.db` + `~/.product_tool/products.db`）读取数据写入 PostgreSQL。

---

## 3. 前端部署（Vercel）

| 步骤 | 操作 |
|------|------|
| 1 | Vercel 创建项目，关联 GitHub repo |
| 2 | Root Directory 设为 `landing` |
| 3 | 环境变量：`NEXT_PUBLIC_API_URL=https://api.quoteflow.it.com` |
| 4 | 可选：`NEXT_PUBLIC_SENTRY_DSN`（与后端同一个 DSN） |

推送代码到主分支即自动部署。

---

## 4. Creem 支付设置

1. 注册 [creem.io](https://creem.io) → 创建产品 → 复制 Product ID 到 `CREEM_PRODUCT_ID_PRO`
2. Creem Settings → API Keys → 复制 Secret Key 到 `CREEM_API_KEY`
3. Creem Settings → Webhooks → 添加 URL `https://api.quoteflow.it.com/api/payment/webhook` → 复制 Signing Secret 到 `CREEM_WEBHOOK_SECRET`
4. 在 `backend/.env` 或服务器环境变量加上这 3 个变量

---

## 5. 数据库备份

```bash
# 设置 cron 每日备份
crontab -e
# 添加：
0 2 * * * /home/admin/product-tool/scripts/backup.sh >> /home/admin/product-tool/backups/backup.log 2>&1
```

备份保留 7 天，自动清理旧文件。

---

## 常见问题排查

| 错误 | 原因 | 修复 |
|------|------|------|
| `No Next.js version detected` | Vercel 找不到 `landing/package.json` | Dashboard → Root Directory 设成 `landing` |
| `connect-src` 限制 API | CSP 没加 API 域名 | `next.config.mjs` 的 `connect-src` 加上 `https://api.quoteflow.it.com` |
| 防火墙连不上 | 服务器端口没开放 | 阿里云/云服务商防火墙开放 8000 端口 |
| Creem 返回 502 | 密钥未配置 | 填入 `CREEM_API_KEY` 等环境变量 |
| PDF 生成失败 | 缺少系统字体 | VPS 安装中文字体包 |
