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

## 解析器择优系统

`backend/main.py` 对同一个文件同时运行两个解析器：
1. **通用解析器**（`universal_parser.py`）：三层策略（KV→表格→内容驱动）
2. **专用解析器**（`run.parse_file`）：格式检测 + 6种专用解析器 + 多级 fallback

然后用 `backend/score.py` 的 **信号组合评分系统** 对两个结果评分，分高者胜。
评分维度：逐产品 7 级信号组合（真型号+价格+参数→+7） + 全局一致性加成。
不再使用旧的数量比较逻辑（谁产品多选谁）。

## 部署生产

### Railway（后端，backend/）

```bash
# 1. railway.app 创建项目 → GitHub repo → Service 选 backend/
# 2. 设置环境变量（必填）:
#    JWT_SECRET_KEY    — 生成: python -c "import secrets; print(secrets.token_hex(32))"
#    DATABASE_URL       — PostgreSQL 连接串
#    BASE_URL           — Vercel 前端域名，如 https://xxx.vercel.app
# 3. (可选) CREEM_API_KEY / CREEM_WEBHOOK_SECRET / CREEM_PRODUCT_ID_PRO
# 4. (可选) GEMINI_API_KEY / USE_DOCLING
# 5. Railway 自动检测 railway.json，部署即可
```

### Vercel（前端，landing/）

```bash
# 1. vercel.com 创建项目，Framework Preset → Next.js，Root Directory → landing/
# 2. 设置环境变量:
#    NEXT_PUBLIC_API_URL=https://你的railway域名.up.railway.app
# 3. Vercel 自动检测 vercel.json，部署即可
```

### 环境变量总表

| 平台 | 变量 | 必填 | 说明 |
|------|------|------|------|
| Railway | `JWT_SECRET_KEY` | ✅ | JWT 签名密钥 |
| Railway | `DATABASE_URL` | ✅ | PostgreSQL 连接串 |
| Railway | `BASE_URL` | ✅ | Vercel 前端域名（CORS 白名单） |
| Railway | `CREEM_API_KEY` | 可选 | Creem 支付 |
| Railway | `CREEM_WEBHOOK_SECRET` | 可选 | Creem Webhook 签名 |
| Railway | `CREEM_PRODUCT_ID_PRO` | 可选 | Creem 产品 ID |
| Railway | `GEMINI_API_KEY` | 可选 | AI 列检测 |
| Railway | `USE_DOCLING` | 可选 | Docling 后备解析 |
| Vercel | `NEXT_PUBLIC_API_URL` | ✅ | Railway 后端域名 |
