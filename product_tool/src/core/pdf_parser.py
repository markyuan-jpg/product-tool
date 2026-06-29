# -*- coding: utf-8 -*-
"""
PDF表格解析
依赖: pip install pdfplumber pymupdf
"""
import os
import re
import math
import logging
import json
from typing import List, Dict, Optional
import pandas as pd

# Docling: optional advanced PDF parser
_USE_DOCLING = os.environ.get('USE_DOCLING', '0') == '1'
_HAS_DOCLING = False
if _USE_DOCLING:
    try:
        from docling.document_converter import DocumentConverter
        _HAS_DOCLING = True
    except ImportError:
        logging.getLogger(__name__).info("Docling not installed. Install with: pip install docling")

try:
    from src.parsers.spec_formatter import format_spec_spec
except ImportError:
    def format_spec_spec(x):
        return x

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def is_likely_scanned_pdf(pdf_path: str) -> bool:
    """快速检测PDF是否为扫描件（图片型，无可提取文字）。
    
    提取所有页面的文字，如果总字符数 < 50 则判定为扫描件。
    """
    if not PDFPLUMBER_AVAILABLE or not os.path.exists(pdf_path):
        return False
    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_text = sum(len(page.extract_text() or '') for page in pdf.pages)
        return total_text < 50
    except Exception:
        return False


