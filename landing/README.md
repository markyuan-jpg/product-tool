# QuoteFlow 前端

Next.js 16 App Router 前端 — 产品报价单在线生成工具。

> 📖 完整项目文档见根目录 [README.md](../README.md) 和 [docs/项目手册.md](../docs/项目手册.md)。

## 启动

```bash
npm install
npm run dev        # 开发 (http://localhost:3000)
npm run build && npm start  # 生产
```

## 环境变量

在 Vercel Dashboard 或 `.env.local` 中设置：

| 变量 | 值 |
|------|-----|
| `NEXT_PUBLIC_API_URL` | `https://api.quoteflow.it.com` 或本地 `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN（可选） |

## 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | 首页 | 文件上传 + 解析 + 报价生成（匿名可用） |
| `/pricing` | 定价 | Free vs Pro ($9.99/月) |
| `/how-it-works` | 工作原理 | 功能导览 |
| `/login` | 登录 | |
| `/register` | 注册 | 用户名 + 邮箱 + 密码 |
| `/forgot-password` | 忘记密码 | 邮箱发送重置链接 |
| `/reset-password` | 重置密码 | token 验证后设新密码 |
| `/workspace` | 工作台 | 产品库 + 报价历史 + 生成（需登录） |
| `/account` | 账户设置 | 公司信息 + 银行信息 |
| `/terms` | 服务条款 | |
| `/privacy` | 隐私政策 | |
| `/payment/success` | 支付成功 | 轮询 Pro 升级状态 |
| `/payment/cancel` | 支付取消 | |

## 目录结构

```
landing/
├── app/                       # App Router 页面
├── components/                # 共享组件 (Nav, Footer, ErrorBoundary)
├── lib/                       # 工具库 (auth, i18n, api, errors)
├── translations/              # 中/英文翻译
├── next.config.mjs            # CSP 安全头配置
└── package.json
```

## 技术栈

- React 19 (全 `'use client'` 组件)
- Tailwind CSS v4
- @vercel/analytics
- @sentry/browser (可选错误监控)
- Context API i18n (中/英文切换)
