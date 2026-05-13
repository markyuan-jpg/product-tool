# 报价单改进实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复报价单生成器的 6 类问题：图片嵌入、规格空缺与截断、Total 列、公司信息、型号/名称去重、格式统一

**Architecture:** 修改 3 个核心文件 + 1 个源文件调查。`spec_cleaner.py` 增强截断检测和规范化入口；`quotation_excel.py` 修改列布局、公司信息区块、图片逻辑和 spec 调用链；`pdf_parser.py` 可能修复跨页截断。

**Tech Stack:** Python 3.10+, openpyxl, pytest, sqlite3

---

### Task 1: 增强 spec_cleaner.py — 截断检测 + normalize_spec 入口

**Files:**
- Modify: `src/parsers/spec_cleaner.py:15-21,36-131`
- Test: `tests/test_spec_cleaner.py:50-68`

- [ ] **Step 1: 增强 `fix_truncated_spec()` — 不同截断用不同标记 + 长文本末尾短词检测**

在 `src/parsers/spec_cleaner.py` 中，重构 `fix_truncated_spec()`：

```python
# 替换 TRUNCATION_PATTERNS：
TRUNCATION_RULES = [
    (r'\d+\*\s*$', '(尺寸单位缺失)'),  # "1360*" → 尺寸单位缺失
    (r'\*\s*$', '(may be incomplete)'),
    (r'-\s+$', '(may be incomplete)'),
    (r'[:：]\s*$', '(may be incomplete)'),
    (r',\s*$', '(may be incomplete)'),
]

SAFE_WORDS = frozenset({
    'the', 'and', 'for', 'box', 'set', 'pcs', 'pc', 'kg', 'mm', 'cm',
    'in', 'ft', 'v', 'a', 'w', 'kw', 'ah', 'mah', 'rpm', 'km', 'lb',
})
```

```python
def fix_truncated_spec(text: str) -> str:
    if not text or len(text) < 3:
        return text

    for pattern, mark in TRUNCATION_RULES:
        if re.search(pattern, text):
            if not text.endswith(mark):
                text = text + mark
            return text

    # 长文本末尾只有 1-3 个字符的单词 → 可能截断
    # 如 "Front d" (Front disc brake 被截断)
    if len(text) > 60:
        last_word_match = re.search(r'(\s+|\n)([a-zA-Z]{1,3})\s*$', text)
        if last_word_match:
            last_word = last_word_match.group(2).lower()
            if last_word not in SAFE_WORDS:
                mark = ' (may be incomplete)'
                if not text.endswith(mark):
                    text = text + mark
                    import logging
                    logging.warning(f"Detected possible truncation at end: ...{last_word!r}, appended marker")

    return text
```

- [ ] **Step 2: 新增 `normalize_spec()` 统一入口函数**

在 `src/parsers/spec_cleaner.py` 末尾添加：

```python
def normalize_spec(text: Optional[str]) -> str:
    """统一规格文本处理入口：清洗 + 格式化 + 截断检测"""
    return clean_spec(text)
```

更新 `__all__` 或模块导出（如有需要，在 `spec_formatter.py` 中也需要导入）。

- [ ] **Step 3: 更新测试文件 — 新增截断模式测试 + 修复现有测试**

修改 `tests/test_spec_cleaner.py` 中 `TestFixTruncatedSpec` 的 `test_ends_with_star`：

```python
def test_ends_with_star(self):
    result = fix_truncated_spec("Package: 1360*")
    assert "(尺寸单位缺失)" in result  # 原来是通用 (may be incomplete)
```

同时修改 `TestCleanSpec` 中两个测试（因为 `1360*` 现在标记为 `(尺寸单位缺失)` 而非通用标记）：

```python
def test_truncation_detected(self):
    result = clean_spec("Package: 1360*")
    assert "(尺寸单位缺失)" in result  # 原来是 (may be incomplete)

def test_complex_scenario(self):
    raw = "Motor：4000W Battery：72V 20AH Package size：1360*"
    result = clean_spec(raw)
    assert ':' in result
    assert '\n' in result
    assert "(尺寸单位缺失)" in result  # 原来是 (may be incomplete)
```

同时添加新测试：

