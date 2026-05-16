# -*- coding: utf-8 -*-
"""
doc_shared.py — 文档生成器共享函数
跨 pi_generator / packing.generator / pdf_generator / quotation_excel 共用
"""
import re
from typing import List, Dict


def has_chinese(text: str) -> bool:
    """检测文本是否包含中文字符"""
    return any('\u4e00' <= c <= '\u9fff' for c in text)


def is_already_bilingual(text: str) -> bool:
    """检测文本是否已同时包含中文和英文（即已经是双语）"""
    if not text or not has_chinese(text):
        return False
    # 去掉中文后还有非空 ASCII 字符 → 包含英文
    non_cjk = re.sub(r'[\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]', '', text).strip()
    return len(non_cjk) > 0
    """检测文本是否包含中文字符"""
    return any('\u4e00' <= c <= '\u9fff' for c in text)


def filter_by_lang(text: str, lang: str) -> str:
    """按语言过滤文本，配合字典翻译兜底
    
    策略：
    1. 按行检测语言，保留匹配 lang 的行
    2. 如果过滤后全空，用字典翻译全文
    3. bilingual 模式不做过滤
    """
    if not text or lang == 'bilingual':
        return text
    
    lines = text.split('\n')
    filtered = [line.strip() for line in lines if line.strip() and (
        (lang == 'chinese' and has_chinese(line)) or
        (lang == 'english' and not has_chinese(line))
    )]
    
    if filtered:
        return '\n'.join(filtered)
    
    # 过滤后全空 → 用字典翻译兜底
    try:
        from src.utils.translator import translate_spec_safe
        mode = 'en_zh' if lang == 'chinese' else 'zh_en'
        translated = translate_spec_safe(text, mode)
        return translated or text
    except Exception:
        return text


def translate_items(items: List[Dict], lang: str) -> List[Dict]:
    """根据 lang 翻译/过滤产品数据（name_zh / spec_zh）"""
    if lang == 'bilingual':
        try:
            from src.utils.translator import bilingual_text, batch_translate
        except Exception:
            return items
        # 先收集所有需要翻译的文本，批处理一次
        names = [it.get('name_zh', '') for it in items if it.get('name_zh') and not is_already_bilingual(it['name_zh'])]
        specs = [it.get('spec_zh', '') for it in items if it.get('spec_zh') and not is_already_bilingual(it['spec_zh'])]
        name_map = batch_translate(names, 'zh_en')
        spec_map = batch_translate(specs, 'zh_en')
        result = []
        for item in items:
            item = dict(item)
            name = item.get('name_zh', '')
            spec = item.get('spec_zh', '')
            if name:
                if is_already_bilingual(name):
                    item['name_zh'] = name
                else:
                    item['name_zh'] = bilingual_text(name, name_map.get(name, ''))
            if spec:
                if is_already_bilingual(spec):
                    item['spec_zh'] = spec
                else:
                    item['spec_zh'] = bilingual_text(spec, spec_map.get(spec, ''))
            result.append(item)
        return result
    
    # Chinese / English 模式：过滤 + 字典翻译兜底
    result = []
    for item in items:
        item = dict(item)
        if item.get('name_zh'):
            item['name_zh'] = filter_by_lang(item['name_zh'], lang)
        if item.get('spec_zh'):
            item['spec_zh'] = filter_by_lang(item['spec_zh'], lang)
        result.append(item)
    return result


def payment_by_lang(text: str, lang: str) -> str:
    """双语付款条件按语言切分
    text 格式: '中文...  Terms of payment: ...'
    按 lang 返回对应语言部分：
      chinese  → 仅中文
      english  → 仅英文
      bilingual / 其他 → 完整双语文案
    """
    if not text:
        return text
    # 处理大小写变体
    import re
    m = re.split(r'(?:Terms?\s*of\s*payment|Payment\s*Terms?)\s*:', text, maxsplit=1, flags=re.I)
    if len(m) > 1:
        zh_part = m[0].strip()
        en_part = ('Terms of payment: ' + m[1].strip()).strip()
    else:
        zh_part = text
        en_part = ''
    if lang == 'chinese':
        return zh_part
    elif lang == 'english':
        return en_part if en_part else text
    else:  # bilingual
        return text


def get_seller_info(seller_config: dict = None) -> dict:
    """从配置获取卖家信息，支持扁平key(web模板)和嵌套bank(company.py)两种格式"""
    if not seller_config:
        try:
            from src.company import load_company
            seller_config = load_company()
        except Exception:
            seller_config = {}
    bank = seller_config.get('bank', {})
    return {
        'company': seller_config.get('name_en', '') or seller_config.get('name', '')
                   or seller_config.get('company', '') or seller_config.get('company_name', '') or 'XXXXX',
        'address': seller_config.get('address_en', '') or seller_config.get('address', '') or 'XXXXX',
        'contact': seller_config.get('contact_person', '') or seller_config.get('contact', '') or 'XXXXX',
        'phone': seller_config.get('tel', '') or seller_config.get('phone', '') or 'XXXXX',
        'bank_beneficiary': seller_config.get('bank_beneficiary', '') or bank.get('beneficiary', '') or 'XXXXX',
        'bank_name': seller_config.get('bank_name', '') or bank.get('bank_name', '') or 'XXXXX',
        'bank_address': seller_config.get('bank_address', '') or bank.get('bank_address', '') or 'XXXXX',
        'bank_account': seller_config.get('bank_account', '') or bank.get('account_no', '') or 'XXXXX',
        'bank_swift': seller_config.get('bank_swift', '') or bank.get('swift_code', '') or 'XXXXX',
    }
