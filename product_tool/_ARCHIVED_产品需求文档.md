# 产品工具 — 需求文档

> ⚠️ **文档同步规则**：本中文文件与英文版 `REQUIREMENTS.md` **必须同步更新**。任何修改必须同时更新两个文件。
> 
> 📖 **完整系统实现文档请参见**：[系统架构与功能实现文档](../docs/系统架构与功能实现文档.md)
> 
> 本文档聚焦产品定位和功能需求。实现细节（API端点、数据流、模块交互、前端组件）全部在架构文档中。

---

## 产品定位

| 项目 | 说明 |
|------|------|
| **谁用？** | 外贸 SOHO / 3-5 人小团队，需要从乱糟糟的源文件快速生成报价单 |
| **有啥不一样？** | 不是模板工具，是**数据整合引擎**。一次解析，永久复用。上传加密处理，解析完成即删除，不长期留存 |
| **能出啥？** | Excel 报价单（含图片）、PDF 报价单、形式发票 PI、装箱单、商业发票（共 5 种） |
| **多快？** | 上传到出单 3-60 秒（取决于文件大小） |
| **架构** | Next.js 前端（Vercel）+ FastAPI 后端（阿里云 VPS 新加坡） |
| **当前状态** | ✅ 通用解析器上线（三层策略：KV→表格→内容驱动，评分择优）。✅ PDF三层策略解析。✅ DOCX三层策略解析。✅ 图片匹配。✅ 货币识别。✅ 产品库/报价历史。✅ PostgreSQL 迁移。✅ Creem 支付。✅ 双Token认证。✅ API 限流。✅ Sentry 监控。✅ 邮件系统(Resend/SMTP)。✅ 忘记密码。✅ CI/CD。✅ 37 项测试 |
| **要钱吗？** | 免费体验 + Pro $9.99/月 (USD) / ¥39/月 (CNY) |

---

## 这工具干啥的

从 Excel / PDF / Word 文件里提取产品数据，管理产品库，生成带图片的英文/中文报价单和外贸单据。

### 数据流水线

```
用户浏览器 (localhost:3000)
   │
   ▼
┌─────────────────────────────────────────────────┐
│  landing/ (Next.js, Vercel)                       │
│  ├── 首页: 上传文件 → 出报价单                     │
│  ├── /pricing: 定价与功能对比                      │
│  ├── /how-it-works: 三步骤工作原理                 │
│  └── /login: 工作台入口                           │
└─────────────────────────────────────────────────┘
   │  API 代理 (/api/*)
   ▼
┌─────────────────────────────────────────────────┐
│  backend/ (FastAPI, Railway)                     │
│                                                  │
│  POST /api/parse — 文件解析（三层策略择优）          │
│     ├── 通用解析器 (universal_parser.py)            │
│     │    ├── 策略1: KV布局检测 → 单/多产品解析       │
│     │    ├── 策略2: 表格布局 → 列映射 + 提取         │
│     │    ├── 策略3: 内容驱动 → 推断列角色后提取       │
│     │    ├── score_result() 评分择优                │
│     │    └── 货币自动识别（FOB表头→USD，价格列→RMB） │
│     │                                              │
│     ├── PDF解析 (pdf_parser.py) 三层策略            │
│     │    ├── 策略1: 布局检测 → col/row_based       │
│     │    ├── 策略2: 内容推断 → _classify + 提取      │
│     │    └── _score_pdf_result() 评分择优            │
│     │                                              │
│     ├── DOCX解析 (doc_parser.py) 三层策略           │
│     │    ├── 策略1: 表头关键词匹配 → 列映射→提取    │
│     │    ├── 策略2: 内容推断列角色 → 提取            │
│     │    ├── 策略3: 段落文本 → 键值对提取           │
│     │    └── _score_docx_result() 评分择优          │
│     └── 专用解析器 (param_price/invoice/table)      │
│                                                  │
│  POST /api/quotation — 生成报价单                  │
│     ├── quotation_excel.py → Excel含图片           │
│     ├── terms.py → FOB/CIF/DDP 计算               │
│     ├── rates.py → 实时汇率                       │
│     ├── translator.py → 中英翻译                  │
│     └── company.py → 公司信息                     │
│                                                  │
│  POST /api/pi — 形式发票 PDF                      │
│  POST /api/packing — 装箱单 + 商业发票            │
│  POST /api/template — 模板提取公司信息            │
│  GET /api/images/ — 产品图片服务                  │
│  POST /api/parse/with-ai — AI 兜底解析            │
└─────────────────────────────────────────────────┘
```

