# 外贸报价单改进设计文档

> Date: 2026-05-04
> Project: Production Tool — 报价单生成器改进
> Status: Approved

---

## 目标

修复外贸报价单（Excel）生成中的 6 类问题：图片空白、规格空缺与截断、缺少 Total 列、公司信息不完整、型号与名称重复、规格格式不统一。

---

## 1. 列布局 — 混合模式

### 表头（7 列）

```
No. | Photo | Model / Product Name | Specifications | Qty | Unit Price | Total
```

### Model / Product Name 列

修改 `quotation_excel.py` 中的 `_format_model_name()` 和 `write()` 方法：

```
逻辑：
  去除前后空格，比较 model 与 name_zh
  if model == name_zh:
      显示 model（不重复）
  else:
      显示 "model\nname_zh"（换行）
```

### Total 列

- 新增 G 列表头 "Total"
- 每行写入 `price * qty` 的计算值
- 可选写入 Excel 公式 `=F{row}*E{row}` 以便用户修改后自动更新
- 底部汇总行：对 Total 列 `SUM`，显示在最后一行（单独占一行）
- 汇总行样式：`SUBHEADER_FILL`（浅蓝底） + 粗体

### 底部汇总行

```
A{row}: "TOTAL:" (右对齐)
G{row}: SUM(Total) 的值 (右对齐，货币格式)
```

---

## 2. 公司完整信息

### 数据来源

`company.py` → `load_company()` 返回的 dict。当前 `company.json` 已有：

```json
{
  "name": "SONLINK E-MOTORCYCLE CO., LTD",
  "name_en": "SONLINK E-MOTORCYCLE CO., LTD",
  "address": "NO.576 Fengyi Road, Fengxian, Jiangsu, China",
  "tel": "+86-13926156666",
  "email": "gwlong926@163.com",
  "bank": { ... }
}
```

### 显示位置

报价单标题（Row 1）下方、信息行上方。插入 Row 2-3，后续行下移。

### 布局

```
Row 1: FOREIGN TRADE QUOTATION 外贸报价单  [标题，不变]
Row 2: SONLINK E-MOTORCYCLE CO., LTD       [新增，合并 A-G，左对齐，Font 11, Bold]
Row 3: NO.576 Fengyi Road, Fengxian, Jiangsu, China  [新增，合并 A-G，左对齐, Font 9]
       Tel: +86-13926156666  |  Email: gwlong926@163.com
Row 4: Quotation No. / Date / Supplier / Valid Until  [信息行，原 Row 2 下移]
Row 5: No. | Photo | ...  [表头行，原 Row 3 下移]
Row 6+: 数据行 [原 Row 4+ 下移]
```

行内容可根据实际情况合并为两行或四行（如有 bank 信息）。

### 错误处理

- 缺失字段：留空，不崩溃
- 全部缺失：跳过公司信息行，表格从正常位置开始
- `load_company()` 返回空 dict 时，使用 `get_default_config()` 的默认值（留空字符串）

---

## 3. 图片嵌入

### 当前问题

- `write()` 中硬编码 `embed_images = with_images and len(data) <= 20`
- `create_quotation_from_library()` 虽然支持 `with_images` 参数但未在 CLI `generate_quotation()` 中默认传递
- 图片路径依赖 glob 全局搜索，性能差
- DB 中只有 66/142 产品有 `image_path`

### 修改策略

| 模式 | 上限 | 行为 |
|------|------|------|
| CLI 本地 (`--with-images`) | 无限制 | 直接嵌入全部，打印 "嵌入 N 张图片，文件体积可能较大" 警告 |
| Streamlit Web (规划中) | 20 | 同现有逻辑，提供 "导出全部图片" 选项 |

### 路径解析修复

`create_quotation_from_library()` 中的图片路径解析逻辑：

```
1. 读取 product.image_path
2. 如果路径存在且为绝对路径 → 直接使用
3. 如果路径为相对路径 → 基于项目根目录解析 (BASE_DIR)
4. 如果路径存在 → 嵌入图片
5. 如果路径不存在 → logger.warning(f"Image not found: {path}")，跳过
6. 不再使用 glob 全局搜索
```

### 性能考量

- 大量图片嵌入时 Excel 文件体积会显著增大
- 建议保留 `--no-images` 选项绕过图片嵌入
- 50+ 图片的报价单建议用户在生成前确认

---

## 4. 规格参数改进

### 增强 `spec_cleaner.py`

`clean_spec()` 已实现步骤：标点统一 → 空填充 → 换行注入 → 截断检测。

