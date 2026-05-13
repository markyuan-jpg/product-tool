# -*- coding: utf-8 -*-
"""
Spec Formatter - 结构化规格参数格式化
将散乱的spec_raw格式化为"参数名: 值"格式
"""
import re
from typing import List, Dict, Optional
from ..config import SPEC_UNITS, SPEC_PATTERNS
from .spec_cleaner import clean_spec


DEFAULT_SPEC_UNITS = [
    'mm', 'cm', 'm', 'inch', 'in', 'ft',
    'kg', 'g', 'lb',
    'W', 'kW', 'MW',
    'V', 'kV', 'A', 'AH', 'mAH',
    'km', 'km/h', 'mph',
    'rpm', 'N.m', 'N·m',
    'L', 'ml', 'g/L',
    'pc', 'pcs', 'set', 'box', 'pair',
    '%', 'degree', '°'
]


def format_spec_spec(spec_raw: str) -> str:
    """
    格式化规格参数
    
    输入: 散乱的spec_raw字符串(可能含换行、分号、空格分隔等)
    输出: 格式化的spec_zh字符串
    
    流程:
    1. 按换行符/n分割原始文本
    2. 冒号匹配(参数名: 值)
    3. 空格分隔匹配(参数名: 值 参数名: 值) - 新增
    4. 无冒号空格匹配(参数名 值,含数字+单位) - 新增
    5. 自定义正则匹配
    6. 剩余行保留原样
    7. 合并
    """
    if not spec_raw:
        return ''
    
    # Step 1: 按换行符分割
    lines = str(spec_raw).split('\n')
    result_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Step 2: 冒号匹配 "参数名: 值" 或 "参数名：值"
        match = re.match(r'^([^:：]+)[:：]\s*(.+)$', line)
        if match:
            param_name = match.group(1).strip()
            param_value = match.group(2).strip()
            if param_name and param_value:
                # 检查value中是否还有 "参数名:" 模式（多个参数被空格分隔）
                if re.search(r'[\w\u4e00-\u9fff]+:', param_value):
                    # 用空格分割整个行
                    space_parts = re.split(r'\s+(?=[\w\u4e00-\u9fff]+:)', line)
                    for part in space_parts:
                        part = part.strip()
                        if not part:
                            continue
                        m = re.match(r'^([^:：]+)[:：]\s*(.+)$', part)
                        if m:
                            pn = m.group(1).strip()
                            pv = m.group(2).strip()
                            if pn and pv:
                                result_lines.append(f"{pn}: {pv}")
                    continue
                else:
                    result_lines.append(f"{param_name}: {param_value}")
                    continue
        
        # Step 3: 空格分隔 "参数名: 值 参数名: 值"
        space_parts = re.split(r'\s+(?=[\w\u4e00-\u9fff]+:)', line)
        if len(space_parts) > 1:
            for part in space_parts:
                part = part.strip()
                if not part:
                    continue
                match = re.match(r'^([^:：]+)[:：]\s*(.+)$', part)
                if match:
                    param_name = match.group(1).strip()
                    param_value = match.group(2).strip()
                    if param_name and param_value:
                        result_lines.append(f"{param_name}: {param_value}")
            # 如果成功分割，跳过原行
            if len([p for p in space_parts if p.strip()]) > 1:
                continue
        
        # Step 4: 空格分隔 (参数名 值,含数字+单位)
        # 条件: 行中包含至少一个数字 + 后面有单位
        has_number = re.search(r'\d', line)
        has_unit = any(u in line.upper() for u in [u.upper() for u in DEFAULT_SPEC_UNITS])
        
        if has_number and has_unit:
            # 尝试拆分: 取第一个词作为参数名,剩余作为值
            parts = line.split(None, 1)
            if len(parts) >= 2:
                param_name = parts[0].strip()
                param_value = parts[1].strip()
                # 修复: 参数名以数字开头 → 不是真正的参数名,保留原行
                if param_name and param_name[0].isdigit():
                    result_lines.append(line)
                    continue
                # 避免误拆纯描述(如"颜色可选")
                if len(param_value) > 2 or re.search(r'\d', param_value):
                    result_lines.append(f"{param_name}: {param_value}")
                    continue
        
        # Step 5: 自定义正则(从config)
        matched = False
        for pattern, param_name in SPEC_PATTERNS:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                param_value = match.group(1).strip()
                result_lines.append(f"{param_name}: {param_value}")
                matched = True
                break
        
        if matched:
            continue
        
        # Step 6: 剩余行保留原样
        result_lines.append(line)
    
    # Step 7: 合并
    result = '\n'.join(result_lines)
    
    # Step 8: 后处理清洗（标点统一、截断检测、空白填充等）
    from .spec_cleaner import clean_spec
    return clean_spec(result)


