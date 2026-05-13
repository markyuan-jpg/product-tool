# PDF产品解析器V2 - 设计与实现

## 目标
自动检测PDF表格的行列布局，智能关联图片到产品，实现全自动解析。

## 当前问题

| 问题 | 原因 |
|-----|------|
| e-motorcycle.pdf: 25行→1产品 | 行式布局，每行是spec |
| quotation.pdf: 20行→3产品 | 列式布局，每列是产品 |
| 图片未自动关联 | 需要手动指定_image_path |

## 设计方案

### 1. 布局自动检测

```python
def detect_layout(tables: List) -> dict:
    """检测表格布局类型"""
    # 行式: Model在第一列 → 每行是产品
    # 列式: Model在第一行 → 每列是产品
```

### 2. 产品解析V2

```python
def extract_products_from_pdf_v2(pdf_path: str) -> pd.DataFrame:
    """V2: 自动检测布局 + 图片关联"""
    # Step 1: 提取表格
    # Step 2: 检测布局类型
    # Step 3: 解析为标准产品DataFrame
    # Step 4: 提取图片
    # Step 5: 自动关联图片
    # 返回: 含_image_path列的DataFrame
```

### 3. 图片关联逻辑

```
IF 图片名包含产品型号 (如 S500.jpg):
    → 精确匹配
    
ELIF 产品数 == 1:
    → 所有图片给这1个产品
    
ELIF 图片数 >= 产品数:
    → 循环分配 (round-robin)
    
ELIF 图片数 < 产品数:
    → 轮流分配
```

## 输出格式

```python
# DataFrame columns:
['model', 'name_zh', 'spec_zh', 'price_rmb', '_image_path', '_source_file']
```

## 兼容性

- 保留现有 `extract_products_from_pdf()` 函数
- 新函数名: `extract_products_from_pdf_v2()`

## 实现步骤

1. 添加布局检测函数
2. 添加产品解析V2函数  
3. 添加图片自动关联函数
4. 测试验证