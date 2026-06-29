# 报价整合工具 — 架构与模块调用文档

> 最后更新: 2026-05-12

> 本次更新: PostgreSQL 迁移 / Creem 支付 / 双 Token 认证 / 配额展示

---

## 1. 项目结构总览

```
production tool/
│
├── landing/                    ← Vercel 部署（前端）
│   ├── app/payment/            ← 支付成功/取消页
│   │   ├── success/page.js
│   │   └── cancel/page.js
│   ├── app/
│   │   ├── layout.js           ← 全局布局（导航 + 字体 + SEO metadata: OG/Twitter/robots）
│   │   ├── globals.css         ← 设计系统变量（深海蓝 #1E3A5F / 琥珀金 #D4A843）
│   │   ├── page.js             ← 首页即工具（核心页面）
│   │   ├── pricing/
│   │   │   └── page.js         ← 定价页（功能对比表 + 价格卡）
│   │   ├── how-it-works/
│   │   │   └── page.js         ← 工作原理展示页
│   │   ├── sitemap.js          ← /sitemap.xml 自动生成（SEO）
│   │   ├── robots.js           ← /robots.txt 爬虫规则（SEO）
│   │   └── login/
│   │       └── page.js         ← 登录占位页
│   ├── next.config.mjs         ← CSP/安全头配置（API直连后端，非代理）
│   └── package.json
│
├── backend/                    ← Railway 部署（后端）
│   ├── main.py                 ← FastAPI 入口（8个接口）
│   ├── universal_parser.py     ← 通用解析器（四层策略：KV→表格→内容驱动→无表头，评分择优）
│   ├── database.py            ← SQLAlchemy ORM (PostgreSQL)
│   ├── alembic/               ← 数据库迁移
│   ├── payment.py              ← Creem 支付集成
│   ├── ai_parser.py            ← AI 兜底解析（Gemini/Ollama）
│   ├── column_cache.json       ← 列映射缓存
│
├── product_tool/               ← 原有 Python CLI 工具（不动）
│   ├── src/
│   │   ├── parsers/
│   │   │   ├── excel_parser_v3.py         # 6种Excel布局自动检测
│   │   │   ├── param_price_parser.py      # Model:/型号: 格式
│   │   │   ├── invoice_parser.py          # PI格式
│   │   │   ├── price_table_parser.py      # 车型价格表
│   │   │   ├── single_spec_parser.py      # 单品规格页
│   │   │   └── spec_formatter.py          # 规格后处理
│   │   ├── core/
│   │   │   ├── pdf_parser.py              # PDF解析（三层策略：布局检测→内容推断→评分择优，+Docling后备）
│   │   │   └── doc_parser.py              # Word文档解析（三层策略：表头匹配→内容推断→段落提取→评分择优）
│   │   ├── output/
│   │   │   ├── quotation_excel.py         # 核心：报价单生成（Excel含图片）
│   │   │   ├── pi_generator.py            # 形式发票 PDF
│   │   │   └── pdf_generator.py           # PDF报价单
│   │   ├── packing/
│   │   │   └── generator.py               # 装箱单 + 商业发票
│   │   ├── utils/
│   │   │   ├── translator.py              # 160+贸易词库中英翻译
│   │   │   ├── price_config.py             # 价格配置加载/行业检测/正则匹配/优先级解析
│   ├── rates.py                   # 实时汇率 + 缓存
│   │   │   └── company.py                 # 公司信息读写
│   │   ├── terms.py                       # FOB/CIF/DDP/DAP/EXW计算
│   │   ├── dedup_engine.py                # 7步模糊去重
│   │   ├── categorizer.py                 # 自动分类
│   │   ├── image.py                       # 图片提取引擎（三路+列过滤+合并传播）
│   │   └── product_manage/
│   │       ├── db.py                      # SQLite建表
│   │       ├── repository.py              # CRUD操作
│   │       ├── importer.py                # 解析结果入库
│   │       └── exporter.py                # 数据库导出Excel
│   ├── run.py                             # CLI入口
│   └── product_cli.py                     # 交互式选品CLI
```

---

## 2. 页面结构

### 2.1 首页（`/`）

