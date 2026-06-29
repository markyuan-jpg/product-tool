# QuoteFlow — 产品报价单在线生成工具

在线上传 Excel / PDF / Word 产品文件 → 自动解析产品信息 → 一键生成报价单 / PI / Packing List。

**网址：** [quoteflow.it.com](https://quoteflow.it.com)

> 📖 **架构/模块/数据流详见 [docs/系统架构与功能实现文档.md](docs/系统架构与功能实现文档.md)**（唯一架构文档，700 行）。
> 🤖 AI 代理请阅读 `CLAUDE.md`。开发者快捷参考见 `AGENTS.md`。

---

## 会话机制

当前为**匿名模式**，无需注册/登录即可使用全部功能：

- 浏览器首次访问自动生成 UUID（`localStorage.quote_session_id`）
- 每次请求携带 `X-Session-ID` header（绕过跨子域 cookie 限制）
- 后端以 `GuestUser` 绑定会话，`require_pro` 为 no-op（所有功能免费开放）
- 登录/注册/支付代码保留休眠（`auth.py`、`payment.py`、`database.py` 未删除），恢复只需改 Nav + 移除 session 中间件

---

## 功能

| 功能 | 状态 |
|------|:----:|
| 文件上传解析 (Excel × PDF × DOCX) | ✅ |
| 报价单生成 (Excel × PDF) | ✅ |
| 产品库管理 (搜索/删除/分页) | ✅ |
| PI 形式发票 | ✅ |
| Packing List 装箱单 | ✅ |
| Commercial Invoice 商业发票 | ✅ |
| 多图提取 (嵌入图 + 浮动图自动拼接) | ✅ |
| 智能粘贴 (AI 文本→产品) | ⚠️ 已禁用 (DeepSeek API 不公开) |

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 16 + React 19 + Tailwind CSS v4 |
| 后端 | FastAPI (Python 3.11+) + SQLAlchemy async |
| 数据库 | SQLite (默认) / PostgreSQL (可选) |
| 支付 | Creem (休眠中) |
| 邮件 | Resend > SMTP > noop (三通道回退) |
| 监控 | Sentry (后端 + 前端) |
| 分析 | Vercel Analytics |
| 限流 | slowapi (nginx X-Forwarded-For 感知) |
| 日志 | Python logging + 可选 JSON 结构化输出 |
| 部署 | 阿里云 VPS 新加坡 (后端) + Vercel (前端) |

---

## 快速开始

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# 前端
cd landing
npm install
npm run dev          # → http://localhost:3000

# 测试
cd backend && venv\Scripts\python -m pytest tests/ -v
```

### 环境变量（`backend/.env`）

| 变量 | 必填 | 说明 |
|------|:---:|------|
| `JWT_SECRET_KEY` | ✅ | JWT 签名密钥（最少 32 字符） |
| `BASE_URL` | ✅ | 前端域名，用于 CORS |
| `DEEPSEEK_API_KEY` | 否 | DeepSeek AI（智能粘贴 + AI 列检测，不设置仅影响 parse/with-ai） |
| `DATABASE_URL` | 否 | PostgreSQL 连接串（默认 `sqlite+aiosqlite:///./app.db`） |
| `CREEM_API_KEY` | 否 | Creem 支付 API Key |
| `CREEM_WEBHOOK_SECRET` | 否 | Creem Webhook HMAC 签名密钥 |
| `CREEM_PRODUCT_ID_PRO` | 否 | Creem Pro 产品 ID |
| `SENTRY_DSN` | 否 | Sentry 错误监控 DSN |
| `RESEND_API_KEY` | 否 | Resend 邮件 API Key（免费 100 封/天） |
| `SMTP_HOST` | 否 | SMTP 服务器地址（邮件备选方案） |
| `SMTP_PORT` | 否 | SMTP 端口（默认 587） |
| `SMTP_USER` | 否 | SMTP 用户名 |
| `SMTP_PASSWORD` | 否 | SMTP 密码 |
| `LOG_JSON` | 否 | 设为 1 启用结构化 JSON 日志 |

**Vercel 前端环境变量：**
- `NEXT_PUBLIC_API_URL=https://api.quoteflow.it.com`
- `NEXT_PUBLIC_SENTRY_DSN`（可选，与后端同一个 DSN）

---

## 部署

### 后端（阿里云 VPS）

```bash
# 首次部署
cd /home/admin/product-tool
git clone <repo-url> .
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# 创建 .env（见上方环境变量表）
nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &

# 更新部署
cd /home/admin/product-tool && git pull
cd backend && source venv/bin/activate
pip install -r requirements.txt    # 如有新依赖
pkill -f uvicorn && sleep 2
nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &
```

**前提：** Python 3.10+，开放 8000 端口（TCP），DNS `api.quoteflow.it.com` → 服务器 IP，nginx 反向代理 + SSL (Let's Encrypt)。

### 前端（Vercel）

1. Vercel 创建项目 → 关联 GitHub repo
2. Root Directory 设为 `landing`
3. 添加环境变量 `NEXT_PUBLIC_API_URL=https://api.quoteflow.it.com`
4. Push 到 master 自动部署

### Creem 支付设置

1. 注册 [creem.io](https://creem.io) → 创建产品 → 复制 Product ID
2. Settings → API Keys → 复制 Secret Key
3. Webhooks → 添加 `https://api.quoteflow.it.com/api/payment/webhook` → 复制 Signing Secret
4. 填入 `backend/.env` 的 `CREEM_API_KEY`、`CREEM_WEBHOOK_SECRET`、`CREEM_PRODUCT_ID_PRO`

### 数据库备份

```bash
# Linux (crontab)
0 2 * * * /home/admin/product-tool/scripts/backup.sh >> /home/admin/product-tool/backups/backup.log 2>&1

# Windows (任务计划程序)
powershell -File "D:\Projects\product-tool\scripts\backup.ps1"
```

备份保留 7 天，自动清理。

### PostgreSQL 迁移

```bash
cd backend && python migrate_data.py
```

---

## 项目结构

```
├── backend/                   # FastAPI 后端 (35 个端点)
│   ├── main.py                # 应用入口 + 匿名模式 session 中间件
│   ├── auth.py                # JWT 鉴权（休眠中）
│   ├── database.py            # ORM (User/Product/Quotation)（休眠中）
│   ├── payment.py             # Creem 支付（休眠中）
│   ├── mailer.py              # 邮件 (Resend > SMTP > noop)
│   ├── sanitize.py            # XSS 输入清洗
│   ├── logger.py              # JSON 结构化日志
│   ├── universal_parser.py    # 通用解析器
│   ├── score.py               # 双解析器评分
│   ├── product_repo.py        # 产品 CRUD（含自动建表）
│   ├── tests/                 # 34 项单元测试
│   └── requirements.txt
├── landing/                   # Next.js 前端
│   ├── app/                   # 页面路由
│   │   └── workspace/         # 工作台（匿名免登，X-Session-ID 会话）
│   ├── components/            # Nav/Footer/ErrorBoundary
│   ├── lib/                   # api/auth/i18n/errors
│   └── translations/          # zh.json / en.json
├── product_tool/              # 核心解析引擎
│   ├── src/core/              # 解析器 (Excel/DOCX/PDF)
│   │   └── image.py           # 图片三路合并提取 (openpyxl+DISPIMG+drawing)
│   ├── src/output/            # 报价单生成
│   └── shared_keywords.py     # 120+ 关键词 (25+ 行业)
├── scripts/                   # 运维脚本 (backup.sh/ps1)
├── .github/workflows/         # CI/CD
└── docs/                      # 技术文档
    └── 系统架构与功能实现文档.md  # 完整架构 (700行)
```

---

## 已知限制

### 格式支持

| 格式 | 支持 | 依赖 |
|------|:---:|------|
| .xlsx / .xls | ✅ | openpyxl |
| .docx | ✅ | python-docx |
| .pdf (文本) | ✅ | pdfplumber + PyMuPDF |
| .pdf (扫描) | ⚠️ | 需 `pip install docling` + `USE_DOCLING=1` |
| .doc | ❌ | 不支持 |
| .pdf (纯图片) | ❌ | 需 OCR |

### 数值限制

| 参数 | 上限 | 原因 |
|------|------|------|
| 行遍历 | 2000 行 | 防卡死 |
| 列扫描 | 50 列 | 防卡死 |
| 文件大小 | 50 MB | 上传限制 |
| 连续空行 | 20 行 | 触发扫描终止 |

### 性能

| 文件大小 | 耗时 |
|---------|------|
| <100 行 | <1s |
| 100-1000 行 | 1-3s |
| >1000 行 | 3-10s |
| >10000 行 | 限制在 2000 行内 |

### 已知 Bug

- **Excel:** 多数字单元格中 price 标识缺失时可能取错数字
- **PDF:** 跨表价格匹配时产品顺序不一致可能错位；图片无精确匹配时按序号分配可能错位
- **DOCX:** 合并单元格返回空字符串；自由文本仅适用于含明确型号+价格模式的文本

### 安全限制

| 限制项 | 状态 |
|--------|:---:|
| API 限流 | ✅ 已实现 |
| 密码加密 | ✅ bcrypt |
| 输入清洗 | ✅ html.escape |
| HSTS / XSS 防护 | ✅ |
| 验证码 | ❌ 未实现 |
| 邮箱验证 | ❌ 未实现 |
| 2FA | ❌ 未实现 |
| WAF | ❌ 未配置 |

### 常见问题

| 错误 | 原因 | 修复 |
|------|------|------|
| `No Next.js version detected` | Vercel 找不到 package.json | Root Directory 设为 `landing` |
| `connect-src` 限制 API | CSP 未加 API 域名 | `next.config.mjs` 加 `https://api.quoteflow.it.com` |
| 防火墙连不上 | 端口未开放 | 阿里云防火墙开放 8000 端口 |
| Creem 返回 502 | 密钥未配置 | 填入 `CREEM_API_KEY` 等环境变量 |
| PDF 生成失败 | 缺少系统字体 | VPS 安装中文字体包 |

---

## 文档

| 文档 | 读者 | 说明 |
|------|------|------|
| [系统架构与功能实现文档](docs/系统架构与功能实现文档.md) | 开发者 | 完整架构 (700行) |
| [CLAUDE.md](CLAUDE.md) | AI 代理 | 完整上下文 |
| [AGENTS.md](AGENTS.md) | 开发者 | 快捷参考 |
| [产品需求文档](product_tool/产品需求文档.md) | 产品经理 | 中文需求 |
| [REQUIREMENTS.md](product_tool/REQUIREMENTS.md) | 产品经理 | 英文需求 |

---

## 许可

Proprietary — All rights reserved.