def extract_images_from_pdf(pdf_path: str, output_dir: str = None) -> List[Dict]:
    """从PDF提取图片
    
    Returns:
        List of dicts: [{'page': int, 'index': int, 'image_path': str, 'y_center': float}, ...]
        y_center 是图片在页面中的垂直中心坐标（用于按位置匹配产品行）。
    """
    if not PYMUPDF_AVAILABLE:
        logger.warning("PyMuPDF not installed: pip install pymupdf")
        return []
    
    if not os.path.exists(pdf_path):
        return []
    
    # Create output directory
    if output_dir is None:
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        output_dir = os.path.join(os.path.dirname(pdf_path), 'images', pdf_name)
    
    os.makedirs(output_dir, exist_ok=True)
    
    images = []
    doc = fitz.open(pdf_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        img_list = page.get_images(full=True)
        
        for img_index, img in enumerate(img_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                ext = base_image["ext"]
                
                img_name = f"page{page_num + 1}_img{img_index + 1}.{ext}"
                img_path = os.path.join(output_dir, img_name)
                
                with open(img_path, "wb") as f:
                    f.write(image_bytes)
                
                # 获取图片在页面上的垂直位置
                y_center = 0
                try:
                    rects = page.get_image_rects(xref)
                    if rects:
                        y_center = (rects[0].y0 + rects[0].y1) / 2
                except Exception:
                    pass
                
                images.append({
                    'page': page_num + 1,
                    'index': img_index,
                    'image_path': img_path,
                    'y_center': y_center,
                })
                logger.info(f"Extracted: {img_path}")
            except Exception as e:
                logger.error(f"Image extraction error: {e}")
                continue
    
    doc.close()
    return images


def _fill_pdf_merged(table):
    """填充PDF表格中的合并单元格（None → 同一列最近非空值，跳过首行防表头泄漏）。"""
    if not table:
        return table
    result = [list(row) for row in table]  # 深拷贝
    for c in range(len(result[0]) if result else 0):
        last_val = None
        for r in range(len(result)):
            if c < len(result[r]):
                if r == 0:
                    # 首行（表头）不传播，只记录值
                    if result[r][c] is not None and str(result[r][c]).strip():
                        last_val = str(result[r][c]).strip()
                elif result[r][c] is None or str(result[r][c]).strip() == '':
                    result[r][c] = last_val
                else:
                    last_val = str(result[r][c]).strip()
    return result


def extract_tables_from_pdf(pdf_path: str, return_positions: bool = False) -> List:
    """从PDF提取所有表格
    
    Args:
        pdf_path: PDF 文件路径
        return_positions: 是否返回位置信息（页面号、行Y坐标）
    
    Returns:
        如果 return_positions=False（默认）:
            List[List[List[str]]] — 旧格式：每个表格是行的列表
        如果 return_positions=True:
            List[Dict] — 每个表格含 page, rows, row_bboxes
            [{'page': int, 'rows': List[List[str]], 'row_bboxes': List[tuple]}, ...]
    """
    import pdfplumber.table as _pt
    
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber not installed: pip install pdfplumber")
    
    if not os.path.exists(pdf_path):
        return [] if not return_positions else []
    
    all_tables = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Use find_tables to get bbox info, extract for text
            raw_tables = page.find_tables()
            for tbl in raw_tables:
                rows_text = tbl.extract()
                if not rows_text or not any(any(c for c in r) for r in rows_text):
                    continue
                rows_text = _fill_pdf_merged(rows_text)
                
                if return_positions:
                    # Get each row's bbox
                    row_bboxes = []
                    # tbl.rows gives CellGroups; each CellGroup has cells with bboxes
                    # Note: Some cells may be None (empty/merged), so filter them
                    for row_group in tbl.rows:
                        valid_cells = [c for c in row_group.cells if c is not None]
                        if valid_cells:
                            rx0 = min(c[0] for c in valid_cells)
                            ry0 = min(c[1] for c in valid_cells)
                            rx1 = max(c[2] for c in valid_cells)
                            ry1 = max(c[3] for c in valid_cells)
                            row_bboxes.append((rx0, ry0, rx1, ry1))
                        else:
                            # No valid cells - use previous row's bbox or zero
                            row_bboxes.append((0, 0, 0, 0))
                    
                    all_tables.append({
                        'page': page.page_number,
                        'rows': rows_text,
                        'row_bboxes': row_bboxes,
                    })
                else:
                    all_tables.append(rows_text)
    
    return all_tables


def extract_products_from_pdf(pdf_path: str, keyword_cols: List[str] = None) -> Optional[pd.DataFrame]:
    """从PDF提取产品数据（含图片）"""
    # Extract images first
    images = extract_images_from_pdf(pdf_path)
    
    tables = extract_tables_from_pdf(pdf_path)
    
    if not tables:
        return None
    
    if keyword_cols is None:
        keyword_cols = ['型号', 'Model', '型号', 'name', 'Name', 
                      '价格', 'Price', 'price', '单价']
    
    # 找到表头行
    header_row = None
    target_table = None
    
    for table in tables:
        for row in table:
            row_str = ' '.join(str(cell or '') for cell in row)
            if any(kw in row_str for kw in keyword_cols):
                header_row = row
                target_table = table
                break
        if header_row:
            break
    
    if not target_table:
        # 使用第一张表
        target_table = tables[0]
        header_row = target_table[0] if target_table else None
    
    if not header_row:
        return None
    
    # 构建DataFrame
    data = []
    for row in target_table[1:]:
        if not any(row):
            continue
        item = {}
        for i, header in enumerate(header_row):
            if i < len(row):
                item[str(header or f'col_{i}')] = row[i]
        if item:
            data.append(item)
    
    df = pd.DataFrame(data) if data else None
    
    # Normalize columns - add standard columns
    if df is not None and len(df) > 0:
        df = normalize_pdf_columns(df)
    
    return df


def normalize_pdf_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize PDF columns to standard model/price format"""
    # Column mapping patterns
    model_patterns = ['Model', '型号', '产品', 'goods', 'Item', 'name', 'Name']
    price_patterns = ['Price', '价格', '单价', 'RMB', 'CNY', 'price', 'Unit Price']
    
    # Find model column
    model_col = None
    for col in df.columns:
        col_str = str(col).strip()
        for p in model_patterns:
            if p.lower() in col_str.lower():
                model_col = col
                break
        if model_col:
            break
    
    # Find price column
    price_col = None
    for col in df.columns:
        col_str = str(col).strip()
        for p in price_patterns:
            if p.lower() in col_str.lower():
                price_col = col
                break
        if price_col:
            break
    
    # Create normalized columns
    result = pd.DataFrame()
    
    if model_col:
        result['model'] = df[model_col]
    else:
        # Use first non-empty column
        for col in df.columns:
            if col in df.columns:
                result['model'] = df[col]
                break
    
    if price_col:
        # Try to convert price to numeric
        result['price_rmb'] = pd.to_numeric(df[price_col].astype(str).str.replace(',', '').str.replace('¥', '').str.strip(), errors='coerce')
    else:
        result['price_rmb'] = None
    
    # Add remaining columns as specs
    for col in df.columns:
        if col != model_col and col != price_col:
            result[f'spec_{col}'] = df[col]
    
    # Filter out empty model rows
    result = result[result['model'].notna() & (result['model'] != '') & (result['model'].str.strip() != '')]
    
    return result


def pdf_to_csv(pdf_path: str, output_path: str = None) -> str:
    """PDF转CSV"""
    if output_path is None:
        output_path = pdf_path.replace('.pdf', '.csv')
    
    df = extract_products_from_pdf(pdf_path)
    if df is not None:
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        return output_path
    
    return ''


def extract_text_from_pdf(pdf_path: str) -> str:
    """从PDF提取纯文本"""
    if not PDFPLUMBER_AVAILABLE:
        return ''
    
    if not os.path.exists(pdf_path):
        return ''
    
    text = ''
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + '\n'
    
    return text


if __name__ == '__main__':
    print('PDF Parser')
    print('Usage: from src.core.pdf_parser import pdf_to_csv')


# 跳过列关键词
SKIP_PDF_COLUMN_KEYWORDS = {'serial', 'no.', 'no', '序号', '序號', 'image', 'picture',
                             'photo', '图片', '圖片', '照片', '附图', '附圖'}
# 包装关键词（用于无表头列的内容推断）
PACKAGING_CONTENT_KEYWORDS = ['pcs/', 'pcs/pack', 'pcs/box', 'pack', 'pieces',
                               '个/箱', '个/包', '只/箱', '装箱']


def _classify_pdf_columns(table) -> dict:
    """从PDF表格数据内容分类每列角色（不依赖表头）
    
    角色: 'skip', 'sequence', 'label', 'price', 'model', 'spec', 'packaging'
    """
    if not table or len(table) < 2:
        return {}
    
    # 包装关键词
    PACKAGING_KEYWORDS = {
        'gw', 'nw', 'g.w.', 'n.w.', 'gross weight', 'net weight',
        'gross', 'net', 'carton size', 'carton', 'package size',
        'packing size', 'packing', 'cbm', 'meas', 'measurement',
        'dimension', 'dimensions', 'qty/ctn', 'pcs/ctn', 'qty per carton',
        '毛重', '净重', '外箱尺寸', '包装尺寸', '每箱数量', '装箱',
        '体积', '包装', 'cartons', 'ctns', 'units per carton',
        'n.w', 'g.w'
    }
    
    # 获取第一行（表头）判断跳过列
    header_row = [str(c or '').strip().lower() for c in table[0]] if table else []
    
    roles = {}
    for c in range(len(table[0])):
        texts = []
        label_count = 0
        model_count = 0
        price_count = 0
        packaging_count = 0
        seq_count = 0
        all_ints = True
        
        # 检查表头是否命中跳过关键词
        if c < len(header_row) and header_row[c]:
            h = header_row[c]
            if any(kw in h for kw in SKIP_PDF_COLUMN_KEYWORDS):
                roles[c] = 'skip'
                continue
        
        for r in range(1, min(len(table), 60)):
            v = str(table[r][c] or '').strip()
            if not v:
                continue
            texts.append(v)
            v_lower = v.lower()
            
            # 序列号检测（纯数字 1-999）
            if v.isdigit() and 1 <= int(v) <= 999:
                seq_count += 1
            elif v and not v.isdigit():
                all_ints = False  # 非数字 → 不是纯序号列
            
            # 标签检测
            if v_lower in {'image', 'picture', 'photo', 'description', 'name',
                           '规格', '参数', '颜色', '材料', '备注'}:
                label_count += 1
            # 包装关键词检测
            if v_lower in PACKAGING_KEYWORDS or any(kw in v_lower for kw in PACKAGING_KEYWORDS):
                packaging_count += 1
            # 内容级包装检测（无表头时靠内容推断）
            if any(kw in v_lower for kw in PACKAGING_CONTENT_KEYWORDS):
                packaging_count += 1
            if re.search(r'[A-Za-z]+\d+', v):
                model_count += 1
            # 价格检测（放宽小数阈值）
            cleaned = re.sub(r'[¥$€£USDusd,\s]', '', v)
            try:
                f = float(cleaned)
                if 0.001 < f < 10000000:
                    price_count += 1
            except Exception:
                pass
        
        if not texts:
            roles[c] = 'skip'
        elif packaging_count >= max(1, len(texts) * 0.15):
            roles[c] = 'packaging'
        elif seq_count >= max(3, len(texts) * 0.8) and all_ints:
            roles[c] = 'skip'  # 纯序号列
        elif label_count >= max(2, len(texts) * 0.3):
            roles[c] = 'label'
        elif price_count >= max(2, len(texts) * 0.2):
            roles[c] = 'price'
        elif model_count >= max(2, len(texts) * 0.15):
            roles[c] = 'model'
        else:
            avg_len = sum(len(t) for t in texts) / len(texts)
            roles[c] = 'model' if avg_len < 25 else 'spec'
    
    logger.info(f"[DEBUG] Column roles: {roles}")
    return roles


def _parse_pdf_by_content(table) -> 'pd.DataFrame':
    """内容驱动的PDF兜底解析：无视表头和数据布局，根据每列内容推断角色后提取
    
    修复：现在正确提取 spec 和 packaging 列并格式化为 spec_zh
    """
    roles = _classify_pdf_columns(table)
    
    model_col = None
    price_col = None
    spec_cols = []
    packaging_fields = {}
    for c, role in sorted(roles.items()):
        if role == 'model' and model_col is None:
            model_col = c
        elif role == 'price' and price_col is None:
            price_col = c
        elif role == 'spec':
            spec_cols.append(c)
        elif role == 'packaging':
            # 记录包装列的列名（从第一行取）
            col_name = str(table[0][c] or f'pack_{c}').strip() if len(table) > 0 else f'pack_{c}'
            packaging_fields[c] = col_name
    
    if model_col is None:
        return pd.DataFrame()
    
    # 从表头行获取 spec 列名
    header_row = table[0] if len(table) > 0 else []
    
    products = []
    for r in range(1, len(table)):
        model = str(table[r][model_col] or '').strip()
        if not model:
            continue
        
        price = None
        if price_col is not None and price_col < len(table[r]):
            val = str(table[r][price_col] or '').strip()
            nums = re.findall(r'[\d,]+(?:\.\d+)?', val.replace(',', ''))
            if nums:
                try:
                    price = float(nums[0])
                except Exception:
                    pass
        
        # 收集 spec 列 → spec_zh
        spec_parts = []
        for c in spec_cols:
            if c < len(table[r]):
                val = str(table[r][c] or '').strip()
                if val:
                    col_key = str(header_row[c] or f'spec_{c}').strip() if c < len(header_row) else f'spec_{c}'
                    spec_parts.append(f"{col_key}: {val}")
        
        # 收集包装列 → 加到 spec_zh
        for c, col_name in packaging_fields.items():
            if c < len(table[r]):
                val = str(table[r][c] or '').strip()
                if val:
                    spec_parts.append(f"{col_name}: {val}")
        
        spec_zh = '; '.join(spec_parts) if spec_parts else ''
        
        products.append({
            'model': model,
            'name_zh': '',
            'price_rmb': price,
            'spec_zh': spec_zh,
            '_image_path': '',
            '_source_file': '',
            '_row': r,
        })
    
    return pd.DataFrame(products)


def _has_real_products(df) -> bool:
    """检查 DataFrame 是否包含真实的产品型号（而非参数名/标签）"""
    if df is None or df.empty:
        return False
    real_count = 0
    for _, r in df.iterrows():
        m = str(r.get('model', '')).strip()
        if _is_valid_pdf_model(m):
            real_count += 1
    # 允许单个真产品（适用单产品规格表）
    return real_count >= 1

# --- Docling fallback parser ---

# USE_DOCLING/_HAS_DOCLING defined at module top (lines 15-22)


def _parse_pdf_via_docling(pdf_path):
    """Use Docling as fallback. Requires USE_DOCLING=1 env var."""
    if not _USE_DOCLING or not _HAS_DOCLING:
        return None
    logger = logging.getLogger(__name__)
    try:
        converter = DocumentConverter()
        result = converter.convert(pdf_path)
        doc = result.document
        products = []

        # Try tables first
        if doc.tables:
            for table in doc.tables:
                data = table.export_to_dict()
                rows = data.get('data', []) if isinstance(data, dict) else data
                if not rows:
                    continue
                for row in rows[1:]:
                    model = str(row[0] if len(row) > 0 else '').strip()
                    if not model or len(model) < 2:
                        continue
                    price = None
                    spec_parts = []
                    for ci, cell in enumerate(row[1:], 1):
                        val = str(cell).strip() if cell else ''
                        if ci < 4:
                            pm = re.search(r'[\d,]+(?:\.\d+)?', val)
                            if pm:
                                try:
                                    p = float(pm.group().replace(',', ''))
                                    if 0.01 < p < 1000000:
                                        price = max(price or 0, p)
                                except ValueError:
                                    pass
                        if val and ci > 1:
                            spec_parts.append(val)
                    products.append({
                        'model': model, 'name_zh': model, 'price_rmb': price,
                        'spec_zh': '; '.join(spec_parts[:20]),
                        'currency': 'CNY', '_image_path': '',
                    })

        # Fallback: text extraction
        if not products and doc.text:
            cm, cs, cp = None, [], None
            for item in doc.text.items():
                t = str(item['text']) if isinstance(item, dict) else str(item)
                t = t.strip()
                if not t:
                    continue
                if re.search(r'[A-Za-z]+\d+', t) and len(t) < 30:
                    if cm and cs:
                        products.append({'model': cm, 'name_zh': cm, 'price_rmb': cp, 'spec_zh': '\n'.join(cs[-30:]), 'currency': 'CNY', '_image_path': ''})
                    cm = t.split()[0]
                    cs = []
                    cp = None
                pm = re.search(r'(?:USD|CNY|\xa5|\$|\u4ef7\u683c|price)\s*([\d,]+(?:\.\d+)?)', t, re.I)
                if pm:
                    try:
                        cp = float(pm.group(1).replace(',', ''))
                    except Exception:
                        pass
                if ':' in t or '\uff1a' in t:
                    cs.append(t)
            if cm and cs:
                products.append({'model': cm, 'name_zh': cm, 'price_rmb': cp, 'spec_zh': '\n'.join(cs[-30:]), 'currency': 'CNY', '_image_path': ''})

        if not products:
            return None
        df = pd.DataFrame(products)
        logger.info(f"[DOCLING] Extracted {len(df)} products from {os.path.basename(pdf_path)}")
        return df
    except Exception as e:
        logger.warning(f"[DOCLING] Failed: {e}")
        return None



def _is_valid_pdf_model(m) -> bool:
    """判断字符串是否是真正产品型号（非参数名/标签）"""
    if not m:
        return False
    m = str(m).strip()
    if len(m) < 2:
        return False
    has_letter = any(c.isalpha() for c in m)
    has_digit = any(c.isdigit() for c in m)
    if not (has_letter and has_digit):
        # 纯数字或纯字母（如"Appearance"）不是产品型号
        return False
    # 排除已知参数名（包含即可，如"Model XF-1"含"Model"）
    param_keywords = {'motor', 'battery', 'weight', 'speed', 'power', 'voltage',
                      'current', 'controller', 'charger', '颜色', '规格', '参数',
                      '尺寸', '重量', '包装', 'description', 'photo', 'picture',
                      'material', 'dimension', '型号'}
    m_lower = m.lower()
    for kw in param_keywords:
        if kw in m_lower:
            return False
    # 排除过长文本（大概率是描述不是型号）
    if len(m) > 40:
        return False
    return True


def _score_pdf_result(df, source='content') -> float:
    """评分PDF解析结果（与 Excel score_result 公式一致，保留 PDF 特有策略）。"""
    if df is None or df.empty:
        return -1
    n = len(df)
    # 只计真正产品型号
    has_model = sum(1 for _, r in df.iterrows() if _is_valid_pdf_model(str(r.get('model', '')).strip()))
    has_price = sum(1 for _, r in df.iterrows() if r.get('price_rmb'))
    models_set = set(str(r.get('model', '')).strip() for _, r in df.iterrows() if r.get('model') and _is_valid_pdf_model(str(r.get('model', '')).strip()))
    diversity = len(models_set) / max(has_model, 1) if has_model > 0 else 0
    # 基础公式（与 Excel 一致）
    score = n * 0.3 + has_model * 0.3 + has_price * 0.2 + diversity * 10 * 0.2
    # 产品_ 前缀惩罚（同 Excel）
    prefix_penalty = sum(1 for _, r in df.iterrows() if str(r.get('model', '')).startswith('产品_'))
    if prefix_penalty > n * 0.5:
        score *= 0.5
    # 布局策略加成（PDF 特有：结构化布局优于自由文本提取）
    source_boost = 1.5 if (source in ('col_based', 'row_based', 'kv_spec') and _has_real_products(df)) else 1.0
    # 单产品规格表加成：col_based 找出的唯一真产品应优先于内容策略的噪音
    single_boost = 1.5 if (n == 1 and has_model == 1 and source in ('col_based', 'row_based', 'kv_spec')) else 1.0
    return score * source_boost * single_boost


def detect_table_layout(table: List[List[str]]) -> str:
    """检测表格布局类型
    
    Returns:
        'row_based': 每行是产品 (Model在第一列)
        'col_based': 每列是产品 (Model在第一行)
        'unknown'
    """
    if not table or len(table) < 2:
        return 'unknown'
    
    # Look for header row (contains Model/型号 keyword)
    header_row_idx = None
    model_keywords = ['model', '型号', '产品', 'item', 'sku', 'product', '产品名称', '编号']
    
    for idx, row in enumerate(table):
        # 逐格检查所有列（仅限短文本<40字符，避免spec误匹配）
        for c in row:
            cv = str(c or '').strip()
            if len(cv) > 40:
                continue  # 长文本不太可能是表头
            cv_lower = cv.lower()
            if any(kw in cv_lower for kw in model_keywords):
                header_row_idx = idx
                break
        if header_row_idx is not None:
            break
    
    if header_row_idx is None:
        header_row_idx = 0
    
    header_row = table[header_row_idx]
    first_col = []
    for row in table[header_row_idx:]:
        if not row or not isinstance(row, (list, tuple)):
            continue
        if len(row) == 0:
            continue
        val = row[0]
        if val is not None and val != '':
            first_col.append(val)
    
    # 同样逐格检查并限制长度（扫描所有列）
    first_row_short = [str(c or '').strip()[:40] for c in header_row]
    first_row_str = ' '.join(first_row_short).lower()
    first_col_str = ' '.join(str(c or '') for c in first_col[:5]).lower()
    
    has_model_in_first_row = any(kw in first_row_str for kw in model_keywords)
    has_model_in_first_col = any(kw in str(c).lower() for c in first_col[:5] for kw in model_keywords)
    
    if has_model_in_first_row:
        return 'col_based'
    elif has_model_in_first_col:
        # 第一列有型号关键词，但若有多列+第一列是参数名 → col_based（多产品对比表）
        non_empty_cols = sum(1 for c in header_row[1:] if str(c or '').strip())
        param_in_first = sum(1 for c in first_col[:8] if ':' in str(c) or '：' in str(c) or _is_param_name(str(c)))
        if non_empty_cols >= 2 and param_in_first >= 3:
            return 'col_based'
        return 'row_based'
    
    # 内容辅助：分析第一列是否全是标签，第一行是否全是短文本
    first_col_vals = [str(row[0] or '').strip().lower() for row in table[1:9] if row and row[0]]
    common_labels = {'image', 'description', 'name', 'picture', 'photo', 'price',
                     'model', '规格', '参数', '包装', '颜色', '材料', '备注', 'product'}
    if first_col_vals:
        label_ratio = sum(1 for v in first_col_vals if v in common_labels) / len(first_col_vals)
        if label_ratio > 0.4:
            return 'col_based'
    
    return 'row_based'


def _is_param_name(text: str) -> bool:
    """检测文本是否看起来像参数名（而非产品型号）"""
    if not text:
        return False
    t = text.strip()
    if not t:
        return False
    # 冒号结尾 → 参数名（Motor: Battery:）
    if t.endswith(':') or t.endswith('：'):
        return True
    # 已知参数关键词
    param_keywords = ['motor', 'battery', 'controller', 'speed', 'range',
                      'dimension', 'weight', 'power', 'voltage', 'current',
                      'charging', 'brake', 'tire', 'tyre', 'material', 'color',
                      'size', 'package', 'gross', 'net', 'max', 'model',
                      'ceiling', 'torque', 'efficiency', 'climb',
                      'wheelbase', 'suspension', 'hydraulic', 'front', 'rear',
                      'including', 'cycle', 'product', 'eco',
                      '电机', '电池', '控制器', '速度', '里程', '功率',
                      '电压', '电流', '充电', '刹车', '轮胎', '材质', '颜色',
                      '尺寸', '重量', '包装', '毛重', '净重', '车型', '型号',
                      '产品名称', '产品', '规格', '参数', '报价', '价格']
    t_lower = t.lower()
    # 逐词匹配（处理 "Including Battery Weight 包含电池重量" → 匹配 "including"）
    # 全角冒号（\uff1a）和ASCII冒号都要替换，PDF提取常使用全角符号
    words = t_lower.replace(':', ' ').replace('\uff1a', ' ').replace('（', '(').split()
    for w in words:
        # 去掉括号后缀
        clean_word = w.split('(')[0].split('（')[0].strip().rstrip(':：）)')
        if clean_word in param_keywords:
            return True
    # 长度检查：只有1-2个长词（>10字符）且都不在关键词中 → 非参数名
    long_words = [w for w in words if len(w) > 10 and w not in ('specification', 'specifications')]
    if len(words) <= 2 and len(long_words) == len(words):
        return False
    return False


def extract_products_from_pdf_v2(pdf_path: str) -> Optional[pd.DataFrame]:
    """从PDF提取产品数据V2 - 三层策略择优
    
    Returns:
        DataFrame with columns: model, name_zh, price_rmb, _image_path, _source_file
    """
    if not os.path.exists(pdf_path):
        return None
    
    # Get tables with position info for image matching
    tables_data = extract_tables_from_pdf(pdf_path, return_positions=True)
    if not tables_data:
        return None
    
    # Separate: old format for strategy processing, position info for image matching
    tables = [td['rows'] for td in tables_data]
    table_positions = [(td['page'], td['row_bboxes']) for td in tables_data]
    
    logger.info(f"[DEBUG] Tables found: {len(tables)}")
    for ti, table in enumerate(tables):
        logger.info(f"[DEBUG] Table {ti}: {len(table)} rows x {len(table[0]) if table else 0} cols")
        for ri, row in enumerate(table[:3]):
            logger.info(f"[DEBUG]   Row {ri}: {[str(c)[:25] if c else '' for c in row]}")
    
    images = extract_images_from_pdf(pdf_path)
    
    all_products = []
    
    for ti, target_table in enumerate(tables):
        if not target_table or len(target_table) < 2:
            continue
        
        # ─── 三策略并行 ───
        candidates = []
        model_keywords = ['model', '型号', '产品', 'item', 'sku', 'product', '产品名称', '编号']
        
        # ─── 策略0: KV规格表检测（仅限≤2列表格，优先） ───
        # 检查第一列是否大多是参数名（Motor: Battery: 等）
        # 多列表格（>=3列）可能是多产品对比表，不合并
        first_col_vals = [str(row[0] or '').strip() for row in target_table[1:21] if row and row[0]]
        param_val_count = sum(1 for v in first_col_vals if _is_param_name(v))
        num_data_cols = max(0, len(target_table[0]) - 1) if target_table else 0
        is_multi_kv = num_data_cols > 2 and len(first_col_vals) >= 3 and param_val_count > len(first_col_vals) * 0.6
        is_kv_spec = (num_data_cols <= 2 and len(first_col_vals) >= 3 and param_val_count > len(first_col_vals) * 0.6) or is_multi_kv
        
        if is_kv_spec:
            if is_multi_kv:
                # Multi-product comparison table (Model: S500 | S400 | S300)
                model_row_idx = None
                for idx, row in enumerate(target_table):
                    first_cell = str(row[0] if row else '').strip().lower().rstrip(':').rstrip('：')
                    if first_cell in ('model', '型号', '产品型号') or first_cell.startswith('model'):
                        model_row_idx = idx
                        break
                
                if model_row_idx is not None:
                    model_row = target_table[model_row_idx]
                    product_names = []
                    for ci in range(1, len(model_row)):
                        val = str(model_row[ci] or '').strip()
                        if val:
                            product_names.append((ci, val))
                    
                    if product_names:
                        multi_products = []
                        for col_idx, prod_name in product_names:
                            p = {
                                'model': prod_name.split()[0] if prod_name else prod_name,
                                'name_zh': prod_name,
                                'price_rmb': 0,
                                'spec_zh': '',
                                'currency': 'CNY',
                                '_image_path': '',
                                '_source_file': pdf_path,
                            }
                            price_raw_vals = []
                            specs = []
                            for row in target_table[model_row_idx + 1:]:
                                if not row or len(row) <= col_idx:
                                    continue
                                param_name = str(row[0] or '').strip()
                                param_val = str(row[col_idx] or '').strip()
                                if not param_val:
                                    continue
                                
                                # Check if this is a price row — also scan value for price signals
                                price_kw = ['price', 'usd', '出厂价', '价格', '报价', 'exw']
                                param_lower = param_name.lower()
                                val_lower = param_val.lower()
                                is_price = any(kw in param_lower for kw in price_kw) or '$' in param_name
                                # 值含usd/$也算价格行（如"950usd"）
                                if not is_price and val_lower:
                                    is_price = 'usd' in val_lower or '$' in val_lower
                                if is_price:
                                    nums = re.findall(r'([\d,]+(?:\.\d+)?)', param_val.replace(',', ''))
                                    if nums:
                                        try:
                                            pv = float(nums[0])
                                            price_raw_vals.append(pv)
                                            if p['price_rmb'] == 0:
                                                p['price_rmb'] = pv
                                            if 'usd' in param_lower or '$' in param_name or 'usd' in val_lower:
                                                p['currency'] = 'USD'
                                            continue
                                        except ValueError:
                                            pass
                                
                                if param_val:
                                    specs.append(f"{param_name}: {param_val}")
                            
                            if specs:
                                p['spec_zh'] = '; '.join(specs[:30])
                            multi_products.append(p)
                        
                        if multi_products:
                            df_multi = pd.DataFrame(multi_products)
                            candidates.append(('col_based', df_multi))
            else:
                # KV规格表：所有行合并为一个产品
                model_name = ''
                all_specs = []
                found_price = None
                found_currency = 'CNY'
                for row in target_table:
                    if not row or not row[0]:
                        continue
                    key = str(row[0]).strip()
                    val = str(row[1]).strip() if len(row) > 1 and row[1] else ''
                    key_lower = key.lower().rstrip(':：（）()').strip()
                    
                    # 检测型号行（匹配 "Model(产品型号)" "Model:" 等）
                    if key_lower.startswith('model') and len(key_lower) < 20:
                        model_name = val or key
                        continue
                    
                    # 检测价格（精确匹配：英文词用边界，中文词要求出现在最后30字）
                    is_price_line = False
                    for kw in ['price', 'exw', 'total']:
                        if re.search(r'\b' + kw + r'\b', key_lower):
                            is_price_line = True
                            break
                    for kw in ['价格', '出厂价', '出厂']:  # 精确匹配
                        if kw in key_lower:
                            is_price_line = True
                            break
                    # '报价'可能出现在"工厂报价"等复合词中 → 只在最后30字才算
                    if not is_price_line and '报价' in key_lower[-30:]:
                        is_price_line = True
                    
                    if is_price_line:
                        nums = re.findall(r'[\d,]+(?:\.\d+)?', val.replace(',', ''))
                        if nums:
                            try:
                                # 优先取 USD/CNY 旁边的数字，否则取最后一个
                                p = None
                                for ni, n in enumerate(nums):
                                    pos = val.find(n)
                                    after = val[pos + len(n):pos + len(n) + 10].lower()
                                    before = val[max(0, pos - 10):pos].lower()
                                    if 'usd' in after or 'usd' in before or '$' in after:
                                        p = float(n)
                                        found_currency = 'USD'
                                        break
                                    if 'cny' in after or 'cny' in before:
                                        p = float(n)
                                        found_currency = 'CNY'
                                        break
                                if p is None:
                                    p = float(nums[-1])
                                if p and p > 0:
                                    if found_price is None:
                                        found_price = p  # 第一个价格(单价)
                                    # else: keep first, don't overwrite with total
                            except Exception:
                                pass
                        continue
                    
                    # 跳过标题行（长文本、specification等）
                    if len(key) > 30 and not val:
                        if not model_name:
                            # 从标题提取型号（"G5000 E-motorcycle..." → "G5000"）
                            words = key.split()
                            if words:
                                model_name = words[0]
                        continue
                    
                    if val:
                        all_specs.append(f"{key}: {val}")
                    elif key:
                        all_specs.append(key)
                
                if model_name:
                    merged_spec = '\n'.join(all_specs)
                    df_kv = pd.DataFrame([{
                        'model': model_name.split()[0] if model_name else '',
                        'name_zh': model_name.split()[0] if model_name else '',
                        'price_rmb': found_price,
                        'spec_zh': merged_spec,
                        'currency': found_currency,
                        '_image_path': '',
                        '_source_file': pdf_path,
                    }])
                    if not df_kv.empty:
                        candidates.append(('kv_spec', df_kv))
        
        # 策略A: 布局检测提取
        layout = None
        if not is_kv_spec:
            layout = detect_table_layout(target_table)
        
        # 包装关键词集
        PACKAGING_KEYS = {'gw', 'n.w.', 'g.w.', 'nw', 'gross weight', 'net weight',
                          'gross', 'net', 'carton size', 'carton', 'package size',
                          'packing size', 'cbm', 'meas', 'measurement',
                          'qty/ctn', 'pcs/ctn', '每箱数量', '毛重', '净重', '外箱尺寸',
                          '包装尺寸', '体积', 'cartons', 'net weight(kg)'}
        
        # col_based 提取
        def _extract_col_based(table):
            products = []
            header_row_idx = None
            for idx, row in enumerate(table):
                row_str = ' '.join(str(c or '') for c in row).lower()
                if any(kw in row_str for kw in ['model', '型号', '产品', 'item', 'sku']):
                    header_row_idx = idx
                    break
            if header_row_idx is None:
                header_row_idx = 0
            header_row = table[header_row_idx]
            
            for col_idx in range(1, len(header_row)):
                model = header_row[col_idx]
                if not model or str(model).strip() == '':
                    continue
                # 过滤真正的产品型号(至少含一个字母+数字)
                model_str = str(model).strip()
                if not (any(c.isalpha() for c in model_str) and any(c.isdigit() for c in model_str)):
                    if not (model_str.isdigit() and len(model_str) >= 2):
                        continue
                # 跳过规格值(如 "Front:3.0-18" 是规格内容不是型号)
                if ':' in model_str or '：' in model_str:
                    continue
                specs = {}
                packaging = {}
                price_rmb = 0
                price_raw = []  # 保留所有价格供 spec 展示
                price_currency = 'CNY'
                # 检查表头行是否含USD/FOB标记
                header_val = str(header_row[col_idx] or '').lower() if col_idx < len(header_row) else ''
                if 'usd' in header_val or '$' in header_val or 'fob' in header_val:
                    price_currency = 'USD'
                # 也从第一列 key 文本检测币种（如表格第一列写"Price USD"）
                for row_idx in range(header_row_idx + 1, min(header_row_idx + 5, len(table))):
                    if table[row_idx] and len(table[row_idx]) > 0:
                        key0 = str(table[row_idx][0] or '').lower()
                        if 'usd' in key0 or '$' in key0:
                            price_currency = 'USD'
                            break
                for row_idx in range(header_row_idx + 1, len(table)):
                    if col_idx >= len(table[row_idx]):
                        continue
                    key = table[row_idx][0]
                    value = table[row_idx][col_idx]
                    if not key:
                        # 嵌套表头：第一列为空时，尝试用左邻列作为参数名
                        if col_idx > 0 and len(table[row_idx]) > col_idx:
                            alt_key = table[row_idx][col_idx - 1]
                            if alt_key and str(alt_key).strip():
                                key = alt_key
                                value = table[row_idx][col_idx]
                    if not key:
                        continue
                    key_str = str(key).strip()
                    key_lower = key_str.lower()
                    # 跳过非产品行（汇总行、标题行）
                    if key_lower in ('total', 'subtotal') or key_lower.startswith('vehicle specific'):
                        continue
                    if len(key_str) > 40 and len(str(value or '').strip()) < 3:
                        continue
                    value_str = str(value or '').strip()
                    # 价格检测:检查key和value两方面
                    price_keywords = ['price', '价格', '单价', 'rmb', 'cny', 'usd', '报价', 'exw', 'fob']
                    is_price = any(kw in key_lower for kw in price_keywords)
                    # 也检查value是否含usd等货币标记（price藏在spec文本中如"950usd"）
                    if not is_price and value_str:
                        v_lower = value_str.lower()
                        if re.search(r'\b\d+\.?\d*\s*(usd|cny|rmb|\$|¥|€)', v_lower):
                            is_price = True
                        elif re.search(r'(usd|cny|rmb|\$|¥|€)\s*\d+\.?\d*', v_lower):
                            is_price = True
                        # 检查value中的最后一个数字（排除spec中的功率数字如"5000W"）
                        elif any(kw in v_lower for kw in ['usd', '报价']) and re.search(r'\d+', v_lower):
                            is_price = True
                    if is_price:
                        # 优先找usd/cny/$旁边的数字(如"950usd"→950),其次取最后一个数字
                        price_num = None
                        # 1) 找 usd/cny/$/€ 旁边的数字
                        usd_match = re.search(r'([\d,]+(?:\.\d+)?)\s*(usd|cny|rmb|\$|¥|€)', value_str, re.I)
                        if not usd_match:
                            usd_match = re.search(r'(usd|cny|rmb|\$|¥|€)\s*([\d,]+(?:\.\d+)?)', value_str, re.I)
                            if usd_match:
                                price_num = usd_match.group(2)
                        else:
                            price_num = usd_match.group(1)
                        if not price_num:
                            # 2) 取所有数字中的最后一个(排除电压/功率等)
                            all_nums = re.findall(r'[\d,]+(?:\.\d+)?', value_str.replace(',', ''))
                            if all_nums:
                                # 过滤掉明显不是价格的数字(如电压87.6V、功率5000W)
                                filtered = [n for n in all_nums if 
                                            not re.search(r'(\d+V|\d+W|\d+AH|\d+KG|\d+NM)', n, re.I)]
                                if filtered:
                                    price_num = filtered[0]  # 第一个数字(通常是单价而非total)
                                else:
                                    price_num = all_nums[-1]
                        if price_num:
                            try:
                                p = float(price_num.replace(',', ''))
                                if p > 0:
                                    price_raw.append(p)  # 保留所有价格
                                    if price_rmb == 0:
                                        price_rmb = p  # 取第一个价格(通常是单价)
                                    # 标记币种
                                    if usd_match:
                                        m = usd_match.group(0).lower()
                                        if any(kw in m for kw in ['usd', '$']):
                                            price_currency = 'USD'
                                    # 表头已检测到USD/FOB标记则锁定币种
                                    if any(kw in (str(header_row[col_idx] or '').lower()) 
                                           for kw in ['usd', 'fob', '$']):
                                        price_currency = 'USD'
                            except Exception:
                                pass
                    elif any(kw in key_lower for kw in PACKAGING_KEYS):
                        packaging[key.strip()] = value_str
                    else:
                        specs[str(key).strip()] = value_str
                
                # 合并 specs 和 packaging 到 spec_zh
                all_specs = dict(specs)
                all_specs.update(packaging)
                # 清理型号名：去除"Model"、"型号"等前缀（"Model XF-1"→"XF-1"）
                model_clean = str(model).strip()
                model_clean = re.sub(r'^(model|型号|产品)\s*[：:\s]', '', model_clean, flags=re.I).strip()
                if not model_clean:
                    model_clean = str(model).strip()
                products.append({
                    'model': model_clean,
                    'name_zh': '',
                    'price_rmb': price_rmb,
                    'price_raw': ' | '.join([f'{price_currency} {p:,.2f}' for p in price_raw]) if len(price_raw) > 1 else '',
                    'currency': price_currency,
                    'spec_zh': format_spec_spec('; '.join(f"{k}: {v}" for k, v in all_specs.items())),
                    '_image_path': '',
                    '_source_file': pdf_path,
                })
            return pd.DataFrame(products)
        
        # row_based 提取
        def _extract_row_based(table):
            products = []
            header_row = table[0]
            # 检测第一列是否是序号列（纯数字），如是则从第2列取 model
            first_col_samples = [str(row[0] or '').strip() for row in table[1:8] if row and row[0]]
            is_serial_col = all(v.isdigit() and 1 <= int(v) <= 999 for v in first_col_samples if v)
            model_col_idx = 1 if is_serial_col else 0
            price_col_idx = None
            last_model = ''
            found_currency = 'CNY'
            for idx, col in enumerate(header_row):
                col_str = str(col or '').lower()
                if 'price' in col_str or '价格' in col_str or '单价' in col_str:
                    price_col_idx = idx
                    if 'usd' in col_str or '$' in col_str or 'fob' in col_str:
                        found_currency = 'USD'
            for row in table[1:]:
                model_raw = str(row[model_col_idx] or '').strip() if model_col_idx < len(row) else ''
                if model_raw:
                    # 过滤非产品行(规格值/参数名)
                    if ':' in model_raw or '：' in model_raw:
                        continue
                    if not (any(c.isalpha() for c in model_raw) and any(c.isdigit() for c in model_raw)):
                        if not (model_raw.isdigit() and len(model_raw) >= 2):
                            continue
                    last_model = model_raw
                model = last_model
                if not model:
                    continue
                price_rmb = 0
                if price_col_idx is not None and price_col_idx < len(row):
                    raw_val = str(row[price_col_idx] or '')
                    nums = re.findall(r'[\d,]+\.?\d*', raw_val)
                    if nums:
                        try:
                            price_rmb = float(nums[0].replace(',', ''))
                        except Exception:
                            pass
                    # 从价格值检测币种("950usd" → USD)
                    if 'usd' in raw_val.lower() or '$' in raw_val:
                        found_currency = 'USD'
                specs = {}
                for idx, val in enumerate(row):
                    if idx != model_col_idx and idx != price_col_idx:
                        key = header_row[idx] if idx < len(header_row) else f"spec_{idx}"
                        if key and val:
                            specs[str(key)] = str(val)
                products.append({
                    'model': model,
                    'name_zh': '',
                    'price_rmb': price_rmb,
                    'currency': found_currency,
                    'spec_zh': format_spec_spec('; '.join(f"{k}: {v}" for k, v in specs.items())),
                    '_image_path': '',
                    '_source_file': pdf_path,
                })
            return pd.DataFrame(products)
        
        if layout == 'col_based':
            candidates.append(('col_based', _extract_col_based(target_table)))
        elif layout == 'row_based' and not is_kv_spec:
            candidates.append(('row_based', _extract_row_based(target_table)))
        
        # 策略B: 内容分发提取（兜底 — 仅非KV规格表时）
        if not is_kv_spec:
            df_c = _parse_pdf_by_content(target_table)
            if not df_c.empty:
                candidates.append(('content', df_c))
        
        logger.info(f"[DEBUG] Candidates: {[(n, round(float(_score_pdf_result(c, n)), 2)) for n, c in candidates]}")
        
        # 择优：布局策略（col/row/kv）优先，内容策略只有当评分远超时才胜出
        if candidates:
            layout_candidates = [c for c in candidates if c[0] in ('col_based', 'row_based', 'kv_spec')]
            content_candidates = [c for c in candidates if c[0] == 'content']
            
            best_layout = max(layout_candidates, key=lambda c: _score_pdf_result(c[1], c[0])) if layout_candidates else None
            best_content = max(content_candidates, key=lambda c: _score_pdf_result(c[1], c[0])) if content_candidates else None
            
            if best_layout and best_content:
                score_layout = _score_pdf_result(best_layout[1], best_layout[0])
                score_content = _score_pdf_result(best_content[1], best_content[0])
                # 内容策略只有当评分远超布局策略时才使用（防止内容策略靠数量碾压）
                if score_content > score_layout * 1.5:
                    df_best = best_content[1]
                else:
                    df_best = best_layout[1]
            elif best_layout:
                df_best = best_layout[1]
            else:
                best = max(candidates, key=lambda c: _score_pdf_result(c[1], c[0]))
                df_best = best[1]
            
            if not df_best.empty:
                df_best['_page'] = table_positions[ti][0] if ti < len(table_positions) else 0
                all_products.append(df_best)
    
    # Fallback: all strategies failed, try content inference from first non-empty table
    if not all_products:
        for ti, table in enumerate(tables):
            if not table or len(table) < 3:
                continue
            df_fb = _parse_pdf_by_content(table)
            if df_fb is not None and not df_fb.empty:
                df_fb['_page'] = table_positions[ti][0] if ti < len(table_positions) else 0
                all_products.append(df_fb)
                logger.info(f"[FALLBACK] Content fallback used for {os.path.basename(pdf_path)} ({len(df_fb)} products)")
                break

    # Docling fallback: all normal candidates failed, try Docling
    if not all_products and _USE_DOCLING:
        docling_df = _parse_pdf_via_docling(pdf_path)
        if docling_df is not None and not docling_df.empty:
            docling_df['_page'] = 0  # Docling has no page info
            all_products.append(docling_df)
            logger.info(f"[DOCLING] Used as fallback for {os.path.basename(pdf_path)} ({len(docling_df)} products)")

    if not all_products:
        return None
    
    df = pd.concat(all_products, ignore_index=True)
    
    # 跨表价格匹配:如果第一个表的产品没有价格,检查后续表是否有按列对应的价格
    if not df.empty and 'price_rmb' in df.columns:
        all_zero = all(
            p is None or p == 0 or p == 0.0 
            for p in df['price_rmb'].values
        )
        if all_zero:
            for table in tables[1:]:
                for row in table:
                    for ci, cell in enumerate(row[1:], 1):
                        val = str(cell or '').strip().lower()
                        m = re.search(r'([\d,]+(?:\.\d+)?)\s*(usd|cny|rmb|\$|¥|€)', val, re.I)
                        if not m:
                            m = re.search(r'(usd|cny|rmb|\$|¥|€)\s*([\d,]+(?:\.\d+)?)', val, re.I)
                            if m:
                                price_val = m.group(2)
                            else:
                                continue
                        else:
                            price_val = m.group(1)
                        try:
                            p = float(price_val.replace(',', ''))
                            if ci <= len(df):
                                idx = ci - 1
                                if df.at[idx, 'price_rmb'] == 0 or df.at[idx, 'price_rmb'] is None:
                                    df.at[idx, 'price_rmb'] = p  # 取第一个价格(单价),不覆盖
                                    # 检测币种
                                    if 'usd' in val or '$' in val:
                                        if 'currency' in df.columns:
                                            df.at[idx, 'currency'] = 'USD'
                        except Exception:
                            pass
    
    df = _associate_images_to_products(df, images)
    # 过滤非产品行
    if 'model' in df.columns:
        mask = df['model'].notna() & (df['model'] != '') & (df['model'].astype(str).str.strip() != '')
        df = df[mask]
        
        def _is_real_model(m):
            m = str(m).strip()
            if not m:
                return False
            if len(m) < 2:
                return False
            # 含冒号 → 规格值
            if ':' in m or '：' in m:
                return False
            # 纯数字 → 允许(可能是序列号)
            if m.isdigit():
                return len(m) >= 2
            # 必须含至少一个字母+一个数字
            if not (any(c.isalpha() for c in m) and any(c.isdigit() for c in m)):
                return False
            # 过滤规格表达式(mmxmm, usd结尾等)
            spec_patterns = [r'\d+\s*mm', r'mm\*mm', r'usd$', r'\d+usd', r'^\d+\.\d+']
            for pat in spec_patterns:
                if re.search(pat, m, re.I):
                    return False
            # 过滤已知参数名
            if m.lower() in {'motor', 'battery', 'weight', 'speed', 'controller',
                             'charging', 'dimension', 'wheelbase', 'tire', 'tyre',
                             'brake', 'suspension', 'ground', 'clearance', 'seat',
                             'height', 'material', 'color', 'tires', 'front', 'rear',
                             'length', 'width', 'full height', 'addon', 'power',
                             'voltage', 'current', 'torque', 'range', '产品', '参数',
                             '规格', '尺寸', '报价', '价格', '马达', '电机'}:
                return False
            return True
        
        df = df[df['model'].astype(str).apply(_is_real_model)]
    df = df.reset_index(drop=True)
    df['_row'] = range(1, len(df) + 1)
    df['_sheet'] = os.path.basename(pdf_path)
    return df


def _associate_images_to_products(df: pd.DataFrame, images: List[Dict]) -> pd.DataFrame:
    """关联图片到产品 — 按页面位置匹配。
    
    每个产品带有 _page 标记（源自 table_positions），
    图片也带有 page 信息。按页面分组后，同一页内的产品和图片
    按出现顺序一一对应，确保图片不会跨页错配。
    如果某个页面没有图片，该页产品保持无图。
    """
    df = df.copy()
    df['_image_path'] = ''
    
    if not images or df.empty:
        return df
    
    # 按页面分组
    has_page_info = '_page' in df.columns
    if not has_page_info:
        # 没有页面信息，不分配（避免跨页错误匹配）
        return df
    
    # 图片按页面分组
    images_by_page = {}
    for img in images:
        p = img.get('page', 0)
        images_by_page.setdefault(p, []).append(img)
    
    # 对每个页面，按 (page, 页内序号) 排序图片
    for p in images_by_page:
        images_by_page[p].sort(key=lambda x: x.get('index', 0))
    
    # 产品按页面分组，同一个页面内的产品按出现顺序与图片一一对应
    page_groups = df.groupby('_page')
    result_parts = []
    for page_num, group_df in page_groups:
        group_df = group_df.copy()
        page_images = images_by_page.get(page_num, [])
        if page_images:
            for i in range(min(len(group_df), len(page_images))):
                group_df.iloc[i, group_df.columns.get_loc('_image_path')] = page_images[i]['image_path']
        result_parts.append(group_df)
    
    df = pd.concat(result_parts) if result_parts else df
    
    return df