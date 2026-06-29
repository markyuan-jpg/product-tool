# CLAUDE.md — QuoteFlow 完整代理上下文

> **目标受众：** AI 编码代理（Claude、OpenCode 等）
> **最后更新：** 2026-06-29
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
- **会话：** 匿名模式 — 前端 `crypto.randomUUID()` → `X-Session-ID` header → 后端 `GuestUser`。JWT 登录/注册代码休眠保留。
- **支付：** Creem（休眠中，端点和 webhook 仍在）
- **AI：** DeepSeek（`deepseek-chat` 模型），仅 `parse/with-ai` + `parse-text-products` 使用。前端 Smart Paste UI 已移除（API 不公开）。
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
│   ├── main.py                   # 应用入口 + 所有 35 个 API 端点 (2311行)
│   │                            # 含 SessionMiddleware + GuestUser + 限流
│   ├── auth.py                   # JWT 鉴权 + 密码哈希 + 用户查询（休眠中）
│   ├── database.py               # SQLAlchemy ORM (User, Product, Quotation)（休眠中）
│   ├── payment.py                # Creem 结账 + webhook 验证（休眠中）
│   ├── mailer.py                 # 邮件发送 (Resend/SMTP/noop)
│   ├── sanitize.py               # XSS 输入清洗 (html.escape)
│   ├── logger.py                 # JSON 结构化日志设置
│   ├── universal_parser.py       # 通用解析器（4 层策略 + 公式列检测）
│   ├── ai_parser.py              # DeepSeek AI 列检测 + 文本转产品
│   ├── score.py                  # 双解析器信号组合评分
│   ├── product_repo.py           # 产品 CRUD 仓库（含 CREATE TABLE IF NOT EXISTS）
│   ├── migrate_data.py           # SQLite → PostgreSQL 迁移
│   ├── requirements.txt          # Python 依赖
│   ├── pytest.ini                # 测试配置
│   └── tests/                    # 测试套件（4 个文件，34 个测试）
│       ├── conftest.py           # 内存 SQLite 测试夹具
│       ├── test_auth.py          # 19 个测试（注册/登录/改密/忘记/重置）
│       ├── test_products.py      # 7 个产品测试 (CRUD + XSS)
│       ├── test_payment.py       # 4 个支付 webhook 测试
│       └── test_quotation.py     # 6 个报价/发票测试
├── landing/                      # Next.js 前端
│   ├── app/                      # 页面路由 (App Router)
│   │   ├── page.js               # 首页（文件上传 + 解析 + 报价生成）
│   │   ├── layout.js             # 根布局（字体、元数据、分析、Sentry）
│   │   ├── pricing/page.js       # 定价页
│   │   ├── how-it-works/page.js  # 功能导览
│   │   ├── login/page.js         # 登录（休眠，Nav 隐藏）
│   │   ├── register/page.js      # 注册（休眠，Nav 隐藏）
│   │   ├── forgot-password/page.js # 忘记密码（邮箱表单）
│   │   ├── reset-password/page.js  # 通过邮箱令牌重置密码
│   │   ├── workspace/page.js     # 工作台（匿名免登，X-Session-ID 会话）
│   │   ├── account/page.js       # 账户设置（Nav 隐藏）
│   │   ├── terms/page.js         # 服务条款
│   │   ├── privacy/page.js       # 隐私政策
│   │   ├── payment/success/page.js # 支付成功（休眠）
│   │   └── payment/cancel/page.js  # 支付已取消（休眠）
│   ├── components/               # 共享 UI 组件
│   │   ├── Nav.js                # 导航栏（Home/HowItWorks/Workspace + 语言切换）
│   │   ├── Footer.js             # 页脚（含 ToS/隐私政策链接）
│   │   ├── ErrorBoundary.js      # 错误边界 + Sentry 捕获
│   │   ├── ClientLayout.js       # 围绕 ErrorBoundary 的薄封装
│   │   ├── LocaleToggle.js       # EN/中文 语言切换
│   │   └── SentryInit.js         # 前端 Sentry 初始化
│   ├── lib/                      # 工具库
│   │   ├── api.js                # API_BASE 配置
│   │   ├── auth.js               # 令牌存储 + 自动刷新 401（休眠中）
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
│   │   │   └── image.py          # 三路合并图片提取 (openpyxl+DISPIMG+drawing)
│   │   ├── output/               # 输出生成器
│   │   │   ├── quotation_excel.py
│   │   │   ├── pdf_generator.py
│   │   │   └── pi_generator.py
│   │   ├── packing/              # 装箱单 + 商业发票
│   │   ├── utils/                # dimension_extractor.py
│   │   └── shared_keywords.py    # 解析关键词定义
│   ├── tests/                    # 12 个测试文件（部分因硬编码路径不可用）
│   └── categories.json           # 产品分类
├── docs/                         # 人类可读文档
│   ├── 系统架构与功能实现文档.md
│   ├── README.md                 # 文档导航索引
│   └── _ARCHIVED_*.md            # 已归档旧文档
├── scripts/                      # 运维脚本
│   ├── backup.sh                 # Linux 备份脚本（crontab）
│   └── backup.ps1                # Windows 备份脚本
├── .github/workflows/
│   └── ci.yml                    # CI（后端测试 + 前端 lint）
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
| GET | `/user/me` | 无 | 是 | 返回用户信息（休眠中） |
| GET | `/user/usage` | 无 | 是 | 返回上传/产品数量统计（休眠中） |

