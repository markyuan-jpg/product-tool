# 系统架构与功能实现文档

> 本文档完整描述报价整合工具的系统架构、数据流、模块交互与核心实现细节。
> 读者对象：需要理解全系统的开发人员。
> 最后更新：2026-05-13（V2 解析器统一架构、多Sheet、共享常量）

---

## 一、架构总览

### 1.1 前后端分离架构

| 层 | 技术栈 | 端口 | 入口 |
|---|---|---|---|---|
| 前端 | Next.js (React) | 3000 | `landing/app/workspace/page.js` |
| 后端 | FastAPI (Python) | 8000 | `backend/main.py` |
| 核心引擎 | Python 模块包 | — | `product_tool/src/` + `product_tool/shared_keywords.py` |
| 数据库 | SQLite | — | `~/.product_tool/products.db` |

前端通过 `API_BASE`（默认 `http://localhost:8000`）调用后端所有接口。后端在启动时将 `product_tool/src` 加入 `sys.path`，直接导入核心模块。

### 1.2 组件树结构

```
WorkspacePage (page.js)
├── Nav (顶部导航)
├── UploadSection (上传解析区)
│   ├── 拖拽上传 DropZone
│   └── 解析结果表格 + "保存到产品库" 按钮
├── ProductLibrarySection (产品库区)
│   ├── 搜索/分页/全选/删除
│   ├── 导出面板
│   │   ├── 公司信息 (ExportSection)
│   │   ├── 产品明细 (ExportSection)
│   │   ├── 运输 (ExportSection)
│   │   ├── 付款 (ExportSection)
│   │   └── 备注 (ExportSection)
│   ├── 语言/货币选择器
│   ├── 导出类型按钮组
│   └── 预览面板
└── QuotationHistorySection (报价历史区)
    ├── 列表 + 全选
    └── 下载/删除/批量删除/一键清空
```

### 1.3 数据库 Schema

**`users` 表**（用户认证 — PostgreSQL）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| username | VARCHAR(100) UNIQUE | 用户名 |
| email | VARCHAR(255) | 邮箱（可选） |
| password_hash | VARCHAR(255) | bcrypt 哈希 |
| tier | VARCHAR(20) DEFAULT 'free' | free / pro |
| upload_count | INTEGER DEFAULT 0 | 月度上传计数 |
| upload_month | VARCHAR(7) DEFAULT '' | YYYY-MM |
| stripe_customer_id | VARCHAR(100) | Creem 客户 ID |
| subscription_id | VARCHAR(100) | Creem 订阅 ID |
| subscription_end | TIMESTAMP | 订阅到期时间 |
| created_at | TIMESTAMP | 注册时间 |

**`web_products` 表**（产品库）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| user_id | TEXT NOT NULL | 用户 ID |
| model | TEXT | 产品型号 |
| name_zh | TEXT | 产品名称 |
| spec_zh | TEXT | 规格参数 |
| price_rmb | REAL | 价格（原始币种） |
| price_cny | REAL DEFAULT 0 | 人民币换算价格 |
| price_usd | REAL DEFAULT 0 | USD 价格（可选） |
| image_path | TEXT | 图片路径 |
| category | TEXT | 分类 |
| currency | TEXT DEFAULT 'RMB' | 币种 |
| carton_size | TEXT DEFAULT '' | 外箱尺寸 |
| gross_weight | REAL DEFAULT 0 | 毛重 |
| net_weight | REAL DEFAULT 0 | 净重 |
| cbm | REAL DEFAULT 0 | 体积 |
| units_per_carton | INTEGER DEFAULT 0 | 每箱数量 |
| packing_type | TEXT DEFAULT '' | 包装类型 |
| created_at | TIMESTAMP | 创建时间 |

索引：`idx_wp_user(user_id)`, `idx_wp_time(created_at)`

**`web_quotations` 表**（报价历史）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INTEGER PK | 自增主键 |
| user_id | TEXT NOT NULL | 用户 ID |
| product_ids | TEXT | 产品 JSON 数组 |
| file_name | TEXT | 文件名 |
| file_path | TEXT DEFAULT '' | 文件存储路径 |
| created_at | TIMESTAMP | 创建时间 |

索引：`idx_wq_user(user_id)`

---

## 二、API 端点全集

### 2.1 认证与用户

所有认证端点使用双 Token 机制：
- **access_token**: 15 分钟过期，通过 `Authorization: Bearer <token>` 请求头传递
- **refresh_token**: 7 天过期，存储在 httpOnly cookie 中（`path=/api/auth`, `Secure`, `SameSite=Strict`），自动随同域请求发送

| 方法 | 路径 | 请求格式 | 响应 | 说明 |
|---|---|---|---|---|
| POST | `/api/auth/register` | `{username, password}` (FormData) | `{token, user}` + set-cookie `refresh_token` | 注册新用户，返回双 token |
| POST | `/api/auth/login` | `{username, password}` (FormData) | `{token, user}` + set-cookie `refresh_token` | 登录，返回双 token |
| POST | `/api/auth/refresh` | 读取 cookie `refresh_token` | `{token}` | 刷新 access_token，无需手动传参 |
| GET | `/api/user/me` | Header: `Authorization: Bearer <token>` | `{id, username, email, tier, upload_count}` | 获取用户信息及配额 |
| GET | `/api/user/usage` | Header: `Authorization: Bearer <token>` | `{upload_count, limit:20, product_count, product_limit:200, tier}` | 配额详情 |
| PUT | `/api/auth/change-password` | `{old_password, new_password}` (FormData) | `{status}` | 修改密码 |

**错误码说明**：
| 状态码 | 含义 | 示例 |
|--------|------|------|
| 400 | 请求参数错误 | 用户名已存在 / 密码至少6位 / 用户名或密码错误 |
| 401 | 未登录或 token 过期 | 登录已过期，请重新登录 |
| 403 | 无权限 | 此功能仅限专业版（Pro）用户使用 |

### 2.2 文件解析

| 方法 | 路径 | 请求格式 | 响应 | 说明 |
|---|---|---|---|---|
| POST | `/api/parse` | FormData: file | `{products[], count, parse_source, cache_key}` | 两步解析管道 |
| POST | `/api/parse/with-ai` | FormData: file + ai_backend | `{products[], count, parse_source}` | AI 增强解析 |

### 2.3 产品库

