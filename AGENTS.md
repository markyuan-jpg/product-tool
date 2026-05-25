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
3. Creem Settings → Webhooks → 添加 URL `https://api.quoteflow.it.com/api/payment/webhook` → 复制 Signing Secret 到 `CREEM_WEBHOOK_SECRET`
4. 在 `backend/.env` 或服务器环境变量加上这 3 个变量

## 解析器择优系统

`backend/main.py` 对同一个文件同时运行两个解析器：
1. **通用解析器**（`universal_parser.py`）：三层策略（KV→表格→内容驱动）
2. **专用解析器**（`run.parse_file`）：格式检测 + 6种专用解析器 + 多级 fallback

然后用 `backend/score.py` 的 **信号组合评分系统** 对两个结果评分，分高者胜。
评分维度：逐产品 7 级信号组合（真型号+价格+参数→+7） + 全局一致性加成。
不再使用旧的数量比较逻辑（谁产品多选谁）。

## 部署（VPS + Vercel）

后端运行在阿里云轻量应用服务器（新加坡），前端托管在 Vercel。

### 后端部署（VPS）

| 步骤 | 操作 |
|------|------|
| 1 | 购买 VPS（推荐 2 vCPU / 2GB 内存以上） |
| 2 | 安装 Python 3.10+、pip、git |
| 3 | `git clone` 项目到服务器 |
| 4 | `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt` |
| 5 | 创建 `backend/.env`（见下方环境变量表） |
| 6 | `nohup venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2 > app.log 2>&1 &` |
| 7 | 设置防火墙开放 8000 端口（TCP） |
| 8 | DNS：`api.quoteflow.it.com` → A 记录指向服务器 IP |

### 前端部署（Vercel）

| 步骤 | 操作 |
|------|------|
| 1 | Vercel 创建项目，关联 GitHub repo |
| 2 | Root Directory 设为 `landing` |
| 3 | 环境变量：`NEXT_PUBLIC_API_URL=https://api.quoteflow.it.com` |

### 环境变量（在 `backend/.env` 中设置）

| 变量 | 必填 | 说明 |
|------|:----:|------|
| `JWT_SECRET_KEY` | ✅ | JWT 签名密钥 |
| `BASE_URL` | ✅ | Vercel 前端域名，用于 CORS |
| `DATABASE_URL` | 可选 | PostgreSQL 连接串（默认 SQLite） |
| `DEEPSEEK_API_KEY` | ✅ | DeepSeek AI（智能粘贴 + AI 列检测） |
| `CREEM_API_KEY` | 可选 | Creem 支付 |
| `CREEM_WEBHOOK_SECRET` | 可选 | Creem Webhook 签名 |
| `CREEM_PRODUCT_ID_PRO` | 可选 | Creem 产品 ID |

### 常见问题排查

| 错误 | 原因 | 修复 |
|------|------|------|
| `No Next.js version detected` | Vercel 找不到 `landing/package.json` | Dashboard → Root Directory 设成 `landing` |
| `connect-src` 限制 API 地址 | CSP 没加 API 域名 | `next.config.mjs` 的 `connect-src` 加上 `https://api.quoteflow.it.com` |
| 防火墙导致连不上 | 服务器端口没开放 | 阿里云/云服务商防火墙开放 8000 端口 |

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
| 工作簿已关闭崩溃 | `wb.close()` 后设 `wb = None`，fallback 路径重加载 |

### PDF 解析器 (`pdf_parser.py`)

| 问题 | 修复 |
|------|------|
| 表头值泄漏到数据行 | 首行不改值，只记录 |
| 图片位置硬塞 | 型号→文件名匹配不到就留空 |
| PDF 图片不显示 | `_associate_images_to_products()` 从型号匹配改为页面分组顺序匹配 |
| quotation.pdf（多产品对比表）解析为空 | 添加 `is_multi_kv` 检测，多列 KV 表正确提取 |
| quotation2.pdf（嵌套表头单产品表）解析为空 | `detect_table_layout` 扫描所有列；`_extract_col_based` 第一列为空时用左邻列作参数名 |
| songlink pi.pdf 缺失产品 | `_is_real_model()` 中 `\d+\.\d+` 加 `^` 锚定，防止产品描述中的小数误杀 |
| 内容策略的假产品得分过高 | `_score_pdf_result` 添加 `_is_valid_pdf_model()` 过滤；`_has_real_products` 阈值 ≥2 → ≥1；单产品加成 |

### 图片匹配 (`image.py`)

| 问题 | 修复 |
|------|------|
| Excel 图片扩散到相邻产品 | 移除扩散逻辑 |
| 兜底时循环分配 | 只在序号范围内分配，不循环 |
| 两个解析器各做一遍图片提取 | 统一在 `main.py` 选赢家后只做一次 |
| DOCX 多表图片互相覆盖 | 递增序号替代原始行号 |
| DOCX 只检测第一列图片 | 改为扫描所有单元格 |
| 图片缓存被绕过 | `_image_cache` 支持带 `image_col` 参数缓存 |

### 评分系统 (`score.py` / `_score_pdf_result`)

| 问题 | 修复 |
|------|------|
| "CONTRACT NO."、"付款方式" 被当作真产品 | 添加字段名黑名单 + 价格合理性检查 `_is_reasonable_price()` |
| 合同条款行被当作产品 | `universal_parser.py` 添加 `_filter_non_product_rows()` |
| `universal_parser.py` 无法提前退出 | 添加评分阈值提前终止策略循环 |

### 报价单生成 (`quotation_excel.py`)

| 问题 | 修复 |
|------|------|
| USD 价格重复换算 | 检查产品原始 currency，仅非 USD 才换算 |
| 价格单元格格式为「自定义」非数值 | 显式设 `number_format = '#,##0.00'` |
| qty 单元格格式非数值 | 显式设 `number_format = '#,##0'` |
| 多价格不显示 | `price_raw` 追加到 spec 列 |
