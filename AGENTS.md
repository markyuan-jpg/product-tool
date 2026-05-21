# 项目备注

## 启动方式

```bash
# 后端 (FastAPI, port 8000)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 --timeout-keep-alive 120

# 前端 (Next.js, port 3000)
cd landing
npm run dev     # 开发
npm run build && npm start  # 生产
```

快捷脚本：`start.bat`（后端），前端需手动启动。

## Python 版本 & 路径

本地安装 Python 3.14.4，同时可能存在 Microsoft Store 版 Python。
`python` 命令可能解析到非预期路径。如遇问题，显式指定：

```powershell
& "C:\Users\marky\AppData\Local\Python\pythoncore-3.14-64\python.exe"
```

推荐：为 backend 创建专用 venv：
```bash
cd backend
python -m venv venv
.\venv\Scripts\pip install -r requirements.txt
.\venv\Scripts\python -m uvicorn main:app ...
```

## 模块导入路径

`backend/main.py` 通过 sys.path 添加了 `product_tool/src/` 和 `product_tool/`，
所以 `from src.company import ...` 实际解析到 `product_tool/src/company.py`。
根目录 `src/` 由 CLI 入口（`run.py`、`app.py` 等）使用。与 `product_tool/src/` 模块名完全不重叠，两者共存。

## 数据库

- **产品/报价历史**：SQLite, 路径 `~/.product_tool/products.db`
- **用户/认证**：SQLite, 路径 `backend/app.db`（由 `DATABASE_URL` 控制）
- 可切换至 PostgreSQL：修改 `DATABASE_URL` 环境变量

## 支付 (Creem)

`CREEM_API_KEY`、`CREEM_WEBHOOK_SECRET`、`CREEM_PRODUCT_ID_PRO` 为空时，
Pro 升级返回 502。如需启用，在 `backend/.env` 中配置。

启用步骤：
1. 注册 Creem → 创建产品 → 复制 Product ID 到 `CREEM_PRODUCT_ID_PRO`
2. Creem Settings → API Keys → 复制 Secret Key 到 `CREEM_API_KEY`
3. Creem Settings → Webhooks → 添加 URL `https://你的railway域名.up.railway.app/api/payment/webhook` → 复制 Signing Secret 到 `CREEM_WEBHOOK_SECRET`
4. Railway → Variables → 加上这 3 个变量

## 解析器择优系统

`backend/main.py` 对同一个文件同时运行两个解析器：
1. **通用解析器**（`universal_parser.py`）：三层策略（KV→表格→内容驱动）
2. **专用解析器**（`run.parse_file`）：格式检测 + 6种专用解析器 + 多级 fallback

然后用 `backend/score.py` 的 **信号组合评分系统** 对两个结果评分，分高者胜。
评分维度：逐产品 7 级信号组合（真型号+价格+参数→+7） + 全局一致性加成。
不再使用旧的数量比较逻辑（谁产品多选谁）。

## 部署生产（Railway + Vercel）

### ⚠️ 做对这几件事才能部署成功

1. **`product_tool/` 必须在容器里** — Railway 的 Root Directory 必须**清空（空白）**，不能设成 `backend/`，否则 `product_tool/` 不会被复制进容器，所有 `from src.xxx import` 都会报错
2. **`railway.json` 必须是 JSON 格式**（不能是 TOML）— 放在**项目根目录**，且在 Railway Dashboard 手动添加 Config File 路径
3. **根目录必须有 `requirements.txt`** — Railpack 只扫描根目录检测 Python；`backend/requirements.txt` 不会被自动发现。内容直接写所有依赖，不能用 `-r backend/requirements.txt` 引用
4. **`product_tool/.gitignore` 不要误杀 `src/output/`** — `output/` 这个规则会匹配 `product_tool/src/output/`，导致 `quotation_excel.py` 等文件被 git 忽略、部署失败
5. **CSP 必须更新** — `landing/next.config.mjs` 的 `img-src` 需要加上 `https://*.up.railway.app`，否则产品图片被安全策略拦截（`Content Security Policy` 报错）

---

### 步骤一：准备代码文件

| 文件 | 位置 | 作用 |
|------|------|------|
| `vercel.json` | 项目根目录 | 告诉 Vercel 这是 Next.js 项目 |
| `railway.json` | 项目根目录 | 告诉 Railway 构建和启动方式 |
| `requirements.txt` | 项目根目录 | 根目录必须有一份，Railpack 依赖它 |