| 方法 | 路径 | 请求格式 | 响应 | 说明 |
|---|---|---|---|---|
| POST | `/api/products/save` | FormData: products (JSON) | `{status, inserted, updated}` | 保存/更新产品 |
| GET | `/api/products` | Header: Authorization | `{products[], total, limited}` | 获取产品列表 |
| DELETE | `/api/products/{id}` | — | `{status}` | 删除单个产品 |
| POST | `/api/products/batch-delete` | FormData: product_ids (JSON) | `{status, count}` | 批量删除 |

### 2.4 文档生成

| 方法 | 路径 | 请求格式 | 响应 | Pro? |
|---|---|---|---|---|
| POST | `/api/quotation` | FormData (products JSON + lang + currency + payment_terms + ...) | FileResponse (.xlsx) | 否 |
| POST | `/api/quotation/pdf` | FormData (同上) | FileResponse (.pdf) | 是 |
| POST | `/api/pi` | FormData (products + lang + buyer + bank + ...) | FileResponse (.xlsx) | 是 |
| POST | `/api/packing` | FormData (products + lang + shipping + ...) | FileResponse (.xlsx) | 是 |
| POST | `/api/invoice` | FormData (products + lang + bank + ...) | FileResponse (.xlsx) | 是 |

### 2.5 支付

| 方法 | 路径 | 说明 | 认证 |
|---|---|---|---|
| POST | `/api/payment/create-checkout` | Creem checkout（升级 Pro） | 需登录 |
| POST | `/api/payment/webhook` | Creem 回调（无需认证，HMAC-SHA256 验签） | 无 |

### 2.6 认证增强

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/auth/refresh` | 读取 httpOnly cookie → 发放新 access_token |

### 2.7 报价历史

| 方法 | 路径 | 请求格式 | 响应 |
|---|---|---|---|
| GET | `/api/quotations` | Header: Authorization | `{quotations[]}` |
| GET | `/api/quotations/{id}/download` | — | FileResponse |
| DELETE | `/api/quotations/{id}` | Header: Authorization | `{status}` |
| POST | `/api/quotations/batch-delete` | FormData: ids (JSON) | `{status, count}` |

### 2.8 模板与配置

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/template/upload` | 上传 Excel 模板提取公司信息 |
| POST | `/api/template/save` | 保存公司配置 |
| GET | `/api/template` | 获取公司配置（UI 可见字段） |
| POST | `/api/company/logo` | 上传 Logo |
| POST | `/api/template/document/{doc_type}` | 上传文档模板 |
| GET | `/api/template/document/{doc_type}` | 查询模板是否存在 |
| DELETE | `/api/template/document/{doc_type}` | 删除模板 |

### 2.9 图片服务

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | `/api/images` | `?path=` | 安全图片服务（仅允许白名单目录） |

白名单目录：
- `product_tool/temp_images/`
- `product_tool/data/`
- `backend/uploads/images/`

### 2.10 健康检查

| 方法 | 路径 | 响应 |
|---|---|---|
| GET | `/api/health` | `{status: "ok", time: "..."}` |

---

## 三、完整数据流

### 3.1 流程：上传 → 解析 → 展示

```
用户拖拽文件到 DropZone
  │
  ▼
前端 handleFile():
  1. 校验扩展名 (.xlsx/.xls/.pdf/.docx)
  2. 创建 FormData，append('file', file)
  3. POST /api/parse (60s 超时，AbortController)
  │
  ▼
后端 parse_file():
  Step 1 - 通用解析器 (仅 Excel):
    universal_parser.parse(save_path)
    → 返回 (df, parse_type, count, cache_key)
    → parse_type: 'kv' / 'table' / 'content' / 'empty'
  
  Step 2 - 专用解析器 (始终运行):
    Excel → run.py:parse_file()
    PDF → pdf_handler.extract_products_from_pdf_v2()
    DOCX → doc_parser.extract_products_from_docx()
    → 返回 df2
  
  Step 3 - 择优选择:
    判断逻辑（main.py + score.py）:
    ├─ 对两个解析器的输出分别用 score_dataframe() 评分
    │  ├─ 逐产品评分（7级信号组合）
    │  │  ├─ 真型号+有价格+有参数 → +7
    │  │  ├─ 真型号+有价格 → +5
    │  │  ├─ 真型号+有参数 → +4
    │  │  ├─ 真型号（只有型号） → +2
    │  │  ├─ 有价格无型号 → +1
    │  │  ├─ 假型号(商品_R/等) → -3
    │  │  ├─ 空型号无价格 → -3
    │  │  └─ 型号含冒号或超长 → -2
    │  └─ 全局一致性加成
    │     ├─ ≥3个不同真型号 → +3
    │     ├─ ≥3个产品有价格 → +2
    │     └─ 噪音比例<20% → +1
    └─ 最终 = (∑单行分 + ∑加成) ÷ 产品数，高分者胜出
    
    后处理: df2 有图片而 df 没有 → 按 _row+_sheet 匹配转移
    PDF: model 空值向前填充（共享上一行型号）
  │
  ▼
返回 JSON {products, count, parse_source, cache_key}
  │
  ▼
前端渲染表格:
  - 遍历 products[]
  - 图片用 src={API_BASE + '/api/images/?path=' + encodeURIComponent(path)}
  - onError → 显示"无图"占位
  - 价格前缀 p.currency === 'USD' ? '$' : '¥'
```

### 3.2 流程：保存到产品库

```
用户点击"保存到产品库"
  │
  ▼
前端 saveToLib():
  1. JSON.stringify(products)
  2. POST /api/products/save
     body: new URLSearchParams({products: JSON})
     header: Authorization: Bearer {token}
  │
  ▼
后端 save_products():
  1. 解析 products JSON
  2. 检查每个 item 必须有 model
  3. 去重检查: user_id + model 已存在 → UPDATE，否则 INSERT
  4. 免费版限制: 去重后不超过 200 个产品
  5. _extract_packaging_from_spec(): 从 spec_zh 解析包装信息
     关键词匹配: 'carton size', '毛重', '净重', 'cbm', 'qty/ctn' 等
  │
  ▼
返回 {status, inserted, updated}
```

### 3.3 流程：导出设置 → 生成文档