**增强 `fix_truncated_spec()`**：在现有 TRUNCATION_PATTERNS 基础上新增：

```python
TRUNCATION_PATTERNS = [
    r'\*\s*$',       # 以 * 结尾（已有）
    r'-\s+$',        # 以 - + 空格结尾（已有）
    r'[:：]\s*$',    # 以 : 结尾（已有）
    r',\s*$',        # 以 , 结尾（已有）
    r'\d+\*\s*$',    # 新增：数字 + * 结尾，如 "1360*"
    r'\w{1,3}$',     # 新增：末尾只有 1-3 个字母（如 "Front d"、"Front disc" → 截断）
]
```

注意：`\w{1,3}$` 可能在正常短文本上误触发。因此限制条件：
- 文本长度 > 60（只有长文本才可能被截断）
- 末尾单词不是已知完整单词（`the`, `and`, `for`, `box`, `set`, `pcs`, `pc`, `kg`, `mm`, `cm` 等常见短单位/冠词）
- 末尾单词前必须是空格或换行（即确实是最后一个词）

### 在 `quotation_excel.py` 中调用

`add_products()` 中对每条记录的 `spec_zh` 字段调用 `clean_spec()`：

```python
from src.parsers.spec_cleaner import clean_spec
...
spec = clean_spec(spec_raw)
```

### 截断标记文本

- `1360*` → 追加 `(尺寸单位缺失)`
- `Front d` → 追加 `(may be incomplete)`
- 空规格 → 填充 `Standard configuration. Contact us for details.`

### XSL-DF17 / XSL-JY86 规格修复

DB 中这两款规格以 `"Front d"` / `"Front disc "` 结尾，明确截断。

行动计划：
1. 检查源文件 `quotation.pdf` 中对应表格是否包含完整文本
2. 确认 `pdf_parser.py` 的跨页文本拼接是否存在问题
3. 修正解析器后重新导入数据
4. 如源文件本身截断，则在 `spec_cleaner.py` 层面标记

---

## 5. 规范化入口

在 `spec_cleaner.py` 中提供统一入口函数：

```python
def normalize_spec(text: Optional[str]) -> str:
    """统一规格文本处理入口：清洗 + 格式化 + 截断检测"""
    text = clean_spec(text)      # 标点、空填充、换行、截断
    return text
```

在 `spec_formatter.py` 中：

```python
def format_and_normalize(spec_raw: str) -> str:
    """格式化为键值对 + 标准化"""
    formatted = format_spec_spec(spec_raw)
    return clean_spec(formatted)
```

---

## 6. 受影响文件汇总

| 文件 | 改动 | 预估行 | 优先级 |
|------|------|--------|--------|
| `src/output/quotation_excel.py` | 公司信息区块、Total 列、Model/Name 去重、图片限制、call clean_spec | ~150 行 | P0 |
| `src/parsers/spec_cleaner.py` | 增强 `fix_truncated_spec()`、新增 `normalize_spec()` | ~30 行 | P0 |
| `src/core/pdf_parser.py` | 可能修复跨页截断（需先确认源文件） | TBD | P1 |

---

## 7. 不变的部分

- `company.py`：不需要改动，`load_company()` 已返回完整 dict
- `spec_formatter.py`：不需要改动核心逻辑，只增加入口函数
- `product_cli.py`：参数接口不变，内部传递 `with_images` 逻辑不变
- `terms.py`：不受影响
- `product_manage/`：不受影响

---

## 8. 边界条件与错误处理

| 场景 | 行为 |
|------|------|
| 公司信息全部缺失 | 跳过公司区块，表格正常生成 |
| 部分字段缺失 | 留空，不崩溃 |
| 图片路径不存在 | `logger.warning` + 跳过，继续生成 |
| 所有规格为空 | 全部填充 "Standard configuration" |
| price=0 | Total=0，汇总行正常求和 |
| 0 个产品 | 创建空白 workbook + 保存，不报错 |
| 超长规格文本 (2000+ 字符) | 截断 + `...`，保留关键参数 |

---

## 9. 验证标准

1. 生成报价单，检查 7 列表头是否正确
2. model 与 name_zh 相同时只显示一次
3. model 与 name_zh 不同时显示 `model\nname_zh`
4. 公司信息（名称、地址、电话、邮箱）正常显示
5. Total 列有值，公式计算正确
6. 底部汇总行 Total 正确
7. `--with-images` 生成带图片的报价单，无上限
8. 图片路径不存在时跳过（不崩溃）
9. 空规格自动填充默认文本
10. 截断规格标记 `(may be incomplete)` 或 `(尺寸单位缺失)`
