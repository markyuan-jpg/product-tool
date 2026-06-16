# CLAUDE.md — QuoteFlow 完整代理上下文

> **目标受众：** AI 编码代理（Claude、OpenCode 等）
> **最后更新：** 2026-06-16
> **行数：** ~350

---

## 1. 项目身份

| 属性 | 值 |
|------|-----|
| 名称 | QuoteFlow（报价整合工具） |
| 用途 | 在线产品报价单生成工具 |
| 前端 URL | https://quoteflow.it.com |
| API URL | https://api.quoteflow.it.com |
| 仓库 | github.com/markyuan-jpg/product-tool |
| 分支 | master |
| 技术栈 | Next.js 16 + FastAPI + SQLAlchemy + SQLite |

---

## 2. 架构总览

```
Browser → Vercel (landing/) → HTTPS → Alibaba VPS (backend/) → SQLite/PostgreSQL
                ↑                          ↓
           Next.js 16                  FastAPI :8000
        (all client comps)           nginx reverse proxy
```

- **前端：** Next.js 16 App Router，所有页面均为 `'use client'`（无 SSR）
- **后端：** FastAPI async，~35 个 API 端点，SQLAlchemy async ORM
- **数据库：** 默认 SQLite（`backend/app.db`），可切换至 PostgreSQL
- **支付：** Creem（`CREEM_API_KEY` 等环境变量为空时 Pro 升级返回 502）
- **AI：** DeepSeek（`deepseek-chat` 模型，智能粘贴 + AI 列检测）
- **邮件：** Resend API > SMTP > noop（三层回退）
- **限流：** slowapi，per-IP（`X-Forwarded-For` 感知）
- **监控：** Sentry（后端 sentry-sdk + 前端 @sentry/browser）
- **日志：** 标准 Python logging + 可选 JSON 结构化输出（`LOG_JSON=1`）
- **分析：** Vercel Analytics（前端）

---

## 3. 目录结构（仅关键目录）