```
用户从产品库勾选产品
  │
  ▼
导出面板展开（5个可折叠区块）:
  公司信息 | 产品明细 | 运输 | 付款 | 备注
  语言选择: chinese / english / bilingual
  货币选择: USD / CNY
  导出类型: quotation / pdf / pi / packing / invoice
  │
  ▼
handleExport() / handleExportAll():
  1. 从 selected Set 取产品，合并每行自定义字段
     (qty, net_weight, gross_weight, carton_size, cbm, units_per_carton)
  2. 构建 URLSearchParams:
     - products: JSON.stringify(sel)
     - trade_terms, lang, company_name, ...
     - PI/Invoice 额外: bank_info (从 localStorage 读取)
  3. 单个: POST 到对应端点, a.click() 下载
  4. 一键全部: 依次调用 5 个端点（不计成败）
  │
  ▼
  PDF, PI, Packing, Invoice → 需要 Pro 权限
```

### 3.4 流程：生成报价 Excel

```
POST /api/quotation
  │
  ▼
后端 generate_quotation():
  1. 解析 products JSON
  2. 构建 company_info（UI 输入优先 → company.json 后备）
  3. 无图片产品 → match_sku_folder() 从 temp_images/data 匹配
  4. create_quotation(items, output_path, lang, with_images, company_info, payment_terms, currency)
  │
  ▼
quotation_excel.py create_quotation():
  → 先检查模板: get_template_path('quotation')
    模板存在 → apply_template() 复制模板填数据
    模板不存在 → QuotationExcel.write() 从头生成
  │
  ▼
QuotationExcel.write():
  1. add_products() → 规格格式化、多语言处理、USD 汇率转换
  2. 创建 Workbook:
     - 标题行: FOREIGN TRADE QUOTATION（语言自适应）
     - 公司信息块: name / address / tel / email
     - 信息行: Quotation No. / Date / Valid Until
     - 7 列表头: No. / Photo / Model+Name / Specs / Qty / Unit Price / Total
     - 每行产品: 交替行色 + 图片嵌入 (100x80px)
     - 备注行（灰色斜体，附加在对应产品下方）
     - 合计行
     - 条款块: Trade Terms / Payment / Packing / Delivery / Validity
  3. 自动列宽计算
  4. freeze_panes = 'A2'
  5. 附加 Raw Data 工作表
  │
  ▼
自动保存到 web_quotations 表
返回 FileResponse(.xlsx)
```

### 3.5 流程：生成 PI（形式发票）

```
POST /api/pi
  │
  ▼
后端 generate_pi():
  1. Pro 权限校验
  2. 加载公司配置 + 前端传来的银行信息
  3. generate_pi_xlsx(items, output_path, buyer_name, seller_config, ...)
  │
  ▼
pi_generator.py generate_pi_xlsx():
  1. translate_items() → 多语言翻译
  2. 先检查模板: get_template_path('pi')
     模板存在 → apply_template()
     模板不存在 → 从头生成
  3. Workbook 构建:
     - Logo（从 seller_config 读）或 [LOGO] 占位
     - 公司信息（B2:F2 合并）
     - 标题: PROFORMA INVOICE（18pt, 深蓝）
     - Invoice No. / Date / Buyer
     - 7 列表头（两层: 主标题 + 副标题）
     - 产品行: Photo / No. / Model+Name / Specs / Qty / Unit Price / Total
       - 图片嵌入 50x50px
       - USD 汇率转换（CNY→USD）
     - TOTAL AMOUNT 行
     - 大写金额 _num_to_words()
     - 11 条标准条款
     - 银行信息分行显示
     - 签名区
     - 页脚
  4. 打印布局: landscape, fitToWidth=1
```

### 3.6 流程：生成装箱单 / 商业发票

```
POST /api/packing → generate_packing_list()
POST /api/invoice → generate_commercial_invoice()
  │
  ▼
packing/generator.py:
  1. translate_items(pi_items, lang)
  2. 先检查模板 (packing/invoice)
  3. 从头生成 Workbook:
  
  装箱单结构:
  - 标题: PACKING LIST
  - Shipper / Consignee / Transport Details
  - 8列表头: Marks / Description / Qty / NW / GW / Meas / Carton Size / Qty/Carton
  - 产品行: 从 product_meta 读取包装字段
  - Total 行 + 大写件数
  - Remarks / Signature
  
  商业发票结构:
  - 标题: COMMERCIAL INVOICE
  - Seller / Invoice No. / Date / L/C No.
  - Buyer / Transport Details / Payment Terms / Incoterms
  - 7列表头: Item No. / Description / Spec / Qty / Unit / Unit Price / Total Amount
  - 产品行 + Subtotal
  - Freight & Charges / Total Amount
  - Country of Origin / HS Code / Bank Information
  - Signature
```

### 3.7 流程：图片提取与匹配

### 3.8 流程：Creem 订阅支付

```
用户点击"升级专业版"
  │
  ▼
POST /api/payment/create-checkout (需登录)
  │
  ▼
后端 payment.create_checkout_session():
  POST https://api.creem.io/v1/checkouts
  { product_id, success_url, metadata: { user_id } }
  → 返回 { checkout_url }
  │
  ▼
前端 window.location.href = checkout_url
  │
  ▼
Creem 托管页面完成支付（支持卡/Alipay/WeChat）
  │
  ├→ 成功 → Creem 跳转 /payment/success
  │        → 前端调 verifyAuth() 确认 tier='pro'
  │
  └→ Creem 异步 POST /api/payment/webhook (HMAC-SHA256)
          checkout.completed → user.tier = 'pro'
          subscription.canceled → user.tier = 'free'
```

### 3.9 流程：Token 刷新

```
前端 apiFetch() 遇到 401
  │
  ▼
调 POST /api/auth/refresh（自动携带 httpOnly cookie）
  │
  ├→ 成功 → 返回新 access_token → 重试原请求
  │
  └→ 失败 → clearAuth() → 跳转 /login
```

```
universal_parser.parse() 尾部:
  best_df = match_images_to_products(best_df, file_path)
  │
  ▼
image.py match_images_to_products():
  1. _detect_image_column() → 扫描表头找"产品图片"/"商品图"列
  2. extract_embedded_images() 三路合并:
     a. extract_openpyxl_images():
        → 遍历 ws._images
        → 读 anchor._from.row/col 确定行号
        → _image_col_matches() 过滤列
        → _data() 读二进制 → hash 去重保存
     
     b. parse_dispimg_images():
        → zip 打开 xlsx
        → 解析 xl/cellimages.xml → guid→rId
        → 解析 .rels → rId→media_file
        → 扫描工作表 XML 找 DISPIMG("guid") 公式
        → 按行定位
     
     c. parse_drawing_images():
        → 解析 xl/drawings/*.xml 的 twoCellAnchor
        → 读 from/row 定位行
        → 读 a:blip 的 rId → media_file
     
  3. 匹配策略（三优先级）:
     a. 精确匹配 (sheet, _row)
     b. ±1 容差
     c. 顺序兜底 images[idx % len(images)]
  
  4. 图片扩散: 同一 sheet 内 ±5 行, 空格从上行继承
  
  5. SKU 文件夹回退: match_sku_folder()
     → 在 data/ 和 temp_images/ 找文件名匹配的图片
```