**`railway.json` 模板（必须放根目录）**
```json
{
  "build": {
    "watchPatterns": ["product_tool/**", "backend/**", "requirements.txt", "railway.json"]
  },
  "deploy": {
    "startCommand": "cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/api/health",
    "restartPolicyType": "always",
    "sleepOnIdle": true,
    "idleTimeoutMinutes": 5
  }
}
```

**`vercel.json` 模板（必须放根目录）**
```json
{ "framework": "nextjs" }
```

---

### 步骤二：Vercel 部署前端

| # | 操作 | 位置 |
|---|------|------|
| 1 | 创建项目，关联 GitHub repo | vercel.com → Add New → Project |
| 2 | Framework Preset = Next.js（自动检测） | — |
| 3 | Root Directory → 填入 `landing` | Settings → General → Root Directory |
| 4 | 加环境变量 `NEXT_PUBLIC_API_URL` | Settings → Environment Variables |
| 5 | 等部署完成，拿到域名（`xxx.vercel.app`） | Deployments |

> 注意：`vercel.json` 里的 `rootDirectory` 字段 Vercel 不支持，必须在 Dashboard 手动设置。

---

### 步骤三：Railway 部署后端

| # | 操作 | 位置 |
|---|------|------|
| 1 | 创建项目，关联 GitHub repo，Service 选根目录 | railway.app → New Project → Deploy from GitHub |
| 2 | **Root Directory 必须清空（空白）** | Settings → Root Directory |
| 3 | 添加 Config File 路径 `railway.json` | Settings → Config-as-code → Railway Config File → Add File Path |
| 4 | 加环境变量（见下表） | Variables → New Variable |
| 5 | 触发部署 | Deploy 按钮 或 ⇧+Enter |
| 6 | 拿到域名（`xxx.up.railway.app`） | Settings → Networking → Generate Domain（端口 8080） |

---

### 步骤四：必设环境变量

| 平台 | 变量 | 必填 | 说明 |
|------|------|:----:|------|
| Railway | `JWT_SECRET_KEY` | ✅ | JWT 签名密钥。生成：`python -c "import secrets; print(secrets.token_hex(32))"` |
| Railway | `BASE_URL` | ✅ | Vercel 前端域名（如 `https://xxx.vercel.app`），用于 CORS 白名单 |
| Railway | `DATABASE_URL` | 可选 | PostgreSQL 连接串（不填则默认用 SQLite） |
| Railway | `PRODUCT_TOOL_DB_PATH` | 可选 | 产品库 SQLite 路径（默认 `~/.product_tool/products.db`） |
| Railway | `CREEM_API_KEY` | 可选 | Creem 支付 |
| Railway | `CREEM_WEBHOOK_SECRET` | 可选 | Creem Webhook 签名 |
| Railway | `CREEM_PRODUCT_ID_PRO` | 可选 | Creem 产品 ID |
 | Railway | `GEMINI_API_KEY` | 可选 | AI 列检测（已弃用，改用 DeepSeek） |
| Railway | `DEEPSEEK_API_KEY` | ✅ | DeepSeek AI（智能粘贴 + AI 列检测） |
| Vercel | `NEXT_PUBLIC_API_URL` | ✅ | Railway 后端域名（如 `https://xxx.up.railway.app`） |

---

### 常见部署失败排查

| 错误 | 原因 | 修复 |
|------|------|------|
| `No Next.js version detected` | Vercel 找不到 `landing/package.json` | Dashboard → Root Directory 设成 `landing` |
| `No module named 'src'` | `product_tool/` 不在容器里 | Railway → Root Directory 清空 |
| `No module named 'src.output'` | `product_tool/.gitignore` 屏蔽了 `output/` | 把 gitignore 里的 `output/` 改成 `/output/` |
| `uvicorn: command not found` | 依赖没装 或 `railway.json` 不被识别 | 根目录放 `requirements.txt` + 手动添加 Config File 路径 |
| `Build skipped` / watchPatterns 不触发 | `watchPatterns` 不包含根文件 | 加上 `"requirements.txt"` 和 `"railway.json"` |
| `unable to open database file` | `~/.product_tool/` 目录不存在 | 确保 `_init_products_db()` 中 `mkdir(parents=True)` |
| 图片加载被 CSP 拦截 | `img-src` 没有允许 Railway 域名 | `next.config.mjs` 的 `img-src` 加上 `https://*.up.railway.app` |
| `connect-src` 限制 API 地址 | 后端换了端口/域名时未更新 CSP | `next.config.mjs` 的 `connect-src` 加上对应地址 |

