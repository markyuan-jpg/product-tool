"""
score.py — 解析质量评分系统
供 backend/main.py、excel_parser_v3.py 等模块共用
"""

import re

# 自动生成的假型号模式
_AUTO_MODEL_RE = re.compile(r'^(商品_?R\d+|PRODUCT_\d+|Item_\d+|\u5546\u54c1_\u00d7\d+|产品_R\d+)$')
# 真型号检测
_REAL_MODEL_RE = re.compile(r'[A-Za-z]')
_REAL_DIGIT_RE = re.compile(r'\d')

# ─── 统一型号验证函数（供所有解析器导入） ───

def is_valid_model(model_str: str, strict: bool = True) -> bool:
    """统一的型号验证 — PDF/Excel/DOCX/universal 解析器共用。
    
    strict=True:  必须字母+数字 (评分/一致性计算用)
    strict=False: 允许纯数字（价格列存在时可能是合法SKU）
    """
    if not model_str or not isinstance(model_str, str):
        return False
    m = model_str.strip()
    if len(m) < 2 or len(m) > 40:
        return False
    if ':' in m or '：' in m:
        return False
    # 排除自动生成的假型号
    if _AUTO_MODEL_RE.match(m):
        return False
    # 排除字段/条款关键词
    if _contains_field_keyword(m):
        return False
    # 排除纯规格模式（mm+数字+usd 等）
    if re.search(r'(\d+\.?\d*\s*mm|\d+\.?\d*\s*cm|\d+v\b|\d+w\b)', m.lower()):
        return False
    has_letter = bool(_REAL_MODEL_RE.search(m))
    has_digit = bool(_REAL_DIGIT_RE.search(m))
    # 中文字符限制（过多中文可能不是型号）
    chinese_count = len(re.findall(r'[\u4e00-\u9fff]', m))
    if chinese_count > 10:
        return False
    if strict:
        # 严格模式：必须包含字母+数字
        return has_letter and has_digit
    else:
        # 宽松模式：允许纯数字（可能为SKU），但不允许纯字母
        return has_digit or (has_letter and len(m) <= 12)

# 已知字段/条款名 — 这些不应被当作产品型号
_FIELD_NAMES = {
    'contract', 'seller', 'buyer', 'payment', 'shipping', 'delivery',
    'transshipment', 'remarks', 'note', 'terms', 'conditions',
    'address', 'tel', 'fax', 'email', 'website', 'phone',
    'bank', 'account', 'beneficiary', 'swift', 'sort code',
    'contact', 'signature', 'date', 'invoice', 'validity',
    'total', 'subtotal', 'amount', '合计', '总计', '金额', '小计',
    '包装', '运输', '付款', '交货', '条款', '备注', '说明',
    '合同', '卖方', '买方', '地址', '电话', '邮箱', '日期',
    '受益', '银行', '账户', '签名', '签字',
    'description', 'product', 'model', 'item', 'specification',
    'hs code', 'origin', 'manufacturer', 'brand',
}

# 单独的条款关键词（用于contains检查，比_FIELD_NAMES的精确匹配宽松）
_TERM_KEYWORDS = ['transshipment', 'payment', 'delivery', 'shipping', 'bank',
                  'contract', 'invoice', 'signature', 'validity', 'beneficiary',
                  '条款', '付款', '交货', '运输', '银行', '合同', '日期', '签字', '签名',
                  'seal', 'stamp', '仲裁', '保险', '不可抗力']


def _contains_field_keyword(m: str) -> bool:
    """检查 model 是否包含已知的字段/条款关键词（作为独立词）"""
    ml = m.lower().strip().rstrip(':').rstrip('：').rstrip('.').rstrip(')').rstrip('）')
    # 精确匹配
    if ml in _FIELD_NAMES:
        return True
    # 词边界匹配（避免 "Contractor" 被 "contract" 误杀）
    for kw in _FIELD_NAMES:
        if kw and len(kw) >= 2:
            if re.search(r'\b' + re.escape(kw) + r'\b', ml):
                return True
    # 含有关键词做子词（如 "5. transshipment" → "transshipment"）
    for kw in _TERM_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', ml):
            return True
    return False