### 3.8 流程：报价历史

```
文档生成后自动保存 (所有 5 个端点都有 auto-save 逻辑):
  conn.execute("INSERT INTO web_quotations ...")
  │
  ▼
前端 QuotationHistorySection:
  GET /api/quotations → 渲染历史列表
  GET /api/quotations/{id}/download → 下载
  DELETE /api/quotations/{id} → 删除（同时删文件）
  POST /api/quotations/batch-delete → 批量删除
  
后端自动标题匹配（main.py:768-786）:
  文件名含"形式发票"/"pi" → "PI #N"
  文件名含"装箱"/"packing" → "装箱#N"
  文件名含"发票"/"invoice" → "商业发票 #N"
  文件名含"pdf" → "PDF报价#N"
  其他 → "报价#N"
```

---

## 四、解析策略详解

### 4.1 universal_parser.py Excel 解析

**入口**: `parse(file_path) → (DataFrame, parse_type, count, cache_key)`

**前置过滤**: 检测文件头是否含 `FOREIGN TRADE QUOTATION` / `PROFORMA INVOICE` 等标记 → 跳过（避免重复解析本工具生成的文件）

**逐工作表处理**, 每 sheet 三策略并行 + 择优：

```
                           ┌─────────────────────────────────────────┐
                           │         detect_header_row()             │
                           │  扫描行 1-30，关键词匹配(型号/价格/规格)  │
                           │  + 非空列数 + 价格关键词加分(前15行)     │
                           │  特殊分 ≥10 且行号 ≥3 提前终止           │
                           └──────────────────┬──────────────────────┘
                                              ▼
                              ┌──────────────────────────────┐
                              │     is_kv_layout() 判断      │
                              │  表头≥4列且无 Model:标记 → 否 │
                              │  第一列有冒号结尾 → KV布局     │
                              │  第一列有3+纯数字 → 表格布局    │
                              │  否则检 65% 行≤2列 → KV       │
                              └──────────┬───────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              ▼                          ▼                          ▼
      ┌──────────────┐       ┌──────────────────┐       ┌──────────────────┐
      │  策略1: KV   │       │   策略2: Table    │       │  策略3: Content  │
      │              │       │                  │       │                  │
      │ 单产品KV:    │       │ map_columns():    │       │ infer_columns    │
      │ extract_kv   │       │ 关键词匹配 7 类列  │       │ _by_content():   │
      │ _product()   │       │ name/price/spec/  │       │ 逐列统计数字/    │
      │ → 1个产品    │       │ model/qty/packing │       │ 文本/型号特征    │
      │              │       │ /remark           │       │ 推断: price/     │
      │ 多产品KV:    │       │ 后备无匹配→position│       │ model/spec/skip  │
      │ extract_multi│       │ 猜测              │       │                  │
      │ _kv_products │       │                  │       │ parse_by_content  │
      │ → Model:标记 │       │ extract_table_    │       │ () → 无视表头    │
      │   切分产品   │       │ products():       │       │ 按内容角色提取    │
      │              │       │ 合并单元格传播     │       │                  │
      │              │       │ 备注/电池行附着    │       │                  │
      │              │       │ 价格列多级表头检测  │       │                  │
      └──────────────┘       └──────────────────┘       └──────────────────┘
                                         │
                                         ▼
                              score_result() 择优:
                              n*0.3 + has_model*0.3 + has_price*0.2 +
                              diversity*10*0.2 - label_penalty
                              prefix_penalty (产品_ 前缀惩罚)
```

**关键函数详解**:

`detect_header_row(ws)`:
- 评分指标: 关键词命中 +2、非数字文本 +1、3+ 非空列 +2、价格关键词 +10（仅前15行）
- 公司信息行惩罚: 低分非空行 -2
- 返回最高分行号, 最低门槛 2 分, 否则返回 1

`map_columns(headers, max_col)`:
- COLUMN_SIGNALS: name(19词)/price(26词)/spec(9词)/model(14词)/qty(12词)/packing(4词)/remark(5词)
- SKIP_COLUMN_SIGNALS: serial/no./image/picture/photo/序号/图片
- 先关键词匹配, 后从保留列中 position 猜测 name_col

`is_kv_layout(ws, header_row)`:
- 关键检测: 表头≥4非空且无 Model:标记 → 表格布局（false）
- 第一列冒号结尾 ≥2 → KV（true）
- 第二条件: 检查 Model: / 型号: 标记（支持 col2 标记检测）

`extract_table_products(ws, header_row, col_map)`:
- 合并单元格传播（merge_map 缓存 top-left 值）
- 电池/充电器行 → 附到上一个产品备注
- 备注/条款行 → 附到上一个产品备注
- 型号为空但有合理价格 → 生成占位编号
- `is_product_row()` 四重判断: 型号模式→产品 / 跳过词→非产品 / 有效数量+价格→产品 / 合理长度名称→产品

`extract_price_from_value(text)` → 价格提取, 优先级:
1. `数字+USD` / `USD+数字` → 原始价 + `currency:USD` + `price_cny`（汇率换算）
2. `¥+数字` / `CNY+数字` / `RMB+数字` / `数字+元` → 原始价 + `currency:CNY`
3. 纯数字千分位 → 范围过滤 (0.01~1,000,000) + 技术单位排除

`_detect_currency(ws, header_row, price_col)`:
- 检查价格列头含 USD/$/FOB/CIF 等 → 'USD', 否则 'RMB'

### 4.2 pdf_parser.py PDF 解析

**入口**: `extract_products_from_pdf_v2(pdf_path) → DataFrame`

**前置**: 提取所有表格（pdfplumber）+ 所有图片（PyMuPDF）

**逐表三策略并行**:

```
策略0: KV 规格表（≤2 列参数表，优先）
  - 检测: 参数名列占比 >60% + 数据列 ≤2
  - 所有行合并为 1 个产品
  - 识别 Model: 行 → 型号名
  - 识别 Price/EXW/价格 行 → 价格
  - 其余行 → 规格拼接

策略A: 布局检测
  detect_table_layout(table):
  - 检测表头含 Model/型号 关键词
  - 第一列关键词 vs 第一行关键词 → col_based / row_based
  
  col_based（每列=产品）:
  - 表头含型号, 第一列是参数名
  - 遍历每列: Model → 产品名
  - 参数遍历: price 检测(含货币标记/价格关键词)、包装列、规格列

  row_based（每行=产品）:
  - 第一列型号, 第二列序号跳过
  - 向下填充空型号

策略B: 内容驱动（兜底）
  _classify_pdf_columns(): 逐列内容分析
  - 跳过列: serial/no./image/photo
  - 包装列: pcs/ / carton / CBM / 毛重 等关键词
  - 序列号: 纯数字 1-999
  - 价格列: ¥/$ 剥离后浮点数检测
  - 型号列: 字母+数字组合
  - 文本列: 平均长度 <25 → model, 否则 spec
```

**择优逻辑**:
- 布局策略 (col/row/kv) 和内容策略各自取评分最高
- 内容策略仅当评分 > 布局评分 × 1.5 时才胜出（防止内容策略靠数量碾压）

`_score_pdf_result(df, source)`:
- `log(n+1)*0.8 + has_model*0.15 + has_price*0.4 + diversity*10*0.3`
- source_boost: 布局策略且有真产品 ×2.0
- label_penalty: 标签占比 >30% 时 ×0.5

**Docling 后备解析**：

```
触发条件:
  仅当当前表格的所有候选（kv_spec / col_based / row_based / content）满足以下任一条件时：
  ├─ 返回空 DataFrame（没有成功提取任何产品）
  └─ 所有候选评分 _score_pdf_result() < 0.6

调用链:
  1. extract_products_from_pdf_v2() 对每张表执行完正常候选管道后
  2. if not all_products and _USE_DOCLING:      ← 整个 PDF 无任何产品时才触发
  3. 调用 _parse_pdf_via_docling(pdf_path)
  4. 返回 DataFrame 追加到 all_products
  5. 后续跨表合并/评分/过滤与正常管道一致

_parse_pdf_via_docling(pdf_path) 函数:
  输入: PDF 文件路径
  输出: Optional[pd.DataFrame]
  列: model, name_zh, price_rmb, spec_zh, currency, _image_path

  处理流程:
    if not _USE_DOCLING or not _HAS_DOCLING:
        return None          ← 环境变量未设置或 docling 未安装时静默跳过

    converter = DocumentConverter()
    result = converter.convert(pdf_path)   ← Docling 解析
    doc = result.document

    # 优先提取表格（产品目录通常是表格）
    if doc.tables:
        for table in doc.tables:
            rows = table.export_to_dict()
            第一行→表头，后续行→产品
            model=row[0], price=正则提取, spec=其余列拼接

    # 无表格时走文本兜底
    if not products and doc.text:
        逐文本项检测 型号模式 → 价格 → 规格

评分复用:
  df_best 进入现有 all_products 管道后，与其他候选一样通过
  pd.concat → 跨表价格匹配 → 图片关联 → 模型过滤

依赖处理:
  USE_DOCLING=0（默认）→ 不导入 docling，零开销
  USE_DOCLING=1 但 pip install docling 未安装 → logging.info 提示安装，不崩溃


**跨表价格匹配**: 主表价格全空时, 从辅助表按列位置匹配 USD 价格（自动汇率换算）

**后过滤** `_is_real_model()`:
- 含冒号 → 排除
- 纯数字且 ≥2 位 → 保留
- 必须含字母+数字
- 排除规格表达式 (mm\*mm, usd$ 等)
- 排除已知参数名 (motor/battery/weight 等 40+ 关键词)

**图片关联** `_associate_images_to_products()`:
- PDF 提取的全部图片
- 按 model 名在图片文件名中匹配
- 没匹配到 → 按产品顺序分配（每个产品取自己的第一张）

### 4.3 API 层 Step 3 择优比较（评分系统）

择优逻辑已改为 **信号组合评分系统**（`backend/score.py`），不再简单比数量：

```python
# score.py — score_dataframe() 评分流程

# 逐产品评分（score_product_row）
#   真型号+价格+参数 → +7   ⭐ 最强
#   真型号+价格       → +5
#   真型号+参数       → +4
#   真型号（只有型号） → +2
#   有价格无型号       → +1   ⚠️ 弱
#   假型号(商品_R等)   → -3   ❌
#   空型号无价格       → -3   ❌
#   型号含冒号/超长    → -2   ❌

# 全局一致性加成
#   ≥3个不同真型号 → +3
#   ≥3个产品有价格 → +2
#   噪音比例<20% → +1

# 最终 = (∑单行分 + ∑加成) ÷ 产品数
selector = 'specialized' if spec_score > uni_score else 'universal'
```


### 4.4 价格配置化（price_config.json）

**行业检测链**（优先级从高到低）：
```
1. --industry 命令行参数
2. PRICE_INDUSTRY 环境变量
3. 文件名正则匹配（config.price_config.json.industry_detection.rules）
   例: "ev_bike.xlsx" 含 "ev" → industry = "ev"
4. config.default_industry（默认 "ev"）
```

**single_spec_parser.py 调用链**：
```python
parse(file_path, industry=None)           # 入口，industry 可选
  → ic = get_industry_config(industry, file_path)  # 自动检测行业
  → parse_composite_price(text, ic)       # 使用配置的 secondary_keywords 分类配件
  → classify_price(item_name, ic)         # 匹配 primary / secondary 返回 (type, label, is_primary)
  → resolve_priority(prices, 'largest')   # first|last|largest|most_common