```
┌──────────────────────────────────────────────────────────────┐
│  NAV  报价整合工具                            定价 | 登录    │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  HERO                                                        │
│  上传文件，30秒生成报价单                                      │
│  Excel / PDF / Word 拖进来                                    │
│                                                               │
│  ┌────────────────────────────────────────────┐               │
│  │   拖拽文件到此处，或点击选择                  │               │
│  │   ↑ 上传 → POST /api/parse                  │               │
│  │   ↓ 返回 { products: [...] }               │               │
│  └────────────────────────────────────────────┘               │
│                                                               │
│  解析完成：sample.xlsx        共识别 12 个产品                  │
│  (原始 15 个，去重合并 3 个)                                   │
│                                                               │
│  [生成报价单]  [重新上传]                                      │
│       ↓                                                       │
│   弹出公司信息配置面板 ← 可选                                  │
│   ┌─────────────────────────────────────┐                     │
│   │ ○ 上传模板自动提取   → POST          │                     │
│   │ ○ 手动填写                          │                     │
│   │ 公司名: [_______________]           │                     │
│   │ 联系人: [_______________]           │                     │
│   │ 不填 → 标准格式                     │                     │
│   └─────────────────────────────────────┘                     │
│       ↓                                                       │
│   POST /api/quotation → 下载 .xlsx                            │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  场景一：自动解析      场景二：智能报价      场景三：全部出单    │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │ 产品表格       │    │ 产品卡片       │    │ 单据列表       │    │
│  │ 型号/名称/价格 │    │ 名称/单价/图片  │    │ Excel/PDF/PI  │    │
│  │ 自动去重       │    │ 贸易术语/FOB   │    │ 装箱单/发票    │    │
│  │ 自动分类       │    │ 中英翻译       │    │ ✓ 可生成      │    │
│  │ (后端处理完    │    │ 实时汇率       │    │              │    │
│  │  前端渲染)     │    │ 公司配置       │    │              │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│                                                               │
├──────────────────────────────────────────────────────────────┤
│  BOTTOM CTA  [查看定价]                                       │
├──────────────────────────────────────────────────────────────┤
│  FOOTER                                                       │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 定价页（`/pricing`）

```
┌──────────────────────────────────────────────────────────────┐
│  NAV  报价整合工具                             登录           │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  定价与功能对比                                                │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ 免费体验       │  │ 注册免费       │  │ 专业版        │        │
│  │ ¥0            │  │ ¥0            │  │ ¥39/月       │        │
│  │ 无需注册       │  │ 产品库持久化    │  │ 早鸟价·名额有限│        │
│  │ [开始体验]     │  │ [免费注册]     │  │ [立即订阅]    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                               │
│  功能对比表                                                    │
│  ┌─────────────────────────────┬──────┬──────┬──────┐        │
│  │ 功能                        │ 免费  │ 注册  │ 专业  │        │
│  ├─────────────────────────────┼──────┼──────┼──────┤        │
│  │ 上传解析 Excel/PDF/Word     │  ✓   │  ✓   │  ✓   │        │
│  │ 生成 Excel 报价单(含图片)    │ 含标记 │  ✓   │  ✓   │        │
│  │ 产品库持久化管理             │  —   │  ✓   │  ✓   │        │
│  │ 报价历史管理                 │  —   │  ✓   │  ✓   │        │
│  │ 图片自动匹配嵌入             │  ✓   │  ✓   │  ✓   │        │
│  │ FOB/CIF/DDP 贸易术语        │  —   │  —   │  ✓   │        │
│  │ 中英双语翻译                 │  —   │  —   │  ✓   │        │
│  │ PDF 报价单                  │  —   │  —   │  ✓   │        │
│  │ 形式发票 PI                 │  —   │  —   │  ✓   │        │
│  │ 装箱单+商业发票             │  —   │  —   │  ✓   │        │
│  │ 不限产品数量                 │  —   │  —   │  ✓   │        │
│  │ 公司信息配置                 │  —   │  —   │  ✓   │        │
│  │ 实时汇率换算                 │  —   │  —   │  ✓   │        │
│  │ 报价模板自适应               │  —   │  —   │  ✓   │        │
│  └─────────────────────────────┴──────┴──────┴──────┘        │
│                                                               │
│  如何订阅                                                     │
│  联系客服开通，当天手动开通                                    │
│  微信：yb857151464                                            │
│  [联系客服]                                                    │
├──────────────────────────────────────────────────────────────┤
│  FOOTER                                                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. API 调用流程图