```
product-tool/
├── backend/                      # FastAPI 后端
│   ├── main.py                   # 应用入口 + 所有 35 个 API 端点 (2227行)
│   ├── auth.py                   # JWT 鉴权 + 密码哈希 + 用户查询
│   ├── database.py               # SQLAlchemy ORM (User, Product, Quotation)
│   ├── payment.py                # Creem 结账 + webhook 验证
│   ├── mailer.py                 # 邮件发送 (Resend/SMTP/noop)
│   ├── sanitize.py               # XSS 输入清洗 (html.escape)
│   ├── logger.py                 # JSON 结构化日志设置
│   ├── universal_parser.py       # 通用解析器（3 层策略）
│   ├── ai_parser.py              # DeepSeek AI 列检测 + 文本转产品
│   ├── score.py                  # 双解析器信号组合评分
│   ├── product_repo.py           # 产品 CRUD 仓库
│   ├── migrate_data.py           # SQLite → PostgreSQL 迁移
│   ├── requirements.txt          # Python 依赖
│   ├── pytest.ini                # 测试配置
│   └── tests/                    # 测试套件（4 个文件，37 个测试）
│       ├── conftest.py           # 内存 SQLite 测试夹具
│       ├── test_auth.py          # 19 个测试（注册/登录/改密/忘记/重置）
│       ├── test_products.py      # 7 个产品测试 (CRUD + XSS)
│       ├── test_payment.py       # 4 个支付 webhook 测试
│       └── test_quotation.py     # 6 个报价/发票测试
├── landing/                      # Next.js 前端
│   ├── app/                      # 页面路由 (App Router)
│   │   ├── page.js               # 首页（文件上传 + 解析 + 报价生成）
│   │   ├── layout.js             # 根布局（字体、元数据、分析、Sentry）
│   │   ├── pricing/page.js       # 定价页 ($9.99/月 Pro)
│   │   ├── how-it-works/page.js  # 功能导览
│   │   ├── login/page.js         # 登录
│   │   ├── register/page.js      # 注册（用户名 + 邮箱 + 密码）
│   │   ├── forgot-password/page.js # 忘记密码（邮箱表单）
│   │   ├── reset-password/page.js  # 通过邮箱令牌重置密码
│   │   ├── workspace/page.js     # 仪表盘（上传 + 产品库 + 历史）
│   │   ├── account/page.js       # 账户设置（公司 + 银行信息）
│   │   ├── terms/page.js         # 服务条款
│   │   ├── privacy/page.js       # 隐私政策
│   │   ├── payment/success/page.js # 支付成功（轮询 Pro 升级）
│   │   └── payment/cancel/page.js  # 支付已取消
│   ├── components/               # 共享 UI 组件
│   │   ├── Nav.js                # 导航栏
│   │   ├── Footer.js             # 页脚（含 ToS/隐私政策链接）
│   │   ├── ErrorBoundary.js      # 错误边界 + Sentry 捕获
│   │   ├── ClientLayout.js       # 围绕 ErrorBoundary 的薄封装
│   │   ├── LocaleToggle.js       # EN/中文 语言切换
│   │   └── SentryInit.js         # 前端 Sentry 初始化
│   ├── lib/                      # 工具库
│   │   ├── api.js                # API_BASE 配置
│   │   ├── auth.js               # 令牌存储 + 自动刷新 401
│   │   ├── i18n.js               # Context API i18n 提供者
│   │   ├── locale.js             # IP 检测 + localStorage 语言
│   │   └── errors.js             # 用户友好错误消息
│   ├── translations/             # i18n 翻译
│   │   ├── zh.json               # 中文
│   │   └── en.json               # 英文
│   ├── next.config.mjs           # Next.js 配置（CSP 头 + 安全头）
│   ├── package.json              # 前端依赖
│   └── README.md                 # 前端说明
├── product_tool/                 # 核心解析引擎（Python 包）
│   ├── src/
│   │   ├── core/                 # 解析器
│   │   │   ├── excel_parser_v3.py
│   │   │   ├── doc_parser.py
│   │   │   ├── pdf_parser.py
│   │   │   ├── detector.py       # 格式检测
│   │   │   └── image.py          # 图片匹配/提取
│   │   ├── output/               # 输出生成器
│   │   │   ├── quotation_excel.py
│   │   │   ├── pdf_generator.py
│   │   │   └── pi_generator.py
│   │   ├── packing/              # 装箱单 + 商业发票
│   │   └── shared_keywords.py    # 解析关键词定义
│   ├── tests/                    # 12 个测试文件
│   └── categories.json           # 产品分类
├── docs/                         # 人类可读文档
│   ├── 系统架构与功能实现文档.md
│   ├── 解析器架构与配置.md
│   ├── 部署指南.md
│   └── 已知限制.md
├── scripts/                      # 运维脚本
│   ├── backup.sh                 # Linux 备份脚本（crontab）
│   ├── backup.ps1                # Windows 备份脚本
│   ├── add_excel_data.py         # 一次性脚本（已归档）
│   └── cleanup_data.py
├── .github/workflows/
│   ├── ci.yml                    # CI（后端测试 + 前端 lint）
│   └── deploy.yml                # 推送到主分支时 SSH 部署
├── ARCHITECTURE.md               # 英文架构文档
├── README.md                     # 项目概览
├── CHANGELOG.md                  # 版本历史
├── CONTRIBUTING.md               # 贡献指南
├── SECURITY.md                   # 安全策略
├── AGENTS.md                     # 代理指令（更简短）
├── findings.md                   # 调研发现
├── progress.md                   # 进度追踪
└── task_plan.md                  # 任务清单（已完成项已打勾）
```

---

## 4. 完整 API 端点目录

### 认证（`/api/auth/`）

| 方法 | 路径 | 速率限制 | 认证 | 参数 |
|------|------|:--------:|:----:|------|
| POST | `/register` | 5次/分钟 | 否 | `username`, `email`, `password` (Form) |
| POST | `/login` | 5次/分钟 | 否 | `username`, `password` (Form) |
| POST | `/refresh` | 无 | Cookie | httpOnly `refresh_token` cookie |
| PUT | `/change-password` | 无 | 是 | `old_password`, `new_password` (Form) |
| POST | `/forgot-password` | 3次/分钟 | 否 | `email` (Form) → 发送重置邮件 |
| POST | `/reset-password` | 5次/分钟 | 否 | `token`, `new_password` (Form) |
| GET | `/user/me` | 无 | 是 | 返回用户信息 |
| GET | `/user/usage` | 无 | 是 | 返回上传/产品数量统计 |

### 解析