def _is_reasonable_price(p):
    """价格应该在一个合理的范围内（不是年份、序号等）"""
    if p is None:
        return False
    # 排除年份（动态范围：当前年份-3 ~ 当前年份+5）
    from datetime import datetime
    this_year = datetime.now().year
    if this_year - 3 <= p <= this_year + 5 and p == int(p) and 2000 <= p <= 2100:
        return False
    # 排除纯序号（1~9的小整数）
    if 1 <= p <= 9 and p == int(p):
        return False
    # 排除极小值
    if p <= 0.1:
        return False
    # 排除极大值
    if p >= 10000000:
        return False
    return True


def score_product_row(model: str, price, spec_zh: str) -> float:
    """对单个产品行评分"""
    m = str(model).strip() if model else ''
    p = price if isinstance(price, (int, float)) else None
    spec = str(spec_zh).strip() if spec_zh else ''

    has_price = _is_reasonable_price(p)
    has_spec = len(spec) > 30
    is_empty = not m or len(m) < 2

    # 检查model是否包含条款/字段关键词
    _has_field_kw = _contains_field_keyword(m)

    # 真型号检查 - 放宽版：支持纯中文+数字、纯数字+价格、英文+数字
    is_real = (
        2 <= len(m) <= 30
        and ':' not in m
        and '\uff1a' not in m  # fullwidth colon
        and not _has_field_kw
        and len(re.findall(r'[\u4e00-\u9fff]', m)) <= 10
        # 至少含数字 OR 有合理价格+短字符串
        and (bool(_REAL_DIGIT_RE.search(m)) or (has_price and len(m) <= 12))
    )

    # 假型号检查
    is_fake = bool(_AUTO_MODEL_RE.match(m)) if not is_empty else False

    # ---- 信号组合评分 ----
    if is_real and has_price and has_spec:
        return 7.0   # 最强：真型号+价格+参数
    if is_real and has_price:
        return 5.0   # 强：真型号+价格
    if is_real and has_spec:
        return 4.0   # 中：真型号+参数
    if is_real:
        return 2.0   # 可接受：只有真型号

    # ---- 弱信号 ----
    if has_price and not is_empty:
        # 额外检查：model含字段/条款关键词 → 垃圾
        if _has_field_kw:
            return -1.0
        return 1.0
    if m and not is_fake and not is_empty:
        # 额外检查：model含字段/条款关键词 → 垃圾
        if _has_field_kw:
            return -1.0
        return 1.0   # 有内容但非标准型号

    # ---- 噪音/错误 ----
    if is_fake:
        return -3.0
    if is_empty and not has_price:
        return -3.0
    if ':' in m or '\uff1a' in m:
        return -2.0
    if len(m) > 40:
        return -2.0

    return 0.0


def score_dataframe(df) -> dict:
    """
    对整个解析结果评分
    返回: {'score': float, 'count': int, 'real_models': int, 'prices': int, 'details': dict}
    """
    if df is None or df.empty:
        return {'score': -999.0, 'count': 0, 'real_models': 0, 'prices': 0}

    total = 0.0
    real_models = 0
    prices = 0
    product_scores = []

    for _, row in df.iterrows():
        s = score_product_row(
            row.get('model', ''),
            row.get('price_rmb'),
            row.get('spec_zh', '')
        )
        total += s
        product_scores.append(s)
        if s >= 5.0:
            real_models += 1
            if row.get('price_rmb') and isinstance(row.get('price_rmb'), (int, float)) and row['price_rmb'] > 0:
                prices += 1

    n = len(df)
    avg = round(total / n, 1) if n > 0 else -999.0

    # ---- 一致性加成 ----
    bonus = 0.0
    unique_real = len(set(
        str(row['model']).strip() for _, row in df.iterrows()
        if 2 <= len(str(row.get('model', '')).strip()) <= 30
        and bool(_REAL_MODEL_RE.search(str(row.get('model', ''))))
        and bool(_REAL_DIGIT_RE.search(str(row.get('model', ''))))
    ))
    if unique_real >= 3:
        bonus += 3.0  # 有 ≥3 个不同真型号
    if prices >= 3:
        bonus += 2.0  # 有 ≥3 个产品有价格
    empty_ratio = sum(1 for s in product_scores if s <= -3) / n if n > 0 else 1
    if empty_ratio < 0.2 and n >= 3:
        bonus += 1.0  # 空行/噪音比例 < 20%

    return {
        'score': avg + (bonus / n if n > 0 else 0),
        'count': n,
        'real_models': real_models,
        'prices': prices,
        'details': {
            'avg_product_score': avg,
            'bonus': round(bonus / n, 2) if n > 0 else 0,
            'empty_ratio': round(empty_ratio, 2),
        }
    }
