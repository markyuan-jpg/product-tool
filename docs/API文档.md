# QuoteFlow API 文档

> 最后更新：2026-06-29
> 基础 URL：`https://api.quoteflow.it.com`

---

## 通用说明

### 认证
当前为匿名模式，无需注册/登录。会话通过 `X-Session-ID` header 识别：
```javascript
// 前端自动生成 UUID 并保存到 localStorage
const sessionId = localStorage.getItem('quote_session_id') || crypto.randomUUID();
localStorage.setItem('quote_session_id', sessionId);

// 每次请求携带
headers: { 'X-Session-ID': sessionId }
```

### 响应格式
```json
// 成功
{ "products": [...], "dedup": 3 }

// 失败
{ "detail": "错误描述" }
```

### 速率限制
| 端点 | 限制 |
|------|------|
| 注册/登录 | 5次/分钟 |
| 解析 | 20次/分钟 |

---

## 一、解析

### POST /api/parse
上传文件并解析产品信息。

**Request:**
```http
POST /api/parse
Content-Type: multipart/form-data
X-Session-ID: abc-123

file: [上传的Excel/PDF/Word文件]
```

**Response (200):**
```json
{
  "products": [
    {
      "model": "LED-001",
      "name_zh": "LED射灯",
      "name_en": "LED Spotlight",
      "spec_zh": "10W, 3000K, IP65",
      "spec_en": "10W, 3000K, IP65",
      "price_usd": 2.5,
      "price_rmb": 18.0,
      "currency": "USD",
      "image": "/uploads/images/abc.jpg",
      "category": "照明",
      "carton_size": "50x40x30cm",
      "gross_weight": 12.5,
      "net_weight": 11.0,
      "cbm": 0.06,
      "units_per_carton": 50,
      "packing_type": "纸箱"
    }
  ],
  "dedup": 0
}
```

**Response (400):**
```json
{ "detail": "不支持的文件格式，仅支持 .xlsx / .xls / .pdf / .docx" }
```

**Response (413):**
```json
{ "detail": "文件超过 50MB 限制" }
```

---

## 二、产品管理

### GET /api/products
获取当前会话的产品列表。

```http
GET /api/products
X-Session-ID: abc-123
```

### POST /api/products
保存/更新产品。

```http
POST /api/products
Content-Type: application/json
X-Session-ID: abc-123

{
  "model": "LED-001",
  "name_zh": "LED射灯",
  "price_usd": 2.5
}
```

### DELETE /api/products/{id}
删除单个产品。

### POST /api/products/batch-delete
批量删除。

```http
POST /api/products/batch-delete
X-Session-ID: abc-123

{ "ids": [1, 2, 3] }
```

---

## 三、单据生成

### POST /api/quotation
生成报价单 Excel。

```http
POST /api/quotation
Content-Type: application/x-www-form-urlencoded
X-Session-ID: abc-123

products=[{...}]
&company_name=My Company
&company_contact=John
&lang=bilingual
```

**Response (200):** 直接返回 xlsx 文件下载。

### POST /api/quotation/pdf
生成报价单 PDF。

### POST /api/pi
生成 Proforma Invoice。

### POST /api/packing
生成装箱单。

### POST /api/invoice
生成商业发票。

---

## 四、报价历史

### GET /api/quotations
获取历史报价列表。

### GET /api/quotations/{id}/download
下载历史报价文件。

### DELETE /api/quotations/{id}
删除历史报价。

---

## 五、配置

### POST /api/template/upload
上传公司模板。

### GET /api/bank/load
加载公司银行信息。

### POST /api/bank/save
保存公司银行信息。

### GET /api/images
获取产品图片。

```http
GET /api/images?path=/uploads/images/abc.jpg
```

### GET /api/exchange-rate
获取实时汇率。

### GET /api/health
健康检查。
