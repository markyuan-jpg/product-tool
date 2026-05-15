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


def score_product_row(model: str, price, spec_zh: str) -> float:
    """对单个产品行评分"""
    m = str(model).strip() if model else ''
    p = price if isinstance(price, (int, float)) else None
    spec = str(spec_zh).strip() if spec_zh else ''

    has_price = p is not None and p > 0
    has_spec = len(spec) > 30
    is_empty = not m or len(m) < 2

    # 真型号检查
    is_real = (
        2 <= len(m) <= 30
        and bool(_REAL_MODEL_RE.search(m))
        and bool(_REAL_DIGIT_RE.search(m))
        and ':' not in m
        and '\uff1a' not in m
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
        return 1.0
    if m and not is_fake and not is_empty:
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
