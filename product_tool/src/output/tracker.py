# -*- coding: utf-8 -*-
"""
Quote Tracker - 简化版报价追踪
记录报价单ID、客户信息、查看次数、最后查看时间
"""
import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

TRACKER_DB = Path(__file__).parent.parent.parent / 'data' / 'quote_tracker.json'


def _load_tracker() -> List[Dict]:
    """加载追踪数据"""
    TRACKER_DB.parent.mkdir(parents=True, exist_ok=True)
    if not TRACKER_DB.exists():
        return []
    with open(TRACKER_DB, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_tracker(data: List[Dict]) -> None:
    """保存追踪数据"""
    TRACKER_DB.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def generate_quote_id() -> str:
    """生成短报价ID"""
    return uuid.uuid4().hex[:8].upper()


def create_tracking_link(
    product_ids: List[int],
    customer_name: str,
    customer_email: str,
    notes: str = "",
    expiration_days: int = 30
) -> Dict[str, Any]:
    """创建追踪链接
    
    Args:
        product_ids: 产品ID列表
        customer_name: 客户名称
        customer_email: 客户邮箱
        notes: 备注
        expiration_days: 有效期天数
        
    Returns:
        {'quote_id': str, 'access_key': str, 'url': str}
    """
    tracker = _load_tracker()
    
    quote_id = generate_quote_id()
    access_key = uuid.uuid4().hex[:12]
    
    created_at = datetime.now().timestamp()
    expires_at = (datetime.now().timestamp() + expiration_days * 86400)
    
    record = {
        'quote_id': quote_id,
        'access_key': access_key,
        'product_ids': product_ids,
        'customer_name': customer_name,
        'customer_email': customer_email,
        'notes': notes,
        'created_at': created_at,
        'expires_at': expires_at,
        'view_count': 0,
        'last_viewed': None,
        'view_history': [],
    }
    
    tracker.append(record)
    _save_tracker(tracker)
    
    return {
        'quote_id': quote_id,
        'access_key': access_key,
        'url': f'/quote/{quote_id}?key={access_key}'
    }


def record_view(quote_id: str, access_key: str, viewer_email: str = None) -> Optional[Dict]:
    """记录查看
    
    Args:
        quote_id: 报价单ID
        access_key: 访问密钥
        viewer_email: 查看者邮箱
        
    Returns:
        更新后的记录或None(无效ID/Key)
    """
    tracker = _load_tracker()
    
    for record in tracker:
        if record['quote_id'] == quote_id and record['access_key'] == access_key:
            view_at = datetime.now().isoformat()
            
            record['view_count'] = record.get('view_count', 0) + 1
            record['last_viewed'] = view_at
            record['view_history'] = record.get('view_history', [])
            record['view_history'].append({
                'at': view_at,
                'email': viewer_email,
            })
            
            _save_tracker(tracker)
            return record
    
    return None


def get_quote_status(quote_id: str) -> Optional[Dict]:
    """获取报价单状态
    
    Args:
        quote_id: 报价单ID
        
    Returns:
        状态记录或None
    """
    tracker = _load_tracker()
    
    for record in tracker:
        if record['quote_id'] == quote_id:
            return {
                'quote_id': quote_id,
                'customer_name': record['customer_name'],
                'customer_email': record['customer_email'],
                'view_count': record.get('view_count', 0),
                'last_viewed': record.get('last_viewed'),
                'created_at': record['created_at'],
                'expires_at': record.get('expires_at'),
            }
    
    return None


def list_quotes(status: str = 'all') -> List[Dict]:
    """列出报价单
    
    Args:
        status: 'all' | 'active' | 'expired'
        
    Returns:
        报价单列表
    """
    tracker = _load_tracker()
    now = datetime.now().timestamp()
    
    result = []
    for record in tracker:
        if status == 'expired' and record.get('expires_at', float('inf')) < now:
            result.append(record)
        elif status == 'active' and record.get('expires_at', float('inf')) > now:
            result.append(record)
        elif status == 'all':
            result.append(record)
    
    return sorted(result, key=lambda x: x.get('created_at', 0), reverse=True)


def validate_quote(quote_id: str, access_key: str) -> bool:
    """验证报价单访问权限 (无副作用，不记录查看)"""
    tracker = _load_tracker()
    for record in tracker:
        if record['quote_id'] == quote_id and record['access_key'] == access_key:
            return True
    return False


if __name__ == '__main__':
    link = create_tracking_link(
        product_ids=[1, 2, 3],
        customer_name="Test Customer",
        customer_email="test@example.com",
        notes="测试报价",
    )
    print(f"Created: {link}")
    
    status = get_quote_status(link['quote_id'])
    print(f"Status: {status}")
    
    quotes = list_quotes('active')
    print(f"Active quotes: {len(quotes)}")