def split_spec_to_dict(spec_text: str) -> Dict[str, str]:
    """
    将spec文本拆分为字典
    输入: "长度: 1720mm; 宽度: 650mm; 重量: 85kg"
    或: "Motor: 4000W Battery: 72V 20AH"
    或: "功率 3000W 电压 72V"
    输出: {'长度': '1720mm', '宽度': '650mm', '重量': '85kg'}
    """
    result = {}
    if not spec_text:
        return result
    
    spec_text = str(spec_text).strip()
    if not spec_text:
        return result
    
    # 先按 ; 或 \n 分割
    parts = re.split(r'[;\n]', spec_text)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # 检查part中是否有多个 "参数名:值" 对（被空格分隔）
        # 例如 "Motor: 4000W Battery: 72V 20AH" → 切成 ["Motor: 4000W", "Battery: 72V 20AH"]
        sub_parts = re.split(r'\s+(?=[\w\u4e00-\u9fff]+:)', part)
        
        # 如果切成了多个子段，逐个处理
        if len(sub_parts) > 1:
            for sub in sub_parts:
                sub = sub.strip()
                if not sub:
                    continue
                match = re.match(r'^([^:：]+)[:：]\s*(.+)$', sub)
                if match:
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    if key and value:
                        result[key] = value
        else:
            # 单段，直接用 "参数名: 值" 匹配
            match = re.match(r'^([^:：]+)[:：]\s*(.+)$', part)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                if key and value:
                    result[key] = value
    
    # 如果以上都没找到，尝试 "参数名 值" 无冒号模式
    if not result:
        words = spec_text.split()
        temp_key = None
        temp_value = []
        for word in words:
            if ':' in word:
                if temp_key and temp_value:
                    result[temp_key] = ' '.join(temp_value)
                name_part = word.rstrip(':')
                if name_part:
                    temp_key = name_part
                    temp_value = []
            elif temp_key:
                temp_value.append(word)
                if re.search(r'\d', word):
                    for unit in DEFAULT_SPEC_UNITS:
                        if unit.lower() in word.lower():
                            result[temp_key] = ' '.join(temp_value)
                            temp_key = None
                            temp_value = []
                            break
        if temp_key and temp_value:
            result[temp_key] = ' '.join(temp_value)
    
    return result


def merge_spec_dict(spec_dict: Dict[str, str], join_char: str = '; ') -> str:
    """
    将字典合并为spec字符串
    输入: {'长度': '1720mm', '宽度': '650mm'}
    输出: "长度: 1720mm; 宽度: 650mm"
    """
    return join_char.join(f"{k}: {v}" for k, v in spec_dict.items())


def clean_spec_text(spec_text: str, max_length: int = 2000) -> str:
    """
    清理规格文本
    - 移除多余空白
    - 分号转换行 (更易读)
    - 截断超长部分
    """
    if not spec_text:
        return ''
    
    # 移除多余空白
    spec_text = re.sub(r'\n+', '\n', spec_text)
    spec_text = re.sub(r' +', ' ', spec_text)
    spec_text = re.sub(r'; +', ';', spec_text)
    
    # 分号转换行 - 使参数每行一个，易读
    spec_text = spec_text.replace('; ', ';\n')
    spec_text = spec_text.replace(';', ';\n')
    
    # 清理尾部换行
    spec_text = spec_text.strip()
    
    # 截断
    if len(spec_text) > max_length:
        spec_text = spec_text[:max_length] + '...'
    
    return spec_text


def batch_format_spec(spec_list: List[str]) -> List[str]:
    """批量格式化spec"""
    return [format_spec_spec(s) for s in spec_list]


def format_spec_wrapper(func):
    """装饰器: 为解析器函数的结果格式化spec"""
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        
        if result is not None and hasattr(result, 'apply'):
            # DataFrame
            if 'spec_zh' in result.columns:
                result['spec_zh'] = result['spec_zh'].apply(
                    lambda x: format_spec_spec(str(x)) if x else ''
                )
        
        return result
    
    return wrapper


# ==================== 测试 ====================

if __name__ == '__main__':
    test_cases = [
        "长度: 1720mm\n座高: 760mm\n重量: 85kg",
        "Motor: 4000W\nBattery: 72V 20AH\nController: 72V 30A",
        "功率 3000W 电压 72V",
        "颜色: 黑色\n规格: 标准配置\n可选颜色: 红/蓝/白",
    ]
    
    print("Spec Formatter 测试:")
    for tc in test_cases:
        result = format_spec_spec(tc)
        print(f"  Input: {tc!r}")
        print(f"  Output: {result!r}")
        print()