---

## 核心模块（数据流水线核心）

这些模块是**必须的**：没有它们，工具跑不起来或输出是错的。

### 1. 命令行入口

| 模块 | `product_cli.py`（推荐） | `run.py`（旧版） |
|------|------------------------|-----------------|
| **技术** | argparse, sqlite3, openpyxl | argparse, openpyxl, pandas |
| **状态** | 100% — 生产可用 | 95% — 测试还在用 |
| **功能** | 从产品库选品 → 生成报价单 | 直接解析文件 → 可选入库 → 输出 |
| **怎么用** | 3 种选品模式：(1) `--select` 交互式浏览分类选 (2) `--sku XP,BOX` 直接指定 (3) `--order-file order.xlsx` 用 Excel 批量选。然后调 `create_quotation_from_library()` 出报价 | 接收 `--input` 文件/文件夹 → 自动检测解析器类型 → 解析 → 去重/分类/入库 → 输出报价或标准 Excel |
| **接谁** | 入口，调 quotation_excel + product_manage | 入口，调 parsers + product_manage + quotation_excel |
| **参数** | `--select`, `--sku`, `--quantity`, `--quote`, `--currency`, `--trade-terms`, `--lang`, `--with-images`, `--user-id` | `--input`, `--output`, `--lang`, `--quotation`, `--save-to-db`, `--merge`, `--category`, `--supplier` |

### 2. 解析层

| 模块 | 技术 | 状态 | 功能 | 怎么运作 | 怎么被接 |
|------|------|------|------|---------|---------|
| `excel_parser_v3.py` | openpyxl, pandas, zipfile | 95% | **主 Excel 解析器** — 自动检测 6 种布局 | `classify_format()` 扫描表格，按优先级判断：参数列表 > 发票 > 价格表 > 横向 > 单品 > 纵向。派发给专用解析器或用内置兜底。通过 zipfile 提取嵌入图片 | `run.py:parse_file()` 自动调用 |
| `param_price_parser.py` | openpyxl, pandas | 95% | 解析 `Model:`/`型号:`/`Item:` 标记格式 | 扫描前几行找标记，然后按列读取键值对。支持价格标记（Price:, 价格:）。提取嵌入图片 | 由 `detect_parser_type()` 检测后派发 |
| `invoice_parser.py` | openpyxl, pandas | 90% | 解析形式发票 PI 格式 | 找 "Description of Goods" 表头，提取型号/规格/数量/单价列。跳过关键字过滤底部噪音 | 同上派发链 |
| `price_table_parser.py` | openpyxl, pandas | 95% | 解析车型价格表 | 固定列映射：第2列=型号，第4列=价格，第6-12列=电机规格 | 同上派发链 |
| `single_spec_parser.py` | openpyxl, pandas | 85% | 解析单一产品规格页 | 处理一个产品+多行参数的文件。支持复合价格拆分（"电动车: ¥4980 / 电池: ¥2530"） | 同上派发链 |
| `spec_formatter.py` | re 正则 | 98% | 规格文本后处理 | 去重、标准化单位、格式化键值对。**新增空格分隔符处理**（`"Motor: 4000W Battery: 72V"` 自动分割为多行）。所有解析结果都经过它处理 | 被 `excel_parser_v3.py` 解析后调用 |
| `pdf_parser.py` | pdfplumber, fitz, pandas | **95%** | 从 PDF 提取产品（三层策略择优） | `extract_products_from_pdf_v2()`：pdfplumber 提取表格 → **三层策略**（布局检测col/row_based → 内容推断列角色`_classify_pdf_columns()` → `_score_pdf_result()` 评分择优）→ `_associate_images_to_products()` 关联图片 | `run.py:parse_file()` 检测到 `.pdf` 后缀时调用 |

