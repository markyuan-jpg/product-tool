# QuoteFlow — 产品报价单在线生成工具

在线上传 Excel / PDF / Word 产品文件 → 自动解析产品信息 → 一键生成报价单 / PI / Packing List。

**网址：** [quoteflow.it.com](https://quoteflow.it.com)

---

## 技术栈

| 层 | 技术 |
|----|------|
| 前端 | Next.js 16 + React 19 + Tailwind CSS v4 |
| 后端 | FastAPI (Python 3.11+) |
| 数据库 | SQLite (默认) / PostgreSQL (可选) |
| 支付 | Creem |
| 邮件 | Resend / SMTP |
| 监控 | Sentry |
| 部署 | 阿里云 VPS (后端) + Vercel (前端) |

## 快速开始

### 环境变量

在 `backend/.env` 中设置：

```env
JWT_SECRET_KEY=你的密钥
BASE_URL=https://quoteflow.it.com
DEEPSEEK_API_KEY=你的DeepSeek密钥
```

可选（按需）：
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/db  # 默认 SQLite
CREEM_API_KEY=          # 支付
CREEM_WEBHOOK_SECRET=   # 支付 Webhook
CREEM_PRODUCT_ID_PRO=   # 支付产品ID
SENTRY_DSN=             # 错误监控
RESEND_API_KEY=         # 邮件（或 SMTP_* 变量）
LOG_JSON=1              # 启用结构化 JSON 日志
```

### 本地开发

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 8000

# 前端
cd landing
npm install
npm run dev
# → http://localhost:3000
```

### 生产部署

详见 `docs/部署指南.md`

---

## 功能

| 功能 | Free | Pro |
|------|:----:|:---:|
| 文件上传解析 (Excel/PDF/Word) | ✅ | ✅ |
| 报价单生成 (Excel/PDF) | ✅ | ✅ |
| 产品库管理 | ✅ (最多200个) | ✅ (无限) |
| 上传次数/月 | 20次 | 无限 |
| 智能粘贴 (AI 提取) | ❌ | ✅ |
| PI 形式发票 | ❌ | ✅ |
| Packing List | ❌ | ✅ |
| Commercial Invoice | ❌ | ✅ |

**定价：** $9.99/月 (Pro)

---

## 项目结构

```
├── backend/             # FastAPI 后端
│   ├── main.py          # API 入口 (35 个端点)
│   ├── auth.py          # JWT 鉴权
│   ├── database.py      # SQLAlchemy ORM
│   ├── payment.py       # Creem 支付
│   ├── mailer.py        # 邮件发送
│   ├── sanitize.py      # 输入清洗
│   ├── logger.py        # 结构化日志
│   └── requirements.txt
├── landing/             # Next.js 前端
│   ├── app/             # 页面路由
│   ├── components/      # 公共组件
│   ├── lib/             # 工具库 (auth, i18n, api)
│   └── translations/    # 中/英文翻译
├── product_tool/        # 核心解析引擎
│   ├── src/core/        # 解析器 (Excel/DOCX/PDF)
│   ├── src/output/      # 报价单生成
│   └── tests/           # 解析器测试
└── docs/                # 技术文档
```

---

## 许可

Proprietary — All rights reserved.
