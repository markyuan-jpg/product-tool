# -*- coding: utf-8 -*-
"""
Quotation Helpers - Tiered Pricing, Discounts, MOQ
"""
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class PriceTier:
    """价格层级"""
    min_qty: int
    max_qty: Optional[int]  # None = 无上限
    unit_price: float
    
    def matches(self, qty: int) -> bool:
        if self.max_qty is None:
            return qty >= self.min_qty
        return self.min_qty <= qty <= self.max_qty


@dataclass
class Discount:
    """折扣"""
    code: str
    discount_type: str  # 'percentage' | 'fixed'
    value: float  # 百分比(如10)或固定金额(如100)
    min_order: float = 0  # 最低订单金额生效
    description: str = ""
    
    def calculate(self, amount: float) -> float:
        if amount < self.min_order:
            return 0
        if self.discount_type == 'percentage':
            return amount * (self.value / 100)
        return min(self.value, amount)  # 不超过订单金额


class TieredPricing:
    """阶梯价计算器"""
    
    def __init__(self, tiers: List[PriceTier]):
        self.tiers = sorted(tiers, key=lambda t: t.min_qty)
    
    def get_unit_price(self, qty: int) -> float:
        for tier in self.tiers:
            if tier.matches(qty):
                return tier.unit_price
        if self.tiers:
            return self.tiers[0].unit_price  # 默认最低价
        return 0
    
    def calculate_total(self, qty: int) -> float:
        return qty * self.get_unit_price(qty)


def apply_discount(amount: float, discount: Optional[Discount]) -> Dict[str, Any]:
    """应用折扣
    
    Args:
        amount: 原始金额
        discount: 折扣对象
        
    Returns:
        {'original': float, 'discount': float, 'final': float}
    """
    if not discount:
        return {'original': amount, 'discount': 0, 'final': amount}
    
    discount_amount = discount.calculate(amount)
    return {
        'original': amount,
        'discount': discount_amount,
        'final': amount - discount_amount
    }


def validate_moq(qty: int, moq: int) -> Dict[str, Any]:
    """验证MOQ
    
    Returns:
        {'valid': bool, 'message': str, 'suggested_qty': int or None}
    """
    if qty >= moq:
        return {'valid': True, 'message': f'MOQ满足 ({qty} >= {moq})', 'suggested_qty': None}
    
    return {
        'valid': False,
        'message': f'低于MOQ ({qty} < {moq})',
        'suggested_qty': moq
    }


def calculate_quotation(
    items: List[Dict[str, Any]],
    discounts: List[Discount] = None,
    currency: str = 'CNY'
) -> Dict[str, Any]:
    """计算完整报价单
    
    Args:
        items: [{'sku': str, 'name': str, 'qty': int, 'unit_price': float, 'moq': int}]
        discounts: 可用折扣列表
        currency: 货币
        
    Returns:
        完整报价结果
    """
    lines = []
    subtotal = 0
    
    for item in items:
        qty = item.get('qty', 1)
        unit_price = item.get('unit_price', 0)
        moq = item.get('moq', 1)
        
        line_total = qty * unit_price
        moq_check = validate_moq(qty, moq)
        
        lines.append({
            'sku': item.get('sku', ''),
            'name': item.get('name', ''),
            'qty': qty,
            'unit_price': unit_price,
            'total': line_total,
            'moq_valid': moq_check['valid'],
            'moq_message': moq_check['message'],
        })
        
        if not moq_check['valid']:
            continue
        subtotal += line_total
    
    best_discount = None
    best_savings = 0
    
    if discounts:
        for disc in discounts:
            savings = disc.calculate(subtotal)
            if savings > best_savings:
                best_savings = savings
                best_discount = disc
    
    discount_result = apply_discount(subtotal, best_discount)
    
    return {
        'currency': currency,
        'lines': lines,
        'subtotal': subtotal,
        'discount_code': best_discount.code if best_discount else None,
        'discount_amount': discount_result['discount'],
        'total': discount_result['final'],
        'moq_errors': [l for l in lines if not l['moq_valid']],
    }


# 预设折扣示例
DEFAULT_DISCOUNTS = [
    Discount('BULK10', 'percentage', 10, min_order=5000, description='订单满5000享10%折扣'),
    Discount('BULK15', 'percentage', 15, min_order=10000, description='订单满10000享15%折扣'),
    Discount('VIP20', 'percentage', 20, min_order=20000, description='VIP客户满20000享20%折扣'),
    Discount('FIXED100', 'fixed', 100, min_order=1000, description='订单满1000减100'),
]


if __name__ == '__main__':
    items = [
        {'sku': 'A001', 'name': '产品A', 'qty': 100, 'unit_price': 50, 'moq': 10},
        {'sku': 'B002', 'name': '产品B', 'qty': 5, 'unit_price': 200, 'moq': 10},  # MOQ错误
    ]
    
    result = calculate_quotation(items, DEFAULT_DISCOUNTS)
    
    print(f"商品数: {len(result['lines'])}")
    print(f"小计: {result['subtotal']}")
    print(f"折扣: {result['discount_code']} - {result['discount_amount']}")
    print(f"总计: {result['total']}")
    print(f"MOQ错误: {len(result['moq_errors'])}")