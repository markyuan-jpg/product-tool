# -*- coding: utf-8 -*-
"""
价格提取增强版
支持：公式值、千分位、范围价格、多货币、百分比
"""
import re
from typing import Optional, Union, Dict, List, Tuple, Any


# 货币符号映射
CURRENCY_MAP = {
    '$': 'USD', 'usd': 'USD',
    '€': 'EUR', 'eur': 'EUR',
    '£': 'GBP', 'gbp': 'GBP',
    '¥': 'CNY', '￥': 'CNY', 'rmb': 'CNY',
    '₦': 'NGN', 'ngn': 'NGN',
    '₹': 'INR', 'inr': 'INR',
    '$': 'USD',
}

# 常用单位
UNIT_MAP = {
    'k': 1000, 'K': 1000,
    'w': 10000, 'W': 10000,
    'm': 1000000, 'M': 1000000,
    'k USD': 1000, 'K USD': 1000,
}


def extract_numbers(text: str) -> list:
    """
    提取所有数字
    
    返回: [数字,...]
    """
    if text is None:
        return []
    
    text = str(text).strip()
    if not text:
        return []
    
    # 匹配数字模式
    # 支持: 1000, 1,000, 1,000.00, 1000.00, ¥1000, $1000, 1000USD
    pattern = r'[\d,]+(?:\.\d+)?'
    
    matches = re.findall(pattern, text)
    
    result = []
    for m in matches:
        # 移除千分位逗号
        try:
            num = float(m.replace(',', ''))
            result.append(num)
        except ValueError:
            continue
    
    return result


def detect_currency(text: str) -> str:
    """
    检测货币类型
    
    返回: 'USD', 'CNY', ...
    """
    if text is None:
        return 'CNY'  # 默认人民币
    
    text = str(text).upper()
    
    for symbol, currency in CURRENCY_MAP.items():
        if symbol.upper() in text:
            return currency
    
    return 'CNY'  # 默认


def clean_price_value(
    value: Union[str, int, float, None],
    default_currency: str = 'CNY'
) -> Optional[float]:
    """
    清洗价格值
    
    支持格式:
    - 1000           -> 1000.0
    - 1,000         -> 1000.0
    - ¥1000         -> 1000.0
    - $1000          -> 1000.0 (美元)
    - 1000 USD      -> 1000.0
    - ¥1,000        -> 1000.0
    - 1000-1500     -> 1250.0 (取中间值)
    - 1000~1500     -> 1250.0
    - 1000 or 1500   -> 1250.0
    - 10% off      -> 0.9 (折扣)
    - 折            -> 原值
    
    Returns:
        float: 价格数值 (人民币)
    """
    if value is None:
        return None
    
    # 如果已是数字
    if isinstance(value, (int, float)):
        if value > 0:
            return float(value)
        return None
    
    text = str(value).strip()
    if not text:
        return None
    
    # 检测折扣
    if '%' in text or '折' in text:
        # 例如: 10% off, 8折
        nums = extract_numbers(text)
        if nums:
            if '折' in text:
                # 8折 = 0.8
                return nums[0] / 10.0
            elif 'off' in text.lower():
                # 10% off = 9折 = 0.9
                return nums[0] * 0.01
    
    # 范围价格
    if '-' in text or '~' in text or 'or' in text.lower():
        # 1000-1500 -> 取平均
        nums = extract_numbers(text)
        if len(nums) >= 2:
            return (nums[0] + nums[1]) / 2
        elif len(nums) == 1:
            return nums[0]
    
    # 检测货币并转换
    currency = detect_currency(text)
    
    # 提取数字
    nums = extract_numbers(text)
    if not nums:
        return None
    
    # 取第一个有效数字
    price = nums[0]
    
    # 处理K/W单位 (仅数字紧邻K/W时，避免型号误触如"SKU-45K")
    text_upper = text.upper()
    if re.search(r'\dK\b', text_upper) and 'KG' not in text_upper:
        price = price * 1000
    elif re.search(r'\dW\b', text_upper):
        price = price * 10000
    
    # 货币转换 (统一转为人民币)
    _EXCHANGE_RATES = {
        'USD': 7.2,
        'EUR': 7.8,
        'GBP': 9.0,
        'NGN': 0.01,
        'INR': 0.087,
    }
    
    try:
        from src.rates import get_rate
        usd_to_cny = get_rate('USD', 'CNY')
        if usd_to_cny:
            _EXCHANGE_RATES['USD'] = usd_to_cny
    except ImportError:
        pass
    
    rate = _EXCHANGE_RATES.get(currency.upper())
    if rate is not None:
        price = price * rate
    
    return price