---

## 国际化 (i18n)

前端全站支持中/英文切换，基于 Context API。

### 框架结构

| 文件 | 作用 |
|------|------|
| `landing/lib/i18n.js` | `LocaleProvider` / `useLocale()` hook / `t()` 翻译函数 |
| `landing/lib/locale.js` | IP 检测 + localStorage 持久化 |
| `landing/components/LocaleToggle.js` | 右上角 EN/中文 切换按钮 |
| `landing/translations/zh.json` | 中文翻译词条 |
| `landing/translations/en.json` | 英文翻译词条 |

### 语言检测优先级

1. localStorage `app_locale`（用户手动切换后持久化）
2. ip-api.com IP 定位（CN→zh，其他→en）
3. 兜底：zh

### 使用方式

```javascript
import { useLocale, t } from '@/lib/i18n';

function Component() {
  const { locale, ready } = useLocale();
  if (!ready) return null;
  return <p>{t('nav.home', locale)}</p>;
}
```

### 已覆盖页面

首页、工作原理、定价、登录、注册、忘记密码、支付结果、账户设置、工作台（含产品库/报价历史）、Nav、Footer、ErrorBoundary。

---

## 智能粘贴 (Smart Paste)

Pro 用户专属功能，粘贴任意格式产品文本 → AI 自动提取结构化数据。

### 工作流程

1. workspace 页面切换到「智能粘贴」tab
2. 粘贴产品描述（微信/邮件/笔记等任意格式）
3. 可选：拖入图片（文件名含型号自动匹配）
4. 点击「解析」→ 后端调 DeepSeek 提取产品
5. 结果展示在已有产品表格，可编辑后保存/生成报价单

### 后端

- 端点：`POST /api/parse-text-products`（需 Pro 用户）
- AI：`call_deepseek()` in `backend/ai_parser.py`
- 模型：`deepseek-chat`（DeepSeek 官方 API）

---

## 解析器修复记录

### DOCX 解析器 (`doc_parser.py`)

| 问题 | 修复 |
|------|------|
| 价格列被放进规格 | 表头匹配优先于内容推断（+8 分加权） |
| 编造价格（Moq 列误当价格） | `/box` `/pc` 后缀值排除出价格检测 |
| spec 含 Photo/Moq 等无关列 | 移除未映射列收集逻辑 |
| 表头值泄漏到数据行 | 首行不参与垂直合并传播 |
| 无型号列时 model 为空 | 用 name 作为 model |
| qty 没映射 | 添加 'moq' 到 qty 关键字 |
| 币种未识别 | 从价格列表头文本检测 USD/CNY |
| 图片按文件名顺序错配 | 解析 XML 检测每个单元格是否真有图片，按 `_row` 匹配 |

### Excel 解析器 (`excel_parser_v3.py`)

| 问题 | 修复 |
|------|------|
| 未映射列塞进 spec | 移除收集逻辑（同 doc_parser） |

### PDF 解析器 (`pdf_parser.py`)

| 问题 | 修复 |
|------|------|
| 表头值泄漏到数据行 | 首行不改值，只记录 |
| 图片位置硬塞 | 型号→文件名匹配不到就留空 |

### 图片匹配 (`image.py`)

| 问题 | 修复 |
|------|------|
| Excel 图片扩散到相邻产品 | 移除扩散逻辑 |
| 兜底时循环分配 | 只在序号范围内分配，不循环 |

### 报价单生成 (`quotation_excel.py`)

| 问题 | 修复 |
|------|------|
| USD 价格重复换算 | 检查产品原始 currency，仅非 USD 才换算 |
| 价格单元格格式为「自定义」非数值 | 显式设 `number_format = '#,##0.00'` |
| qty 单元格格式非数值 | 显式设 `number_format = '#,##0'` |
| 多价格不显示 | `price_raw` 追加到 spec 列 |