### 解析

| 方法 | 路径 | 速率限制 | 认证 |
|------|------|:--------:|:----:|
| POST | `/api/parse` | 20次/分钟 | GuestUser |
| POST | `/api/parse/with-ai` | 无 | GuestUser（需 DEEPSEEK_API_KEY） |
| POST | `/api/parse-text-products` | 无 | GuestUser（需 DEEPSEEK_API_KEY） |

> `/parse-text-products` 和 `/parse/with-ai` 端点存在但前端 UI 已移除（DeepSeek API 不对外公开）。

### 产品与报价

| 方法 | 路径 | 认证 |
|------|------|:----:|
| GET/POST | `/api/products` | GuestUser |
| DELETE | `/api/products/{id}` | GuestUser |
| POST | `/api/products/batch-delete` | GuestUser |
| GET | `/api/quotations` | GuestUser |
| GET | `/api/quotations/{id}/download` | GuestUser |
| DELETE | `/api/quotations/{id}` | GuestUser |
| POST | `/api/quotations/batch-delete` | GuestUser |

### 文档生成

| 方法 | 路径 | 认证 |
|------|------|:----:|
| POST | `/api/quotation` | GuestUser |
| POST | `/api/quotation/pdf` | GuestUser |
| POST | `/api/pi` | GuestUser |
| POST | `/api/packing` | GuestUser |
| POST | `/api/invoice` | GuestUser |

> `require_pro` 已改为空操作，所有文档生成功能对全部用户开放。

### 支付

| 方法 | 路径 | 认证 |
|------|------|:----:|
| POST | `/api/payment/create-checkout` | 是（休眠中） |
| POST | `/api/payment/webhook` | HMAC（休眠中） |

### 模板与配置

| 方法 | 路径 | 认证 |
|------|------|:----:|
| POST | `/api/template/upload` | 否 |
| POST/GET | `/api/template` | GuestUser |
| POST/GET/DELETE | `/api/template/document/{type}` | 混合 |
| POST/GET | `/api/bank/{save,load}` | GuestUser |
| POST | `/api/company/logo` | GuestUser |
| GET | `/api/images` | 否（路径白名单，支持 `\|\|` 多路径） |

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

> **当前为匿名模式，users 表未启用。GuestUser 的 user_id 为 UUID 字符串。**

### `web_products` 表 — 20 列

关键列：id, user_id(TEXT), model, name_zh, name_en, spec_zh, spec_en, price_rmb, price_cny, price_usd, currency, image_path（`||` 分隔多图）, category, carton_size, gross_weight, net_weight, cbm, units_per_carton, packing_type, created_at

### `web_quotations` 表 — 6 列

id, user_id(TEXT), product_ids (JSON 文本), file_name, file_path, created_at

> 两表均在首次连接时自动创建（`CREATE TABLE IF NOT EXISTS`）。

---

## 6. 环境变量（`backend/.env`）