```

**param_price_parser.py 调用链**：
```python
is_price_marker(text, ic)                # 用配置的 main_price_keywords 检测价格行
extract_price_from_string(value, ic)     # 用配置的 value_range 验证价格有效性
```

**正则匹配示例（price_config.json）**：
```json
{
  "secondary_keywords": [
    {"type": "battery", "keywords": ["电池", "battery", "\\d+V\\d+Ah"], "use_regex": true, "label": "Battery Price"}
  ]
}
```
匹配 `"Battery: 2530 CNY"` → item_name="Battery" → type="battery" → price=2530


### 4.4 run.py 专用解析器选择

`parse_file()` 为 Excel 文件先调 `detect_parser_type()`:

| 检测条件 | 解析器 | 对应模块 |
|---|---|---|
| 表头含"车型"等 | 'table' | param_price_parser.parse_table |
| 含 Model:/型号: 标记 | 'param_price' | parsers.parse_param_price |
| 含 Proforma Invoice | 'invoice' | invoice_parser.parse_invoice |
| 列少+有价格+型号 | 'price_table' | price_table_parser.parse_price_table |
| 其他 | 'single_spec' / 'default' | single_spec / excel_parser_v3 |

---


### 4.5 CLI 装箱单/商业发票集成（run.py）

**新增参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `--packing` | flag | false | 生成装箱单 + 商业发票 |
| `--buyer-name` | text | — | 买方名称（必填） |
| `--buyer-address` | text | — | 买方地址 |
| `--port-loading` | text | Qingdao | 启运港 |
| `--port-discharge` | text | — | 目的港（必填） |
| `--vessel` | text | — | 船名/航次 |
| `--bl-no` | text | — | 提单号 |
| `--trade-terms` | text | FOB | 贸易条款 |
| `--no-interactive` | flag | false | 跳过交互输入 |

**交互逻辑**：
```python
is_interactive = not args.no_interactive and sys.stdin.isatty()

if is_interactive:
    if not buyer_name:       buyer_name = input("  Buyer name: ")
    if not port_discharge:   port_discharge = input("  Port of discharge [Hamburg]: ") or 'Hamburg'
    if not buyer_address:    addr = input("  Buyer address (optional): ")

if not buyer_name or not port_discharge:
    print("Error: --buyer-name and --port-discharge are required")
    sys.exit(1)
```

**调用链**：
```
run.py --packing --buyer-name "ABC" --port-discharge Hamburg
  → generate_packing_list(pi_items, buyer_name, port_loading, port_discharge, ...)
  → generate_commercial_invoice(pi_items, buyer_name, port_loading, port_discharge, ...)
  → 两张表同时生成，文件名后缀 _PackingList.xlsx / _Invoice.xlsx
```

**缓存**：`packing_cache.json` 按 buyer_name 存储地址/港口信息，下次交互时复用。


## 五、前端组件详解

### 5.1 UploadSection

```
Props: { onSaveSuccess }
State: dragOver, parsing, parseError, products[], saving, saveMsg, failedImages(Set)

handleFile(file):
  - 校验扩展名: .xlsx .xls .pdf .docx
  - FormData POST /api/parse 60s 超时
  - setProducts(d.products)

saveToLib():
  - URLSearchParams: {products: JSON.stringify(products)}
  - POST /api/products/save
  - 成功后清空 products, 触发 onSaveSuccess → 刷新产品库

渲染:
  - 拖拽区（svg 上传图标 + 提示文字）
  - 解析结果表格: 图片(无图回退) / 型号 / 名称 / 规格 / 价格
  - "保存到产品库" 按钮
```

### 5.2 ProductLibrarySection

```
Props: { refreshKey, user, onQuotationGenerated }
State: products[], total, search, selected(Set), exportOpen, exportType, 
       productMeta{}, customers[], piBuyerName/Address/..., tradeTerms,
       quotationLang, piCurrency, 包装/运输/银行 等 30+ 字段

特征:
  1. 搜索过滤: match(model/name_zh)
  2. 多选: selected Set, 全选/反选
  3. 内联编辑: qty/nw/gw/ctn/cbm/upc → productMeta[id][field]
  4. 批量设置数量
  5. 客户管理: localStorage 存取
  6. 导出状态持久化 → localStorage
    
导出面板:
  ExportSection(title, sectionKey):
  - 可折叠展开, icon + 标题
  - 5 子面板: 公司/产品明细/运输/付款/备注

导出流程:
  handleExport():
  1. 构造产品数组合并自定义字段
  2. URLSearchParams 含所有字段
  3. 根据 exportType 选端点 + 文件名
  4. POST, blob → a.click() 下载
  
  handleExportAll():
  循环 5 个端点依次请求
  (quotation → pdf → pi → packing → invoice)
```

### 5.3 QuotationHistorySection

```
Props: { refreshKey }
State: quotations[], selectedIds(Set)

功能:
  - GET /api/quotations → 展示列表
  - title 自适应: PI #N / 装箱#N / 报价#N
  - 单/多/全选 + 批量删除
  - 下载: 解析 content-disposition 文件名
  - 一键清空
```

---

## 六、导出设置字段全集

所有导出端点接受 FormData URLSearchParams 格式。

### 产品字段（每个产品对象 JSON）

```javascript
{
  model: string,
  name_zh: string,
  spec_zh: string,
  price_rmb: number,
  price_cny: number,                    // RMB换算价格
  _image_path: string,
  image_path: string,
  currency: string,
  qty: number,                    // 自定义
  net_weight: number,             // 自定义
  gross_weight: number,           // 自定义
  carton_size: string,            // 自定义
  cbm: number,                    // 自定义
  units_per_carton: number        // 自定义
}
```

### 表单字段统一表

| 字段 | 适用于 | 说明 |
|---|---|---|
| products (JSON) | 全部 | 产品数组 |
| lang | 全部 | chinese/english/bilingual |
| currency | quotation/pdf/pi/invoice | USD/CNY |
| trade_terms | 全部 | EXW/FOB/CIF/DDP |
| payment_terms | quotation/pdf/pi/invoice | 付款条件 |
| company_name | quotation/pdf | 发货人/供应商 |
| company_contact | quotation/pdf | 联系人 |
| company_phone | quotation/pdf | 电话 |
| buyer_name | pi/packing/invoice | 买方名称 |
| buyer_address | pi/packing/invoice | 买方地址 |
| buyer_contact | pi | 买方联系人 |
| buyer_tel | pi | 买方电话 |
| buyer_email | pi | 买方邮箱 |
| port_loading | packing/invoice | 启运港 |
| port_discharge | packing/invoice | 目的港 |
| port_destination | pi | 目的港 |
| vessel | packing/invoice | 船名/航次 |
| bl_no | packing/invoice | 提单号 |
| origin_country | packing/invoice | 原产国 |
| packing_type | packing | CARTON/Pallet/Box/Bag/Drum |
| packing_qty | packing | 包装数量 |
| brand_name | pi | 品牌名 |
| bank_beneficiary | pi/invoice | 收款人 |
| bank_name | pi/invoice | 银行名称 |
| bank_address | pi/invoice | 银行地址 |
| bank_account | pi/invoice | 银行账号 |
| bank_swift | pi/invoice | Swift Code |

---

## 七、模板系统

### 7.1 文档模板

**存储位置**: `~/.product_tool/templates/{type}.xlsx`

**支持的文档类型**: quotation, pi, packing, invoice

**上传/查询/删除**: `/api/template/document/{doc_type}`

**使用流程**:
```
生成文档时:
  1. get_template_path(doc_type) → 检查 ~/.product_tool/templates/{type}.xlsx
  2. 模板存在 → apply_template(data, template_path, output_path)
  3. 模板不存在 → 从头生成（所有 generator 都有 fallback）