| 方法 | 路径 | 速率限制 | 认证 |
|------|------|:--------:|:----:|
| POST | `/api/parse` | 20次/分钟 | 可选 |
| POST | `/api/parse/with-ai` | 无 | 可选 |
| POST | `/api/parse-text-products` | 无 | Pro 必填 |

### 产品与报价

| 方法 | 路径 | 认证 |
|------|------|:----:|
| GET/POST | `/api/products` | 是 |
| DELETE | `/api/products/{id}` | 是 |
| POST | `/api/products/batch-delete` | 是 |
| GET | `/api/quotations` | 是 |
| GET | `/api/quotations/{id}/download` | 是 |
| DELETE | `/api/quotations/{id}` | 是 |
| POST | `/api/quotations/batch-delete` | 是 |

### 文档生成

| 方法 | 路径 | 认证 |
|------|------|:----:|
| POST | `/api/quotation` | 可选 |
| POST | `/api/quotation/pdf` | 可选 |
| POST | `/api/pi` | Pro 必填 |
| POST | `/api/packing` | Pro 必填 |
| POST | `/api/invoice` | Pro 必填 |

### 支付

| 方法 | 路径 | 认证 |
|------|------|:----:|
| POST | `/api/payment/create-checkout` | 是 |
| POST | `/api/payment/webhook` | HMAC |

### 模板与配置

| 方法 | 路径 | 认证 |
|------|------|:----:|
| POST | `/api/template/upload` | 否 |
| POST/GET | `/api/template` | 是 |
| POST/GET/DELETE | `/api/template/document/{type}` | 混合 |
| POST/GET | `/api/bank/{save,load}` | 是 |
| POST | `/api/company/logo` | 是 |
| GET | `/api/images` | 否（路径白名单） |

### 通用

| 方法 | 路径 | 认证 |
|------|------|:----:|
| GET | `/api/health` | 否 |
| GET | `/api/exchange-rate` | 否 |

---

## 5. 数据库 Schema

### `users` 表

| 列 | 类型 | 约束 |
|----|------|------|
| id | Integer PK | 自增 |
| username | String(100) | 唯一，索引 |
| email | String(255) | 唯一，可空 |
| password_hash | String(255) | 非空（bcrypt） |
| tier | String(20) | 默认 'free'（'free' 或 'pro'） |
| upload_count | Integer | 默认 0 |
| upload_month | String(7) | 默认 '' (YYYY-MM) |
| stripe_customer_id | String(100) | 可空（Creem 客户 ID） |
| subscription_id | String(100) | 可空（Creem 订阅 ID） |
| subscription_end | DateTime | 可空 |
| created_at | DateTime | 默认 utcnow |

免费用户限制：每月 20 次上传，最多 200 个产品。Pro 无限制。

### `web_products` 表 — 20 列

关键列：id, user_id(FK), model, name_zh, name_en, spec_zh, spec_en, price_rmb, price_cny, price_usd, currency, image_path, category, carton_size, gross_weight, net_weight, cbm, units_per_carton, packing_type, created_at

### `web_quotations` 表 — 6 列

id, user_id(FK), product_ids (JSON 文本), file_name, file_path, created_at

---

## 6. 环境变量（`backend/.env`）

| 变量 | 必填 | 说明 |
|------|:-----:|------|
| `JWT_SECRET_KEY` | ✅ | 最少 32 字符 |
| `BASE_URL` | ✅ | 前端 URL，用于 CORS |
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek AI |
| `DATABASE_URL` | 否 | 默认为 `sqlite+aiosqlite:///./app.db` |
| `CREEM_API_KEY` | 否 | Creem 支付 |
| `CREEM_WEBHOOK_SECRET` | 否 | Creem webhook HMAC |
| `CREEM_PRODUCT_ID_PRO` | 否 | Creem 产品 ID |
| `SENTRY_DSN` | 否 | Sentry 错误监控 |
| `RESEND_API_KEY` | 否 | Resend 邮件 API |
| `SMTP_HOST` | 否 | SMTP 服务器 |
| `SMTP_PORT` | 否 | SMTP 端口（默认 587） |
| `SMTP_USER` | 否 | SMTP 用户名 |
| `SMTP_PASSWORD` | 否 | SMTP 密码 |
| `LOG_JSON` | 否 | 设置为 1 启用 JSON 日志 |

**Vercel 前端环境变量：** `NEXT_PUBLIC_API_URL`（指向 `https://api.quoteflow.it.com`）+ `NEXT_PUBLIC_SENTRY_DSN`（可选）