### 3. 数据处理层

| 模块 | 技术 | 状态 | 功能 | 怎么运作 | 怎么被接 |
|------|------|------|------|---------|---------|
| `price.py` | re 正则 | **100%** ✅ | 价格清洗与转换 | `clean_price_value()`：提取数字 → 检测货币（$¥€£）→ 处理 K/W 单位（5K=5000）→ 统一转人民币。**Bug 已修：K 展开不再被 'USD' 阻断** | 被所有解析器 + 入库模块调用 |
| `image.py` | openpyxl, zipfile, xml.etree | **100%** ✅ | **图片提取引擎（三路+列过滤+合并传播）** | 三路：① openpyxl `_images` + anchor row（标准嵌入）；② DISPIMG 公式解析 + worksheet XML（WPS 文件）；③ drawing XML 解析（标准 xlsx 图片）。**`_detect_image_column()` 自动检测"产品图片"列 → `image_col` 参数过滤包装图/适合图（col 8）**。统一 `match_images_to_products()` 入口，含 `match_sku_folder()` 文件夹回退、`extract_images_from_docx()` DOCX 提取。**合并单元格图片传播**：同一合并组的行共享第一行图片。 | 所有解析器自动调用 |
| `detector.py` | pandas, re | 95% | 列类型自动检测 | `smart_detect_columns()`：根据内容模式分析给每列打分（价格/型号/规格/名称） | 被解析器调用 |
| `dedup_engine.py` | pandas, numpy | 100% | 7 步模糊去重 | 7 步：标准化型号 → 去后缀 → 模糊分组 → 打分 → 阈值过滤 → 合并 → 报告。**Bug 已修：total_input 统计现在用输入数而不是过滤后的输出数** | `run.py` 入库前调用 |
| `categorizer.py` | pandas, JSON | 100% | 自动分类 | 根据 json 配置文件里的分类规则，匹配产品关键词自动归类 | `run.py` 调用 |

### 4. 存储层

| 模块 | 技术 | 状态 | 功能 | 怎么运作 | 怎么被接 |
|------|------|------|------|---------|---------|
| `db.py` | sqlite3 | 100% | 数据库初始化与建表 | 建 `products` 表：id, user_id, sku(唯一), name_zh, name_en, category, price_rmb, price_usd, moq, specs(JSON), spec_zh, spec_en, image_path, source_file, 时间戳。索引：sku, category, name_zh, user_id | 被所有 product_manage 模块调用 |
| `models.py` | dataclasses | 100% | 产品数据模型 | `Product` 数据类，`to_row()`/`from_row()` 做数据库序列化。`specs` 存字典，序列化成 JSON | 被 repository + importer 使用 |
| `repository.py` | sqlite3 | 100% | 数据库增删改查 | 提供：单查/批量查（**N+1 已修**）、列表、搜索、分类列表、删除。所有查询用参数化防止注入 | 被 importer, exporter, product_cli 调用 |
| `importer.py` | pandas, sqlite3 | 100% | 解析结果入库 | 遍历行 → 批量查重 → 冲突自动加后缀（-A, -B）→ 自动翻译中文名→英文名（如果空的）→ 写入时间戳 | `run.py` 加 `--save-to-db` 时调用 |
| `exporter.py` | pandas, openpyxl | 100% | 从数据库导出 Excel | 读取某用户所有产品，写出带样式的 Excel | 测试脚本在用 |