```python
def test_ends_with_number_star(self):
    result = fix_truncated_spec("Dimension: 1360*")
    assert "(尺寸单位缺失)" in result  # 数字+* 用特定标记

def test_long_text_truncated_last_word(self):
    result = fix_truncated_spec(
        "350W Electric Motor of 14\" Iron Wheel,48V21A Lithium Iron Batteries & 48V2A Charger, Brushless BMS,14*130*275 Silver Front fork, Iron wheel rim, 14-250 Tubeless Tires, Front disc"
    )
    assert "(may be incomplete)" in result

def test_safe_short_word_no_mark(self):
    text = "This is a box of 10 pcs per set with standard packing material"
    assert not fix_truncated_spec(text).endswith("(may be incomplete)")

def test_normalize_spec_exists(self):
    from src.parsers.spec_cleaner import normalize_spec
    assert callable(normalize_spec)
    result = normalize_spec("")
    assert "Standard configuration" in result
```

- [ ] **Step 4: 运行测试验证规格清洗**

Run: `python -m pytest tests/test_spec_cleaner.py -v`

Expected: All 18+ tests PASS (existing + new). 
If pytest not installed: `pip install pytest`

- [ ] **Step 5: 提交**

```bash
git add src/parsers/spec_cleaner.py tests/test_spec_cleaner.py
git commit -m "feat: enhance spec truncation detection and add normalize_spec entry"
```

---

### Task 2: quotation_excel.py — 公司信息区块 + 列布局 (Model/Name去重 + Total列)

**Files:**
- Modify: `src/output/quotation_excel.py:48-68,73-80,164-174,224-238,249-258,260-371,373-400,429-467`

- [ ] **Step 1: QuotationExcel 接受 company_info 参数**

```python
def __init__(
    self,
    supplier: str = '',
    quotation_no: str = '',
    valid_days: int = 30,
    trade_terms: str = 'FOB Qingdao',
    payment_terms: str = 'T/T 30% deposit + 70% before shipment',
    currency: str = 'CNY',
    lang: str = 'chinese',
    company_info: dict = None,  # 新增
):
    ...
    self.company_info = company_info or {}
```

- [ ] **Step 2: 修改 `_format_model_name()` — 智能去重**

```python
@staticmethod
def _format_model_name(model: str, name: str) -> str:
    model = str(model).strip() if model else ''
    name = str(name).strip() if name else ''
    if not model and not name:
        return ''
    if not name or name.lower() in ('nan', 'none', ''):
        return model
    # 去重：去除前后空格后比较
    if model == name:
        return model
    return f"{model}\n{name}"
```

- [ ] **Step 3: `add_products()` 新增 total 字段 + 调用 clean_spec**

在 `add_products()` 方法的 `result.append(...)` 中新增 `'总价'` 字段。

找到 `result.append({...})` 块，在 `'单价': unit_price,` 之后添加：

```python
'总价': unit_price * qty if unit_price and qty else 0,
```

同时，在 spec 处理逻辑中（处理 `spec_raw` 的部分），调用 `clean_spec()`：

在文件顶部添加 import：
```python
try:
    from src.parsers.spec_cleaner import clean_spec
except ImportError:
    def clean_spec(x): return x or ''
```

修改 spec 处理部分：
```python
# 原：
spec = str(spec_raw).strip()
# 改为：
spec = clean_spec(spec_raw)
```

注意：keep the existing translation logic after clean_spec — clean first, then translate.

- [ ] **Step 4: `write()` 方法 — 在标题下方插入公司信息区块**

找到 Row 1 标题写入后的位置，在信息行（Quotation No./Date/Supplier/Valid Until）之前插入：

```python
# ----- 公司信息区块 (Row 2-3) -----
company = self.company_info or {}
company_name = company.get('name_en', '') or company.get('name', '') or self.supplier
company_addr = company.get('address', '')
company_tel = company.get('tel', '')
company_email = company.get('email', '')

if company_name:
    ws.merge_cells(f'A{row}:G{row}')
    cell = ws[f'A{row}']
    cell.value = company_name
    cell.font = Font(name='Arial', size=11, bold=True, color='1a5fb4')
    cell.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[row].height = 22
    row += 1

if company_addr or company_tel or company_email:
    ws.merge_cells(f'A{row}:G{row}')
    parts = []
    if company_addr:
        parts.append(company_addr)
    if company_tel or company_email:
        contact = []
        if company_tel:
            contact.append(f"Tel: {company_tel}")
        if company_email:
            contact.append(f"Email: {company_email}")
        parts.append(' | '.join(contact))
    cell = ws[f'A{row}']
    cell.value = ' | '.join(parts)
    cell.font = Font(name='Arial', size=9, color='555555')
    cell.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[row].height = 18
    row += 1

# 信息行 (原 Row 2，现下移)
info_labels = ...
# ... rest stays the same but row is now at the right position
```