---

## 7. 开发命令

```bash
# 首次设置
cd backend && python -m venv venv && venv\Scripts\pip install -r requirements.txt
cd landing && npm install

# 启动开发环境（需要 2 个终端）
# 终端 1：backend
cd backend && venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# 终端 2：frontend
cd landing && npm run dev

# 运行测试
cd backend && venv\Scripts\python -m pytest tests/ -v        # 全部测试
cd backend && venv\Scripts\python -m pytest tests/test_auth.py -v  # 仅认证

# 生产启动（VPS）
cd backend
nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &
```

---

## 8. 关键设计决策

1. **双解析器 + 评分：** 通用解析器（`universal_parser.py`，3 层策略：KV→表格→内容驱动）与专用解析器（`run.parse_file`）并行运行。`score.py` 对两个结果评分，高分者胜出。不再按数量比较。
2. **可选认证：** 首页允许匿名上传/解析（无需注册）。已认证用户获得上传计数和产品库功能。
3. **全客户端组件：** 前端全部为 `'use client'`。无服务器端渲染。简化部署但限制 SEO。
4. **SQLite 默认：** 小型部署零配置。通过 `DATABASE_URL` 切换至 PostgreSQL。
5. **httpOnly 刷新令牌：** 访问令牌存储于 localStorage（15 分钟），刷新令牌为 httpOnly cookie（7 天）。`auth.js` 中的自动刷新包装器在 401 时透明重试。
6. **邮件优先级：** `mailer.py` → Resend API（首选）→ SMTP（备选）→ noop（开发/仅日志）。
7. **nginx 代理：** slowapi 速率限制使用自定义 `_get_real_ip()`，从 `X-Forwarded-For` 头读取真实客户端 IP。
8. **输入清洗：** 所有文本字段在入库前执行 `html.escape`（`sanitize.py` → 产品存储端点）。
9. **无 WebSocket：** 100% REST API。全部请求-响应。
10. **Vercel + 阿里云：** 前端托管于 Vercel（边缘 CDN），后端托管于阿里云新加坡 VPS（低延迟，主要面向中国外贸用户）。

---

## 9. 常见陷阱

| 陷阱 | 解决方法 |
|------|----------|
| **Python 路径问题：** `python` 可能解析至 Microsoft Store 版本，而非本地安装版本。使用显式路径，或为 backend 创建 venv。 |
| **`sys.path` 魔法：** `main.py` 将 `product_tool/src/` 和 `product_tool/` 添加到路径中，因此 `from src.company import ...` 可解析至 `product_tool/src/company.py`。勿与根目录的 `src/`（CLI 入口使用）混淆——不重叠。 |
| **Creem 支付：** 若 `CREEM_API_KEY` 为空，Pro 升级返回 502。需在 Creem 设置 4 步（产品 + API 密钥 + webhook + 环境变量）。 |
| **图片调整大小 BytesIO：** `quotation_excel.py` 使用临时文件（非 BytesIO），因 openpyxl 延迟加载时无法读取 BytesIO。在调用 `create_quotation()` 前，先于 main.py 中通过 `pre-resize` 预热调整大小缓存。 |
| **速率限制器要求 `request` 参数：** 使用 `@limiter.limit()` 的端点必须将 `request: Request` 作为参数。忘记添加将导致 `Exception: No "request" argument`。 |
| **test_auth.py 中的测试隔离：** 所有测试共享同一 slowapi 限制器（内存存储）。do NOT write tests that assume clean rate-limit state across test functions. Accept 429 alongside 400 for late-register tests. |
| **WeasyPrint 字体：** PDF 生成可能因缺少系统字体而失败。生产环境需安装中文+拉丁字体，或接受 500 错误。 |

---

## 10. 部署

**VPS 设置：**
```bash
# 克隆 + 安装
git clone <repo> /home/admin/product-tool
cd /home/admin/product-tool/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 创建 backend/.env（参考 backend/.env.example）
# 通过 nginx 运行（反向代理 :8000）
nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &
```

**Vercel 设置：** Root Directory = `landing`，环境变量 = `NEXT_PUBLIC_API_URL=https://api.quoteflow.it.com`

**备份：** `scripts/backup.sh` (Linux) → crontab：`0 2 * * * /home/admin/product-tool/scripts/backup.sh >> /home/admin/product-tool/backups/backup.log 2>&1`