```
用户操作                前端                         后端                         现有 Python 代码
────────               ──────                      ──────                       ────────────────

① 拖文件上传           fetch POST /api/parse
                          │
                          ▼
                       next.config.mjs 代理
                       /api/* → localhost:8000/api/*
                          │
                          ▼
                       main.py:parse_file()
                          │
                          ├── .xlsx → run.py:parse_file()
                          │              ├── detect_parser_type()  # 自动检测文件类型
                          │              │    ├── param_price_parser.py   # Model:/型号: 格式
                          │              │    ├── invoice_parser.py       # PI 发票格式
                          │              │    ├── price_table_parser.py   # 车型价格表
                          │              │    ├── single_spec_parser.py   # 单品规格页
                          │              │    ├── universal_parser.py    # 通用4层策略解析器
              │              │    │   (KV → 关键词 → 内容推断 → 无表头)
              │              │    ├── shared_keywords.py    # 跨解析器共享关键词
              │              │    ├── dedup_engine.py       # 7步模糊去重
              │              │    └── categorizer.py        # 自动分类
               │              │
               │              ├── .pdf  → pdf_handler.py → pdf_parser.py
               │              │          (4层策略: KV → 布局检测 → 内容 → Docling)
               │              │
               │              ├── .docx → doc_parser.py
               │              │          (3层策略: 表头关键词 → 内容推断 → 段落文本)
               │              │
               │              └── 择优: score_dataframe() 信号组合评分
               │                    │  逐产品评分(7级) + 全局一致性加成 → 分高者胜
              │                    ▼
              │                  返回 [{model, name_zh, price_rmb, _row, _sheet, ...}]
              │                    │
              │                    ▼
              │                图片匹配: 按 _row+_sheet 键值匹配 (image.py)
              │                    │
              │                    ▼
              │                前端渲染 3 个场景：
              │                场景1：产品表格（型号/名称/价格）
              │                场景2：产品卡片（名称/单价/图片）
              │                场景3：单据列表（5种类型✓可生成）

② 配置公司信息（可选）   fetch POST /api/template/upload
  上传模板 / 手动填写        │
                             ▼
                          main.py:upload_template()
                             │
                             ├── 提取公司名称/地址
                             ├── 提取 Logo（image.py）
                             ├── 检测列名映射（detector.py）
                             └── 保存到用户 session
                             │
                             ▼
                          返回 { company_name, address, columns, ... }

③ 生成报价单           fetch POST /api/quotation
                          │
                          ▼
                       main.py:generate_quotation()
                          │
                          ├── quotation_excel.py:create_quotation()
                          │    ├── company.py         → 公司信息
                          │    ├── terms.py           → FOB/CIF/DDP 计算
                          │    ├── rates.py           → 实时汇率 USD/CNY
                          │    ├── translator.py      → 中英翻译
                          │    ├── image.py           → 三路图片匹配嵌入
                          │    └── dedup_engine.py    → 智能去重显示
                          │
                          └── 返回 .xlsx 文件下载
```

---

## 4. API → Python 模块映射表

| API 端点 | 方法 | 输入 | 输出 | 调用的 Python 模块 |
|----------|------|------|------|-------------------|
| `/api/parse` | POST | 文件(.xlsx/.pdf/.docx) | `{products: [...], count: N}` | `run.py` → 各类解析器 + `dedup_engine.py` + `categorizer.py` + `image.py` |
| `/api/quotation` | POST | products JSON, lang, trade_terms | .xlsx 文件下载 | `quotation_excel.py` → `company.py` + `terms.py` + `rates.py` + `translator.py` + `image.py` |
| `/api/pi` | POST | products JSON | .pdf 文件下载 | `pi_generator.py` → `config.py` |
| `/api/template/upload` | POST | 模板文件(.xlsx) | `{company_name, address, logo, columns}` | `image.py`（Logo提取）+ `detector.py`（列检测）+ `company.py` |
| `/api/template/save` | POST | template config JSON | `{status: ok}` | `company.py` |
| `/api/template` | GET | — | `{saved config}` | `company.py` |

---

## 5. 定价分层功能限制

通过 `user.tier` 字段控制（匿名 session / 注册免费 / 专业版），后端中间件检查：

| 功能 | 免费体验（匿名） | 注册免费 | 专业版 |
|------|:--------------:|:--------:|:-----:|
| 上传解析文件 | ✓ 不限 | ✓ 每月50次 | ✓ 不限 |
| 生成Excel报价单 | ✓ 含"由报价整合工具生成"标记 | ✓ 无标记 | ✓ 无标记 |
| 产品库持久化 | ✗ | ✓ | ✓ |
| 报价历史 | ✗ | ✓ | ✓ |
| 图片匹配 | ✓ | ✓ | ✓ |
| FOB/CIF/DDP | ✗ | ✗ | ✓ |
| 中英翻译 | ✗ | ✗ | ✓ |
| PDF报价单 | ✗ | ✗ | ✓ |
| 形式发票PI | ✗ | ✗ | ✓ |
| 装箱单+商业发票 | ✗ | ✗ | ✓ |
| 公司信息配置 | ✗ | ✓ | ✓ |
| 报价模板自适应 | ✗ | ✗ | ✓ |
| 实时汇率 | ✗ | ✗ | ✓ |
| 不限产品数 | ✗ | ✗ | ✓ |