- [ ] **Step 5: 修改表头为 7 列 + Total 列**

找到 headers 定义（line ~250）：
```python
headers = ['No.', 'Photo', 'Model / Product Name', 'Specifications', 'Qty', 'Unit Price', 'Total']
```

- [ ] **Step 6: 数据行写入 Total 列**

在数据行循环中，找到 `row_data` 数组，在第 6 个元素（Unit Price）后面添加：

```python
row_data = [
    record.get('序号', idx + 1),
    '',  # Photo
    record.get('型号', ''),
    record.get('规格参数', ''),
    record.get('数量', ''),
    record.get('单价', 0),
    record.get('总价', 0),
]
```

在列写入逻辑中添加 col_idx == 7 的 Total 处理。在 col_idx == 6 的价格处理代码后（~line 358-364）添加：

```python
elif col_idx == 6:  # 单价
    ...
elif col_idx == 7:  # Total
    if value and value > 0:
        cell.value = value  # 写入计算值
    else:
        cell.value = 0
    cell.alignment = DATA_ALIGN_RIGHT
    cell.font = PRICE_FONT
    # 可选写入公式: =F{row}*E{row}
    # cell.value = f'=F{row}*E{row}'
```

- [ ] **Step 7: 更新汇总行（7 列）**

修改 Total 行，将 `ws.merge_cells(f'A{row}:E{row}')` 改为合并到 G：
```python
ws.merge_cells(f'A{row}:F{row}')
cell = ws.cell(row, 1)
cell.value = 'TOTAL:'
...
cell = ws.cell(row, 7)  # G 列
total_disp = sum(r.get('总价', 0) for r in df.to_dict('records'))
...
```

- [ ] **Step 8: 更新列宽自适应逻辑（7 列）**

```python
widths = [6, 12, 25, 45, 8, 12, 15]  # No., Photo, Model/Name, Specs, Qty, Price, Total
```

更新 column width 计算循环，添加第 7 列宽度。

更新 terms 行的 merge_cells：
```python
ws.merge_cells(f'A{row}:G{row}')  # 原来是 A-F
```

- [ ] **Step 9: 更新 `create_quotation_from_library()` — 传递 company_info**

找到创建 `QuotationExcel` 的位置（~line 748-755），添加 `company_info=company_config`：

```python
qt = QuotationExcel(
    supplier=supplier,
    trade_terms=trade_terms,
    payment_terms=payment_terms,
    currency=currency,
    lang=lang,
    company_info=company_config,  # 新增
)
```

- [ ] **Step 10: 运行集成测试验证输出**

Run: `python tests/test_final_quote.py`

Expected: 生成 output/ 目录下的 xlsx 文件，无报错。
手动打开 xlsx 检查：
- 公司信息显示在标题下方
- Model/Name 智能去重
- Total 列有值
- 底部汇总 Total

- [ ] **Step 11: 提交**

```bash
git add src/output/quotation_excel.py
git commit -m "feat: add company info block, smart model/name dedup, Total column"
```

---

### Task 3: quotation_excel.py — 图片嵌入 + 路径解析修复

**Files:**
- Modify: `src/output/quotation_excel.py:206,311-330,530-739`

- [ ] **Step 1: 移除 20 产品图片上限**

在 `write()` 方法中找到：
```python
embed_images = with_images and len(data) <= 20
```
改为：
```python
embed_images = with_images
if with_images and len(data) > 50:
    print(f"Warning: Embedding {len(data)} images. The Excel file may be large (~{len(data)*200}KB).")
```

- [ ] **Step 2: 修复 `create_quotation_from_library()` 图片路径解析**

找到图片解析逻辑（~line 701-728），替换为：

```python
resolved_img = stored_img

if stored_img:
    if os.path.isfile(stored_img):
        resolved_img = stored_img
    elif not os.path.isabs(stored_img):
        candidate = os.path.join(BASE_DIR, stored_img)
        if os.path.isfile(candidate):
            resolved_img = candidate
        else:
            # 尝试 data/ 下的相对路径
            candidate2 = os.path.join(BASE_DIR, 'data', stored_img)
            if os.path.isfile(candidate2):
                resolved_img = candidate2
            else:
                import logging
                logging.warning(f"Image not found for {product.sku}: {stored_img}")
                resolved_img = ''
else:
    resolved_img = ''
```

