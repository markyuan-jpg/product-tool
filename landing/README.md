# 报价整合工具 — 前端 (landing/)

外贸报价整合系统，基于 Next.js 16 + Tailwind CSS 4。

## 快速开始

```bash
npm install
npm run dev        # 开发模式，默认 localhost:3000
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址（生产必设） | `http://127.0.0.1:8000` |

## 目录结构

```
app/
├── page.js            # 首页（上传解析 + 生成报价）
├── workspace/page.js  # 工作台（产品库 + 报价历史）
├── login/page.js      # 登录
├── register/page.js   # 注册
├── pricing/page.js    # 定价
├── how-it-works/      # 工作原理
├── layout.js          # 全局布局 + ErrorBoundary
├── globals.css        # 设计系统变量
components/
├── ErrorBoundary.js   # 错误边界组件
├── ClientLayout.js    # 客户端包裹层
lib/
├── api.js             # API 地址配置
├── auth.js            # Token/用户管理
├── errors.js          # 中文友好错误消息
```

## 部署

```bash
npm run build
npx vercel --prod
```

生产环境必须设置 `NEXT_PUBLIC_API_URL` 指向部署的后端地址。


## Recent Updates
- RMB price column (price_cny) full pipeline: parse → save → display → export
- Export column selection: 11 checkboxes in export settings
- Language fixes: cur_sym ($/¥), PDF header translation, payment terms parsing
- Customer delete in company info section
- Commercial invoice & packing list preview now matches actual output

## Recent Updates (Phase 3-4)
- PostgreSQL + ORM (Supabase)
- Creem subscription payments (checkout + webhook)
- Dual-token auth (access + refresh httpOnly cookie)
- Usage quota display in workspace
- Bug fixes: change-password async ORM, quota await/db, user.id dict access