---

## 6. 数据流全景

```
源文件 (xlsx / pdf / docx)
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│  backend/main.py                                             │
│                                                              │
│  POST /api/parse                                             │
│     │                                                        │
│     ├── 文件类型检测 → dispatch parser                       │
│     │     ↓                                                  │
│     │  1. param_price_parser.py    ("Model:"标记)             │
│     │  2. invoice_parser.py        ("Description of Goods")  │
│     │  3. price_table_parser.py    (车型价格表)               │
│     │  4. single_spec_parser.py    (单一产品规格)              │
│     │  5. excel_parser_v3.py       (6种布局自动检测)          │
│     │  6. pdf_parser.py            (PDF表格 pdfplumber)      │
│     │  7. doc_parser.py            (Word文档 python-docx)    │
│     │     ↓                                                  │
│     ├── spec_formatter.py          (规格文本格式化)           │
│     ├── image.py                   (三路图片匹配)             │
│     ├── dedup_engine.py            (7步模糊去重)              │
│     └── categorizer.py             (自动分类)                 │
│          ↓                                                   │
│     return { products: [...], count: N }                     │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│  landing/page.js                                             │
│                                                              │
│  场景1: 渲染产品表格（型号/名称/价格/去重统计）                │
│  场景2: 渲染产品卡片（名称/单价/图片/贸易术语/翻译）            │
│  场景3: 渲染单据列表（5种类型 ✓ 可生成）                      │
│                                                              │
│  用户点"生成报价单"                                           │
│     → 可选配置公司信息 (POST /api/template)                   │
│     → POST /api/quotation                                    │
│          ↓                                                   │
│        quotation_excel.py 生成 .xlsx                         │
│        + terms.py (FOB/CIF/DDP)                              │
│        + rates.py (汇率)                                     │
│        + translator.py (翻译)                                 │
│        + company.py (公司信息)                                │
│        + image.py (图片嵌入)                                  │
│          ↓                                                   │
│       浏览器下载报价单                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 状态与错误处理

### 页面状态

| 状态 | 用户看到 |
|------|---------|
| **Loading** | 上传区旋转动画 + "正在解析文件..." |
| **Empty** | 拖拽图标 + "拖拽文件到这里，或点击选择" |
| **Success** | ✓ 解析完成 + 产品数 + [生成报价单] 按钮 |
| **Error** | ⚠️ 红色错误消息 + 原因 + [重新上传] |
| **Parsing** | 计算去重前后的数量差，标注分类 |

### API 错误

| 后端错误 | 前端表现 |
|----------|---------|
| 400 文件格式不支持 | 弹出"仅支持 .xlsx/.xls/.pdf/.docx" |
| 400 未找到产品 | "解析完成，但未识别到产品数据" |
| 500 服务器错误 | "服务器繁忙，请稍后重试" + 重试按钮 |
| 网络断开 | fetch 超时 → "网络连接失败，请检查网络" |

---

## 8. 部署架构

```
Vercel（免费）                    Railway（~$5/月额度）
┌─────────────┐                  ┌──────────────────┐
│ landing/     │      /api/*      │ backend/          │
│ Next.js 16    │ ──────────────→ │ FastAPI + uvicorn │
│ 静态页面      │ ←────────────── │ 包装 product_tool │
│              │   JSON/文件下载  │ ├── uploads/      │
│ landing/     │                  │ ├── outputs/      │
│   .vercel    │                  │ ├── main.py       │
│  (自动检测)   │                  │ └── product_tool/ │
└─────────────┘                  │    → src/         │
                                  └──────────────────┘
                                           │ 自动休眠
                                           │ 3分钟无请求
                                           │ 休眠
                                           │ 有请求唤醒
                                           ▼
                                    冷启动 ~3-5秒
```

### 部署命令

**Vercel（前端）：**
```bash
cd landing
npx vercel --prod
```

**Railway（后端）：**
```bash
# GitHub 导入 backend/ 目录
# Railway 自动检测 railway.json
# 自动执行: pip install -r requirements.txt
# 自动启动: uvicorn main:app --host 0.0.0.0 --port $PORT
```