在函数开头确保有 `BASE_DIR`：
```python
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
```

同时，移除 `create_quotation_from_library()` 中 `image_search_dirs` 相关的全局 glob 搜索代码（~line 614-621），因为不再需要。

- [ ] **Step 3: 运行集成测试验证图片嵌入**

Run: `python tests/test_final_quote.py --with-images`

- [ ] **Step 4: 提交**

```bash
git add src/output/quotation_excel.py
git commit -m "feat: remove image count limit, fix image path resolution"
```

---

### Task 4: XSL-DF17 / XSL-JY86 源文件调查

**Files:**
- Investigate: `data/新能源电动车/quotation.pdf`
- Investigate: `data/新能源电动车/e-motorcycle.pdf`
- Maybe fix: `src/core/pdf_parser.py`

- [ ] **Step 1: 检查源 PDF 查找 XSL 产品规格**

Run: `python -c "
import sys; sys.path.insert(0, 'src')
from core.pdf_parser import extract_products_from_pdf_v2
df = extract_products_from_pdf_v2('data/新能源电动车/quotation.pdf')
if df is not None:
    for _, r in df.iterrows():
        m = str(r.get('model','')).strip()
        if 'XSL' in m.upper():
            print(f'{m}: spec={str(r.get(\"spec_zh\",\"\"))[:200]}')
" 2>&1`

- [ ] **Step 2: 如果源文件有完整规格，修复 pdf_parser.py 跨页拼接**

检查 `extract_tables_from_pdf()` 函数在 `pdf_parser.py` 中。如果 PDF 中表格被分页截断（一页表尾、下页表头），需要：

在 `extract_products_from_pdf_v2()` 中对多页表格进行拼接：
```python
# 在提取后拼接跨页文本
if layout == 'row_based' and len(tables) > 1:
    # 合并连续页面的表格行（跳过重复表头）
    merged_rows = []
    for table in tables:
        for row in table:
            row_str = ' '.join(str(c or '') for c in row).lower()
            if any(kw in row_str for kw in ['model', '型号', 'product']):
                continue  # 跳过表头
            merged_rows.append(row)
```

- [ ] **Step 3: 重新导入修复后的数据**

如果源文件有完整规格但解析截断，修复后重新导入：
```bash
python run.py --input data/新能源电动车/quotation.pdf --save-to-db --user-id ev_alls
```

- [ ] **Step 4: 提交**

```bash
git add src/core/pdf_parser.py
git commit -m "fix: handle cross-page PDF table truncation for XSL products"
```

---

### Task 5: 端到端验证

**Files:**
- Run: End-to-end quotation generation test

- [ ] **Step 1: 生成完整报价单验证所有功能**

```bash
python product_cli.py --sku XSL-DF17,XSL-JY86,XF-1,BOX,M6 --quantity 2,3,5,1,2 --quote output/e2e_test.xlsx --lang bilingual --with-images
```

- [ ] **Step 2: 验证输出**

手动/脚本检查：
```python
# verify_quote.py
import openpyxl
wb = openpyxl.load_workbook('output/e2e_test.xlsx')
ws = wb['Quotation']
print("Title:", ws['A1'].value)
print("Company:", ws['A2'].value)  # 公司名称
print("Headers:", [ws.cell(4, c).value for c in range(1, 8)])  # 7 列表头
print("Row 6 Model/Name:", ws.cell(6, 3).value)  # 去重
print("Row 6 Total:", ws.cell(6, 7).value)  # Total
# 检查最后几行
for r in range(ws.max_row - 5, ws.max_row + 1):
    vals = [ws.cell(r, c).value for c in range(1, 8)]
    if any(v for v in vals):
        print(f"Row {r}: {vals}")
wb.close()
```

Expected:
- Row 1: FOREIGN TRADE QUOTATION
- Row 2: SONLINK E-MOTORCYCLE CO., LTD
- Row 4: Quotation No., Date, Supplier, Valid Until
- Row 5: No. | Photo | Model / Product Name | Specifications | Qty | Unit Price | Total
- Data rows: model/name 去重逻辑正确
- Total 列: Qty * Unit Price 值正确
- 底部汇总: TOTAL + 求和值

- [ ] **Step 3: 提交最终验证文件（可选）**

```bash
git add output/e2e_test.xlsx
git commit -m "test: e2e quotation verification"
```