| 变量 | 必填 | 说明 |
|------|:-----:|------|
| `JWT_SECRET_KEY` | ✅ | 最少 32 字符 |
| `BASE_URL` | ✅ | 前端 URL，用于 CORS |
| `DEEPSEEK_API_KEY` | 否 | DeepSeek AI（不设置仅影响 parse/with-ai 和智能粘贴） |
| `DATABASE_URL` | 否 | 默认为 `sqlite+aiosqlite:///./app.db` |
| `CREEM_API_KEY` | 否 | Creem 支付（休眠中） |
| `CREEM_WEBHOOK_SECRET` | 否 | Creem webhook HMAC（休眠中） |
| `CREEM_PRODUCT_ID_PRO` | 否 | Creem 产品 ID（休眠中） |
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
cd backend && venv\Scripts\python -m pytest tests/ -v        # 全部测试（34 个）
cd backend && venv\Scripts\python -m pytest tests/test_auth.py -v  # 仅认证

# 生产启动（VPS）
cd backend
nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &
```

---

## 8. 关键设计决策

1. **双解析器 + 评分：** 通用解析器（`universal_parser.py`，4 层策略：KV→表格→内容驱动→无表头）与专用解析器（`run.parse_file`）并行运行。`score.py` 对两个结果评分，高分者胜出。不再按数量比较。
2. **全站匿名模式：** 前端 `crypto.randomUUID()` → `localStorage.quote_session_id` → 每次请求 `X-Session-ID` header。后端 `GuestUser(session_id)` 绑定会话。无需注册/登录。JWT 代码休眠保留。
3. **全客户端组件：** 前端全部为 `'use client'`。无服务器端渲染。简化部署但限制 SEO。
4. **SQLite 默认：** 小型部署零配置。通过 `DATABASE_URL` 切换至 PostgreSQL。表自动创建。
5. **图片三路合并提取：** 三路独立提取（openpyxl 浮动图 + DISPIMG 嵌入图 + drawing XML），set 去重后 `||` 拼接路径。多列检测 + exact tolerance 匹配。
6. **nginx 代理：** slowapi 速率限制使用自定义 `_get_real_ip()`，从 `X-Forwarded-For` 头读取真实客户端 IP。
7. **输入清洗：** 所有文本字段在入库前执行 `html.escape`（`sanitize.py` → 产品存储端点）。
8. **无 WebSocket：** 100% REST API。全部请求-响应。
9. **Vercel + 阿里云：** 前端托管于 Vercel（边缘 CDN），后端托管于阿里云新加坡 VPS（低延迟，主要面向中国外贸用户）。

---

## 9. 常见陷阱

| 陷阱 | 解决方法 |
|------|----------|
| **Python 路径问题：** `python` 可能解析至 Microsoft Store 版本，而非本地安装版本。使用显式路径，或为 backend 创建 venv。 |
| **`sys.path` 魔法：** `main.py` 将 `product_tool/src/` 和 `product_tool/` 添加到路径中，因此 `from src.company import ...` 可解析至 `product_tool/src/company.py`。勿与根目录的 `src/`（CLI 入口使用）混淆——不重叠。 |
| **Creem 支付：** 若 `CREEM_API_KEY` 为空，Pro 升级返回 502。当前为匿名模式，支付休眠中。 |
| **图片调整大小 BytesIO：** `quotation_excel.py` 使用临时文件（非 BytesIO），因 openpyxl 延迟加载时无法读取 BytesIO。在调用 `create_quotation()` 前，先于 main.py 中通过 `pre-resize` 预热调整大小缓存。 |
| **速率限制器要求 `request` 参数：** 使用 `@limiter.limit()` 的端点必须将 `request: Request` 作为参数。忘记添加将导致 `Exception: No "request" argument`。 |
| **test_auth.py 中的测试隔离：** 所有测试共享同一 slowapi 限制器（内存存储）。do NOT write tests that assume clean rate-limit state across test functions. Accept 429 alongside 400 for late-register tests. |
| **WeasyPrint 字体：** PDF 生成可能因缺少系统字体而失败。生产环境需安装中文+拉丁字体，或接受 500 错误。 |
| **图片路径缓存：** `image.py` 的 `_image_cache` 按 `image_col` 参数缓存。多列检测会多次调用 `extract_embedded_images`（每列一次），确保缓存键正确。 |
| **X-Session-ID 跨子域：** quoteflow.it.com → api.quoteflow.it.com 跨域请求不能依赖 cookie。前端在 `localStorage` 存 UUID，通过 `X-Session-ID` header 发送。所有 workspace fetch 加 `credentials: 'include'` 兜底。 |

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