apply_template():
  1. shutil.copy2 复制模板
  2. find_data_table() → 找第一条完整数据行（≥3 列有内容）
  3. 清空旧数据（保留表头）
  4. 按列号填入: No. / Model / Spec / Qty / Unit Price / Total
```

**当前状态**: 模板目录为空（调用方都有从头生成的回退逻辑）

### 7.2 公司配置模板

| 端点 | 说明 |
|---|---|
| POST `/api/template/upload` | 上传 Excel 扫描前 10 行提取公司名/地址/联系/电话 |
| POST `/api/template/save` | 保存到 `company.json`（仅 UI 可见字段） |
| GET `/api/template` | 读取公司配置 |

`company.json` 存储于 `~/.product_tool/company.json`，包含: name, name_en, address, address_en, city, tel, email, website, contact_person, logo_path, bank 信息

---

## 八、图片系统

### 8.1 三路提取策略

```
extract_embedded_images(file_path):
  ├── extract_openpyxl_images()  [标准嵌入]
  │   └── 遍历 ws._images, 读 anchor._from.row 定位
  │
  ├── parse_dispimg_images()     [WPS 公式]
  │   └── zip → cellimages.xml → 公式 DISPIMG("guid") → media 文件
  │
  └── parse_drawing_images()     [标准 drawing]
      └── xl/drawings/*.xml → twoCellAnchor → a:blip → rId → media
```

三路合并策略: openpyxl 优先 → DISPIMG 补充 → drawing 兜底（目标 sheet+row 不重复）

### 8.2 图片列过滤

`_detect_image_column()`: 扫描表头列名（产品图片/商品图/picture）
`_image_col_matches()`: 锚点列在图片列 ±1 容差内 → 保留（避免混入包装图/尺寸图）

### 8.3 SKU 文件夹回退

`match_sku_folder(sku, image_dirs)`:
- 精确匹配 (fname == sku) → score=3
- 包含匹配 (sku in fname or fname in sku) → score=2
- 部分匹配 (sku 的 `-` 分隔部分匹配) → score=1
- 取分数最高的候选

### 8.4 安全服务

`/api/images/` 路径白名单校验:
- 解析绝对路径 → 检查是否在 allowed_dirs（temp_images / data / uploads/images）
- 防止 path traversal 攻击

---



---



## 十、配额系统

### 10.1 免费版限制

| 维度 | 限制 | 检测时机 |
|------|------|---------|
| 月度上传次数 | 20 次/月 | POST `/api/parse` 时校验 |
| 产品库容量 | 200 个产品 | POST `/api/products/save` 时校验 |
| PDF 报价 / PI / 装箱单 / 商业发票 | 不可用 | 各端点内部 `require_pro()` 拦截 |

### 10.2 配额检测逻辑

```python
# auth.py — 每次请求时检查月度重置
if user.tier == 'free':
    current_month = datetime.utcnow().strftime('%Y-%m')
    if user.upload_month != current_month:
        user.upload_count = 0
        user.upload_month = current_month

# main.py — 上传限制（parse_file 入口）
if not await check_upload_limit(user, db)(user, db):
    raise HTTPException(403, "免费版每月限上传 20 个文件")

# main.py — 产品库容量（save_products 入口）
if user.tier != 'pro':
    current_count = conn.execute("SELECT COUNT(*) FROM web_products WHERE user_id=?", [uid]).fetchone()[0]
    if current_count >= 200:
        raise HTTPException(403, "免费版最多保存 200 个产品")
```

### 10.3 配额展示

前端 `WorkspacePage` 顶部 amber 进度条（仅免费用户可见）：
- 显示：`上传 X/20 次 | 产品 X/200 个`
- 附 `升级专业版` 链接跳转 `/pricing`


---

## 九、去重引擎（DedupEngine）

**位置**: `product_tool/src/dedup_engine.py`

**入口**: `dedup_dataframe(df) → df`

**7 步管道**:

```
Step 1: _filter_by_score()
  score_product(): 型号长度>2 +1, 含 product 关键词 +2, 含噪声词 -1
  score < threshold → 丢弃

Step 2: _normalize_keys()
  fuzzy_key: 全小写去空格去特殊字符
  normalized_key: 去多余空格
  spec_hash: MD5(normalized_spec)[:8]

Step 3: _fuzzy_group()
  按 fuzzy_key 分组 → defaultdict(list)

Step 4: _detect_conflicts()
  组内冲突检测:
  - spec_hash 差异 → spec_mismatch
  - 价格差异 <5% → same spec, 合并
  - 价格差异 >5% → 拆分为独立版本

Step 5: _merge_groups()
  - 单元素组 → single
  - spec_mismatch → 保留每个版本 (multi_spec)
  - 合并组 → 取最长 model + 最长 spec + 价格平均
  - 图片取第一个有值的

Step 6: _split_by_price()
  同 normalied_key 组内价格差异 >20% → 拆分为 price_split

Step 7: _report()
  统计 status_counts
```

---

## 十、权限与限制

### 10.1 免费版限制

| 维度 | 免费版 | Pro 版 |
|---|---|---|
| 产品库容量 | 200 个（去重后不重复 model 数） | 不限 |
| 上传次数 | 20 次/月 | 不限 |
| PDF 报价 | ❌ | ✅ |
| PI (形式发票) | ❌ | ✅ |
| 装箱单 | ❌ | ✅ |
| 商业发票 | ❌ | ✅ |

### 10.2 上传大小限制

- 单个文件: 50MB (`MAX_UPLOAD_BYTES = 50 * 1024 * 1024`)
- 解析后文件自动删除（`finally: os.remove(save_path)`）

### 10.3 安全措施

- CORS 白名单: localhost:3000, 127.0.0.1:3000
- 安全头: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy
- 图片路径白名单校验
- SQLite 参数化查询（防注入）

---

---


## 数据迁移（SQLite → PostgreSQL）

### 迁移脚本：migrate_data.py

**作用**：一次性将本地 SQLite 数据导入 Supabase PostgreSQL。幂等，可重复运行。

**核心逻辑**（伪代码）：
```python
async def migrate_users(auth_db):
    src = sqlite3.connect('auth.db')
    rows = src.execute("SELECT * FROM users").fetchall()
    for row in rows:
        exists = await session.get(User, row['id'])
        if exists:
            # 更新已有记录（重跑场景）
            exists.username = row['username']
            exists.tier = row.get('tier', 'free')
        else:
            session.add(User(id=row['id'], username=row['username'], ...))
    await session.commit()

async def migrate_products(products_db):
    src = sqlite3.connect(products_db)
    rows = src.execute("SELECT * FROM web_products").fetchall()
    for row in rows:
        exists = await session.get(Product, row['id'])
        if not exists:
            session.add(Product(
                id=row['id'],
                user_id=int(row['user_id']),     # SQLite TEXT → PostgreSQL INTEGER
                model=row['model'],
                price_rmb=row['price_rmb'],
                price_cny=row.get('price_cny', 0),
                currency=row.get('currency', 'RMB'),
                ...
            ))
    await session.commit()
```

**user_id 关联**：SQLite 中 `user_id` 存储为文本（从 JWT `sub` 解析），PostgreSQL 中定义为 `INTEGER FK → users.id`。迁移时通过 `int(row['user_id'])` 转换，前提是 auth.db 和 products.db 的 user_id 一致。

**运行方式**：
```bash
cd backend
# 确保 .env 已配置 DATABASE_URL
python migrate_data.py
```

**前置条件**：
- Supabase 项目已创建，`DATABASE_URL` 配置正确
- SQLite 文件存在（`backend/auth.db` + `~/.product_tool/products.db`）
- 首次运行前确保 PostgreSQL 中无数据（或已有空表）

---

## 十一、模块依赖关系图

```
web (page.js)
  │ HTTP
  ▼
backend/main.py  (FastAPI, 端口 8000)
  │
  ├── universal_parser.py  (通用 Excel 解析)
  │     ├── image.py (match_images_to_products)
  │     └── openpyxl
  │
  ├── run.py:parse_file()  (专用解析器路由)
  │     ├── excel_parser_v3 / param_price_parser / invoice_parser / price_table_parser / single_spec_parser
  │     ├── pdf_parser.py (pdfplumber + PyMuPDF)
  │     ├── doc_parser.py
  │     └── image.py (match_images_to_products)
  │
  ├── quotation_excel.py → QuotationExcel  (报价单生成)
  │     ├── excel_template.py (模板引擎)
  │     └── doc_shared.py (翻译/多语言)
  │
  ├── pi_generator.py  (形式发票生成)
  │     ├── excel_template.py
  │     └── doc_shared.py
  │
  ├── packing/generator.py  (装箱单 + 商业发票)
  │     ├── excel_template.py
  │     └── doc_shared.py
  │
  ├── image.py  (图片提取引擎)
  │     ├── openpyxl._images
  │     ├── zip+xml (DISPIMG / drawing 解析)
  │     └── glob (文件夹图片匹配)
  │
  ├── auth.py  (认证/授权)
  ├── company.py  (公司配置)
  ├── database.py  (SQLAlchemy ORM + PostgreSQL)
  ├── alembic/  (数据库迁移)
  ├── payment.py  (Creem 支付)
  ├── ai_parser.py  (AI 列检测)
  ├── dedup_engine.py  (去重引擎)
  ├── price_config.py  (价格配置) │ config/price_config.json
  └── rates.py  (汇率)
```

---

## 十二、关键设计决策

1. **两步解析+第三方比较**: 通用解析器（结构分析）和专用解析器（格式特化）各自独立运行，在 API 层用型号+价格组合评分选优，兼顾覆盖率和精确度。

2. **三路策略并行**: Excel 和 PDF 解析器内部都采用多策略并行 + scorer 选优，而不是单一策略容错，提高对不同文件格式的适应能力。

3. **模板引擎兜底**: 文档生成器先检查用户上传模板，存在则用 `apply_template()` 复制填数，不存在则从头生成，模板系统零侵入。

4. **图片三路提取**: openpyxl（标准嵌入）、DISPIMG 公式（WPS）、drawing XML（标准 xlsx）三路独立解析后合并，应对不同 Excel 实现。

5. **行号+sheet 匹配**: 解析结果携带 `_row` 和 `_sheet` 元数据，后续图片匹配/数据转移都基于此，在跨解析器结果合并时保持上下文一致性。

6. **状态持久化**: 导出设置（贸易术语、付款条件、语言、港口等）通过 `localStorage` 持久化，下次会话自动恢复。

7. **价格配置化**: 通过 `config/price_config.json` 解耦价格检测规则，支持多行业配置+环境变量覆盖+正则匹配+四策略优先级解析。

8. **Docling 后备**: PDF 解析在规则引擎失败时自动降级到 Docling（`USE_DOCLING=1`），通过现有评分系统自然择优，不干扰正常解析速度。

9. **列选择过滤**: 导出面板新增「保留列」复选框，导出时未被选中的列数据在前端级置零/置空，后端 generator 无需感知。

10. **双 Token 认证**: access_token(15min) + refresh_token(httpOnly cookie, 7天)，前端 401 自动刷新，降低 XSS 泄露风险。

11. **Creem Merchant of Record**: 用 Creem 替代 Stripe，自动处理全球税务合规，支持支付宝/微信支付。

12. **Supabase PostgreSQL**: 用户数据和配额管理迁移至 PostgreSQL（Supabase 免费计划），产品库数据保留 SQLite 待后续迁移。

13. **去重 pipeline**: DedupEngine 的 7 步管道（过滤→归一→分组→冲突检测→合并→价格拆分→报告）在 `run.py --merge` 模式和 CLI 入口中使用，但在 Web API 的产品保存路径中直接用 SQL `user_id + model` 做简单去重。

14. **SEO 配置**: 前端通过 Next.js 内置机制实现 SEO：
   - `landing/app/sitemap.js` 自动生成 `/sitemap.xml`，收录首页、定价页、工作原理页
   - `landing/app/robots.js` 生成 `/robots.txt`，允许爬虫访问公开页，屏蔽 `/workspace/`、`/login/`、`/api/` 等需登录页面
   - `landing/app/layout.js` 导出 `metadata` 对象，设置标题/描述/Open Graph/Twitter Card
   - 子页面（`how-it-works/page.js`、`pricing/page.js`）在 `useEffect` 中运行时更新 `document.title` 和 meta description，弥补静态 metadata 无法覆盖动态路由的不足