### 5. 业务逻辑层

| 模块 | 技术 | 状态 | 功能 | 怎么运作 | 怎么被接 |
|------|------|------|------|---------|---------|
| `terms.py` | dataclasses | 100% | 贸易术语计算 | `calculate_price()`：按 Incoterms 2020 算 EXW/FOB/CIF/DAP/DDP。输入：底价、数量、目的地、体积。输出：详细拆解（运费、保险、关税） | 被 `quotation_excel.py` 调用 |
| `rates.py` | requests, JSON | 100% | 实时汇率 | `get_rate(来源币种, 目标币种)`：从 rates.convert API 获取，缓存到 JSON，网络失败时用硬编码兜底 | 被 `terms.py`, `price.py`, `importer.py` 调用 |
| `translator.py` | 字典替换 | 100% | 中英翻译 | `translate_text(文本, 模式)`：160+ 贸易专业词库，按词长从长到短替换避免"锂电池"→"Lithium Batteryattery"。`translate_dataframe()` 翻译所有文本列。解析入库和报价输出都会用到 | 被 `run.py`, `product_cli.py`, `quotation_excel.py` 通过 `--lang` 参数使用 |
| `company.py` | json, pathlib | 100% | 公司信息管理 | `load_company()` / `save_company()`：从 `company.json` 读写公司信息（名称、联系人、地址等） | 被 `quotation_excel.py` 调用 |

### 6. 输出层