def format_price(
    value: Optional[float],
    currency: str = 'CNY',
    include_currency: bool = True
) -> str:
    """
    格式化价格输出
    
    Args:
        value: 价格数值
        currency: 货币类型
        include_currency: 是否包含货币符号
    
    Returns:
        str: 格式化后的字符串
    """
    if value is None:
        return ''
    
    if not include_currency:
        return f'{value:,.2f}'
    
    symbols = {'CNY': '¥', 'USD': '$', 'EUR': '€', 'GBP': '£'}
    symbol = symbols.get(currency, '¥')
    
    return f'{symbol}{value:,.2f}'


def batch_clean_prices(values: list) -> list:
    """批量清洗价格"""
    return [clean_price_value(v) for v in values]


# ==================== 测试 ====================

if __name__ == "__main__":
    test_cases = [
        '1000',
        '1,000',
        '¥1000',
        '$1000',
        '1000 USD',
        '1000-1500',
        '1000~1500',
        '1000 or 1500',
        '¥1,000',
        '5K',
        '10W',
        1000,
        1000.50,
        None,
    ]
    
    print("价格清洗测试:")
    for tc in test_cases:
        result = clean_price_value(tc)
        print(f"  {tc!r:20} -> {result}")


def classify_composite_price(
    text: str,
    industry_config: dict,
    existing_prices: Dict[str, List[Tuple[float, str]]] = None
) -> Dict[str, Any]:
    """Parse composite price string, classify into primary/secondary by industry_config.
    
    Input: "EV: CNY 4980 / Battery: CNY 2530 / Charger: CNY 230"
    Returns: {
        'primary_price': 4980.0,
        'primary_currency': 'CNY',
        'prices': {'battery': [(2530.0, 'CNY')], 'charger': [(230.0, 'CNY')]},
        'spec_lines': ['Battery Price: CNY 2,530.00', 'Charger Price: CNY 230.00']
    }
    """
    from ..price_config import classify_price, get_secondary_labels

    result = {
        'primary_price': None,
        'primary_currency': 'CNY',
        'prices': {},
        'spec_lines': [],
        'unclassified': [],
    }

    if not text:
        return result

    parts = str(text).replace('\n', '/').split('/')
    secondary_labels = get_secondary_labels(industry_config)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        match = re.match(r'([A-Za-z\u4e00-\u9fff]+)\s*[:\s]*([A-Z]{3})?\s*([\d,]+(?:\.\d+)?)', part)
        if not match:
            nums = re.findall(r'[\d,]+(?:\.\d+)?', part)
            if nums:
                val = clean_price_value(nums[0])
                if val:
                    if result['primary_price'] is None:
                        result['primary_price'] = val
                    else:
                        result['prices'].setdefault('unclassified', []).append((val, 'CNY'))
            continue

        item_name = match.group(1)
        currency_raw = (match.group(2) or 'CNY').upper()
        price_str = match.group(3)
        price_val = clean_price_value(price_str)
        if not price_val:
            continue

        currency = CURRENCY_MAP.get(currency_raw, currency_raw)
        ptype, label, is_primary = classify_price(item_name, industry_config)

        if is_primary:
            if result['primary_price'] is None:
                result['primary_price'] = price_val
                result['primary_currency'] = currency
            else:
                result['prices'].setdefault('unclassified', []).append((price_val, currency))
        else:
            result['prices'].setdefault(ptype, []).append((price_val, currency))
            display_label = secondary_labels.get(ptype, label)
            result['spec_lines'].append(f"{display_label}: {currency} {price_val:,.2f}")

    if result['primary_price'] is None and result['prices']:
        all_prices = []
        for vals in result['prices'].values():
            all_prices.extend(vals)
        if all_prices:
            all_prices.sort(key=lambda x: -x[0])
            result['primary_price'] = all_prices[0][0]
            result['primary_currency'] = all_prices[0][1]

    return result