| 模块 | 技术 | 状态 | 功能 | 怎么运作 | 怎么被接 |
|------|------|------|------|---------|---------|
| `quotation_excel.py` | openpyxl, pandas | **100%** ✅ | **报价单生成器** — 核心输出 | `write()`：生成带样式的 Excel，含公司信息区块（名称/地址/电话/邮箱）、7 列表头（No./Photo/Model+Name/Specs/Qty/Unit Price/**Total**）、型号/名称智能去重、规格自动换行、图片嵌入、底部 Total 汇总行、贸易术语、付款条件。`create_quotation_from_library()`：从数据库读产品 → 规格回退（specs 字典 vs spec_zh 文本取更完整者）→ name_zh/nane_en "nan" 自动过滤 → 解析图片路径 → 计算价格。支持 `--lang english/bilingual`。 | 被 `product_cli.py` + `run.py` 调用 |

---

## 非核心模块（辅助/待接线）

这些模块不是必需的。有些写好了但没接上，有些是独立工具。

| 模块 | 技术 | 状态 | 功能 | 为啥非核心 | 要接上需要做什么 |
|------|------|------|------|-----------|----------------|
| `doc_parser.py` | python-docx, zipfile, re | **95%** | Word 文档解析（三层策略：表头匹配→内容推断→段落提取） | `parse_product_docx()` 三层策略：① 表头关键词匹配（扩充型号/价格/规格同义词）→ 列映射 → 提取；② `_infer_docx_columns()` 内容推断列角色 → 提取；③ `_extract_products_from_text()` 段落文本键值对提取（优先匹配¥价格，后备$）。`_score_docx_result()` 评分择优。内置 `extract_images_from_docx()` 图片提取。 | `run.py:parse_file()` 检测到 `.docx` 时调用 |
| `pi_generator.py` | weasyprint, jinja2 | 90% | 生成形式发票 PDF | 报价被接受后才用的下游单据 | ✅ 已接线 `--pi`。需 `pip install weasyprint` |
| `pdf_generator.py` | weasyprint | 85% | 生成 PDF 报价单 | 旧版 reportlab 有中文字体问题，改用 weasyprint | ✅ 已接线 `--pdf`。用 weasyprint HTML→PDF，系统字体支持中文 |
| `packing/generator.py` | openpyxl | 100% | 装箱单 + 商业发票 | 报价被接受后才用的下游单据 | ✅ 已接线 `--packing`。**Bug 已修：裸 except → except Exception** |
| `excel_writer.py` | openpyxl | 95% | 样式化 Excel 输出 | 和 quotation_excel 功能重叠 | 已部分替代 run.py 中的 df.to_excel() |
| `excel_enhanced.py` | openpyxl | 90% | 冻结/筛选/模板 | 锦上添花 | 集成到 quotation_excel |
| `pricing.py` | dataclasses | 100% | 分级定价（量大优惠） | 业务规则，不是基础报价必需的 | 接入 `create_quotation_from_library()` |
| `tracker.py` | json | 100% | 报价版本追踪 | 客户管理功能，不是核心 | 加 `--track` 参数。**Bug 已修：两个时间字段现在都用浮点数时间戳** |
| `folder_watcher.py` | watchdog | 100% | 监控文件夹自动解析 | 独立工具 | 直接运行，不用接线 |
| `image_matcher.py` | PIL, re | 100% | 图片文件名匹配产品 | 独立工具 | 直接运行，不用接线 |
| `filter.py` | pandas | 100% | 按条件筛选产品 | 锦上添花 | 集成到 product_cli 搜索 |
| `config.py` | Python stdlib | 100% | 全局常量 | 基础设施 | 被各模块间接使用 |

---

## Bug 修复状态（全部已修）

| 严重度 | 在哪 | 问题 | 怎么修的 |
|--------|------|------|---------|
| 🔴 **高** | `price.py` 148-151 行 | K 展开被 'USD' 守卫阻断 → "5K USD" 变成 ¥36 而不是 ¥36000 | 删掉 K 和 W 展开条件里的 'USD' 排除 |
| 🔴 **高** | `pdf_parser.py` 275 行 | `detect_table_layout` 一行列表推导式在 pdfplumber 不规则行上可能崩溃 | 改成稳健的迭代：检查类型、长度、None/空值 |
| 🟡 **中** | `excel_parser_v3.py` 空行断行 | `parse_price_list` 从不触发空行中断 → 把尾巴上的总价/银行信息当成产品 | 加了连续空行计数器，连续 2 个空行且已找到 2+ 产品时跳出 |
| 🟡 **中** | `excel_parser_v3.py` 82-131 行 | return 后 50 行死代码 | 删掉死代码块；恢复被误删的辅助函数（is_numeric / is_model_code / is_spec_keyword 等） |
| 🟡 **中** | `packing/generator.py` 59/222 行 | 裸 `except:` 会抓住 Ctrl+C | 两处都改成 `except Exception:` |
| 🟡 **中** | `tracker.py` 62-63 行 | created_at 是字符串，expires_at 是浮点数 — 没法直接比较 | created_at 改成 `.timestamp()` 浮点数 |
| 🟡 **中** | `dedup_engine.py` 321 行 | total_input 统计用了过滤后的输出数 | 把统计挪到 `run()` 开头，在过滤之前捕获输入数 |
| 🟡 **中** | repository / quotation | 每个产品单独查一次数据库的 N+1 问题 | 加了批量查询 `get_products_by_ids()` 和 `get_products_by_skus()`，支持 `order_by_source` 参数 |
| 🟡 **中** | `importer.py` 52-62 行 | 每行单独查 SKU 的 N+1 问题 | 同上批量查询 |
| 🟢 **低** | `db.py` 76-84 行 | 缺 user_id 索引 | 加了索引 |
| 🟢 **低** | `translator.py` 48 行 | 重复 key 把 'Remarks' 覆盖成了 'Note' | 去掉重复，保留正确的 |
| 🟢 **低** | `excel_parser_v3.py` | 辅助函数被死代码删除误删 | 全部恢复 |

### 2026-05-05 修复

| 严重度 | 在哪 | 问题 | 怎么修的 |
|--------|------|------|---------|
| 🔴 **高** | `image.py` 71/265 行 | `row <= 2` 过滤器误杀了第 2 行的产品图片（XP） | 改为 `row <= 1`，只跳过真正的表头行 |
| 🟡 **中** | `quotation_excel.py` 740-748 行 | `create_quotation_from_library()` 只用 `product.specs` 字典，`specs=None` 时即使 `spec_zh` 有完整文本也返回空 | 改为长度比较：`spec_zh` 和 `specs` 输出谁长用谁 |
| 🟡 **中** | `quotation_excel.py` 772 行 | `name_zh` 为 null 时 Python 转字符串变成 "nan" | 过滤 "nan"/"none"/"" 时回退到 `sku` |
| 🟡 **中** | `quotation_excel.py` 774 行 | `name_en` 为 "nan" 时 `bilingual_text` 产生 "XP / nan" | `name_en` 同规则过滤，`bilingual_text` 在 `name_en` 为空时跳过 |
| 🟡 **中** | `spec_cleaner.py` 截断检测 | `1360*` 只追加通用 `(may be incomplete)` | 支持按模式追加特定标记（`(尺寸单位缺失)`），新增长文本末尾短词检测 |

---

## 图片性能优化

**之前：** 80 个产品的报价单要 **6 分钟**。原因：每次生成报价都递归全局搜图（`**/*.jpg`）。

**之后：** `image_path` 存在数据库里，报价生成器直接读。三路匹配引擎（openpyxl _images / DISPIMG 公式 / drawing XML）+ DOCX + 文件夹 SKU 回退，覆盖所有源文件类型。

**结果：** 80 产品报价约 **~10 秒**，无全局搜图。图片覆盖率 **99%**（79/80）。

---

## 翻译系统

| 功能 | 状态 | 用法 |
|------|------|------|
| 词典 | ✅ 160+ 贸易专业词（电池、车辆、尺寸、颜色、材料、认证等） | `translator.py` |
| 长词优先 | ✅ 按词长从长到短替换，避免"锂电池"变成"Lithium Batteryattery" | `translate_text()` |
| 输出模式 | `chinese`（默认）、`english`、`bilingual` | `--lang` 参数 |
| CLI 接线 | ✅ `run.py` + `product_cli.py` 都支持 `--lang` | 全线接好 |
| 列标题 | ✅ `--lang english` 时表头自动翻译成英文 | `quotation_excel.py` |
| 产品名 | ✅ 入库时如果英文名为空自动翻译 | `importer.py` |
| 规格内容 | ✅ 通过词典替换翻译 | `translator.translate_dataframe()` |

---

## 产品整合结果

| 指标 | 数值 |
|------|------|
| **源文件** | `param_price.xlsx`、`车型价格表...xlsx`、`quotation.pdf`、`e-motorcycle.pdf`、`SONLINK PI.xlsx`、`BAOSHIMA_...xlsx` |
| **原始产品** | 118 |
| **最终产品** | 80（已过滤） |
| **图片覆盖率** | **79/80 = 99%** |
| **用户优先级** | `ev_alls` > 其他用户（去重获胜） |
| **数据来源** | ev_alls: 80 产品，local: 54 产品，共约 109 产品（去重后 80） |

---

## 产品来源分布

| 源文件 | 产品数 |
|--------|--------|
| param_price.xlsx | 56 |
| 车型价格表...xlsx | 12 |
| SONLINK PI.xlsx | 7 |
| quotation.pdf | 3 |
| e-motorcycle.pdf | 1 |
| BAOSHIMA_...xlsx | 1 |
| **合计** | **80** |

---

## 新增功能 (2026-05-04)

### 1. 按源文件排序产品

| 功能 | 说明 |
|------|------|
| **函数** | `get_products_by_ids(product_ids, user_id, order_by_source=True)` |
| **位置** | `src/product_manage/repository.py` |
| **行为** | 按 `source_file` + `created_at` 排序，同源文件的产品排在一起 |
| **调用** | `product_cli.py` 中 9 处调用都加了 `order_by_source=True` |
| **效果** | 输出Excel中同源文件的产品连续显示 |

### 2. 空格分隔符规格自动换行

| 功能 | 说明 |
|------|------|
| **位置** | `src/parsers/spec_formatter.py` |
| **输入** | `"Motor: 4000W Battery: 72V 20AH"`（用空格分隔参数） |
| **输出** | `Motor: 4000W\nBattery: 72V 20AH`（自动换行分隔） |
| **逻辑** | 检测空格前的 `参数名:` 模式，在此处分割 |
| **修改函数** | `format_spec_spec()`、`split_spec_to_dict()` |

---

## 新增功能 (2026-05-05)

### 1. 三路图片匹配引擎

`image.py` 完全重写，支持三种 xlsx 图片系统：

| 匹配方式 | 覆盖文件 | 原理 |
|---------|---------|------|
| **openpyxl `_images`** | 标准 xlsx（param_price.xlsx 等） | 取 anchor row（1-indexed），匹配产品 `_row` |
| **DISPIMG 公式** | WPS 文件（SONLINK PI.xlsx 等） | 解析 `cellimages.xml` + worksheet 中 `_xlfn.DISPIMG` 公式 → (row, file) |
| **drawing XML** | 标准 xlsx 无 _images 时 | 解析 `drawingN.xml` → twoCellAnchor → (row, rId) → media/file |

匹配策略：精确匹配 `_row` → 容差 ±1 → 顺序匹配（兜底）。

### 2. 报价单列布局改进

| 功能 | 说明 |
|------|------|
| **公司信息区块** | 标题下方显示名称、地址、电话、邮箱（从 `company.json` 读取） |
| **Total 列** | 第 7 列 `Qty × Unit Price`，底部汇总行 |
| **型号/名称去重** | `model == name_zh` 时只显示 model，否则显示 `model\nname_zh` |
| **规格回退** | `specs` 字典 vs `spec_zh` 文本取更完整者（长度比较） |
| **"nan" 过滤** | `name_zh`/`name_en` 为 null/"nan" 时自动回退到 `sku`，`bilingual_text` 在 `name_en` 为空时跳过 |

### 3. DOCX 图片提取

新增 `extract_images_from_docx()`：从 `word/media/` 提取图片，按文件名序号顺序分配给产品。

### 4. 截断检测增强

`spec_cleaner.py` 新增 `normalize_spec()` 统一入口；`fix_truncated_spec()` 支持不同截断模式不同标记（`(尺寸单位缺失)` vs `(may be incomplete)`）；长文本末尾短词检测。

---

## 新增功能 (2026-05-06)

### 1. 三层策略择优（Excel / PDF / DOCX 通用架构）

所有解析器统一为三层策略架构，各解析器内部使用内建评分函数选择策略内最优：

| 解析器 | 策略 A | 策略 B | 策略 C | 内部评分 |
|--------|--------|--------|--------|---------|
| `universal_parser.py` | KV → Table 布局检测 | 内容推断列角色 | — | `score_result()` |
| `pdf_parser.py` | col_based / row_based | 内容推断列角色 | — | `_score_pdf_result()` |
| `doc_parser.py` | 表头关键词匹配 | 内容推断列角色 | 段落文本提取 | `_score_docx_result()` |

### 跨解析器择优（`backend/score.py`）

通用解析器与专用解析器两者结果用**信号组合评分系统**选优，不再比数量：

| 信号组合 | 分值 | 说明 |
|---------|------|------|
| 真型号 + 有价格 + 有参数 | +7 | 最强信号 |
| 真型号 + 有价格 | +5 | 强信号 |
| 真型号 + 有参数 | +4 | 中信号 |
| 真型号（只有型号） | +2 | 可接受 |
| 有价格无型号 | +1 | 弱信号 |
| 假型号(商品_R/产品_R) | -3 | 自动生成的假型号 |
| 空型号 + 无价格 | -3 | 噪音行 |
| 型号含冒号或超长 | -2 | 内容错列 |

全局一致性加成：≥3个不同真型号 +3，≥3个产品有价格 +2，噪音比例<20% +1。

最终 = (∑单行分 + ∑加成) ÷ 产品数，分高者胜。

### 2. 图片按列过滤

`image.py` 新增 `_detect_image_column()`：扫描表头检测"产品图片"/"图片"/"Picture"等关键词，定位产品图片列位置。三路提取（openpyxl / DISPIMG / drawing XML）都接受 `image_col` 参数，只提取该列附近的图片。`_image_col_matches()` 提供 ±1 宽容度。

**效果：** 新品报价表等含"适合图/包装图"列的文件，不再把包装图混入产品图。

### 3. 货币自动识别

`universal_parser.py` 新增 `_detect_currency()`：检查价格列头是否含 FOB/CIF/USD/$ → 设为 USD，否则 RMB。`web_products` 表新增 `currency` 列（默认 'RMB'）。前端显示：`currency === 'USD' ? '$' : '¥'`。

### 4. 备注附着系统

非产品行（说明行、电池价格、充电器价格、通用备注）不再被丢弃或做成独立产品，而是附着到上一个产品的 `remark` 字段：

- `_is_general_remark()` / `_is_battery_or_charger()` 分类检测
- `remark_text` 排除价格列，避免价格数字混入备注
- `quotation_excel.py` 输出灰色斜体备注行

### 5. 合并单元格处理

`extract_table_products()` 构建 `merge_map`：扫描 `ws.merged_cells.ranges`，合并区域的非 top-left cell 从 top-left 取值。`parse()` 中额外做合并单元格图片传播。

### 6. 产品库/报价历史自动刷新

`WorkspacePage` 新增 `productRefreshKey` 和 `quotationRefreshKey`，保存/生成后 state 自增 → `useEffect` 依赖触发重新 fetch。

### 7. 报价历史下载/删除

新增后端端点：
- `GET /api/quotations/{id}/download` — 从 `file_path` 返回文件
- `DELETE /api/quotations/{id}` — 删记录+删文件

报价生成时自动保存到 `web_quotations`（含 `file_path`），无需手动"保存到历史"。

### 8. 产品库批量删除

新增 `POST /api/products/batch-delete` 端点 + 前端"删除选中 (N)"按钮。

---

## 数据质量规则

| 规则 | 实现方式 |
|------|----------|
| **坏 SKU 过滤** | 跳过含 `\n` 或第 5 位前有 `:` 的 SKU |
| **测试用户排除** | 跳过 `user_id='test'` 的产品 |
| **去重优先级** | 同一 SKU 多用户存在时，保留 `user_id='ev_alls'` 版本 |
| **型号列** | 仅含干净 SKU（无规格泄露） |
| **规格列** | 每个参数单独一行（不是分号分隔） |

---

## 已知问题

| 严重度 | 文件 | 问题 | 状态 |
|--------|------|------|------|
| 🟡 中 | 24 个文件 | 裸 `except:` 会抓住 Ctrl+C | 需要修复 |
| 🟢 低 | `config.py`, `company.py` | 占位符值（XXX） | 已知限制 |

- **重复 SKU**：自动加后缀（-A, -B, ... -AA, -AB），不覆盖
- **图片关联**：三路匹配引擎自动处理所有源文件类型。DISPIMG 文件需 WPS 格式支持
- **图片性能**：图片路径预存到数据库，报价时直接读取，不做全局搜图。`--with-images` 可选
- **汇率**：实时从 rates.convert() 获取，不行就用缓存
- **FOB**：按 Incoterms 2020，卖方只负责装船，不安排海运
- **用户 ID**：80 个产品存在 `user_id='ev_alls'` 下。切换用户用 `--user-id` 参数
- **翻译**：基于词典（不依赖外部 API）。优先覆盖贸易专业词汇