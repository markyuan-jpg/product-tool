# -*- coding: utf-8 -*-
"""
Spec Cleaner - 规格清洗后处理器

在格式化的spec输出前执行：
1. 标点统一（全角→半角冒号、分号）
2. 自动换行（在参数名前插入换行）
3. 截断检测（检测不完整的规格文本）
4. 空白填充（空规格时返回默认文本）
"""
import re
from typing import Optional

DEFAULT_SPEC_TEXT = "Standard configuration. Contact us for details."

# 截断检测规则: (pattern, marker)
# 按优先级排序：数字+星号必须在普通星号之前
TRUNCATION_RULES = [
    (r'\d+\*\s*$', '(尺寸单位缺失)'),  # "1360*" → size unit missing
    (r'\*\s*$', '(may be incomplete)'),
    (r'-\s+$', '(may be incomplete)'),
    (r'[:：]\s*$', '(may be incomplete)'),
    (r',\s*$', '(may be incomplete)'),
]

SAFE_WORDS = frozenset({
    'the', 'and', 'for', 'box', 'set', 'pcs', 'pc', 'kg', 'mm', 'cm',
    'in', 'ft', 'v', 'a', 'w', 'kw', 'ah', 'mah', 'rpm', 'km', 'lb',
})

# 可识别的参数名前缀（用于换行判断）
PARAM_PREFIXES = [
    'Motor', 'Battery', 'Controller', 'Speed', 'Range',
    'Dimension', 'Weight', 'Power', 'Voltage', 'Current',
    'Charging', 'Headlight', 'Brake', 'Tyre', 'Shock',
    'Wheelbase', 'Material', 'Color', 'Size', 'Package',
    'Gross', 'Net', 'PCS', 'FR', 'RR', 'Front', 'Rear',
    '电机', '电池', '控制器', '速度', '里程', '功率',
    '电压', '电流', '尺寸', '重量', '材质', '颜色',
    '刹车', '轮胎', '减震', '轴距', '离地', '包装',
    '充电', '大灯', '仪表', '报警',
]


# 字段名别名映射（从供应商原始数据提取 → 标准名称）
FIELD_NAME_ALIASES = {
    "Motorcycle Brand Name": "Brand Name",
}

def normalize_field_names(text: str) -> str:
    """统一字段名：按 FIELD_NAME_ALIASES 映射替换"""
    if not text:
        return text
    for old, new in FIELD_NAME_ALIASES.items():
        text = text.replace(old, new)
    return text


def normalize_punctuation(text: str) -> str:
    """统一标点为半角：全角冒号/分号 → 半角，清除双冒号"""
    if not text:
        return text
    text = text.replace('\uff1a', ':')  # ：→ :
    text = text.replace('\uff1b', ';')  # ；→ ;
    text = text.replace('：:', ':')     # 全+半双冒号 → :
    text = text.replace('::', ':')      # 双冒号 → :（保留后面内容）
    text = text.replace(': :', ': ')    # 冒号空格冒号 → 冒号空格
    return text


def inject_linebreaks(text: str) -> str:
    """
    在参数名前插入换行，避免多个参数挤在一行。
    
    输入: "Motor: 4000W Battery: 72V"
    输出: "Motor: 4000W\nBattery: 72V"
    
    策略：只在前一个参数已有冒号时才插入换行。
    这避免了误拆多词参数名（"Package size:"、"USB Port:"）。
    """
    if not text or '\n' in text:
        return text
    
    # 按空格分词，逐个检查
    words = text.split()
    result = []
    found_colon = False
    
    for w in words:
        # 检查这个词是否是 "参数名:" 格式
        is_new_param = False
        colon_at = -1
        for sep in (':', '：'):
            idx = w.find(sep)
            if idx > 0:
                colon_at = idx
                break
        
        if colon_at > 0 and found_colon:
            name_part = w[:colon_at]
            # 参数名以字母或中文开头 → 新参数（不区分大小写，修复 "length:" / "colour:" 等小写参数名）
            if name_part and (name_part[0].isalpha() or '\u4e00' <= name_part[0] <= '\u9fff'):
                is_new_param = True
        
        if is_new_param:
            result.append('\n' + w)
        else:
            if result:
                result.append(' ' + w)
            else:
                result.append(w)
        
        if colon_at > 0:
            found_colon = True
    
    return ''.join(result)


def fix_truncated_spec(text: str) -> str:
    """
    检测截断：按规则匹配并追加对应标记。
    对长文本（>60字）额外检测末尾短词是否可能是截断。
    """
    if not text or len(text) < 3:
        return text
    
    # 1) 规则匹配：不同模式追加不同标记
    for pattern, marker in TRUNCATION_RULES:
        if re.search(pattern, text):
            if not text.endswith(marker):
                text = text + ' ' + marker
            return text
    
    # 2) 长文本短词检测：文本末尾若有空白，最后单词为1-3字符且不在安全词中 → 可能截断
    if len(text) > 60 and re.search(r'\s+$', text):
        stripped = text.rstrip()
        if stripped:
            last_word = stripped.split()[-1]
            if 1 <= len(last_word) <= 3 and last_word.lower() not in SAFE_WORDS:
                if not text.endswith('(may be incomplete)'):
                    text = text + ' (may be incomplete)'
    
    return text


def fill_empty_spec(text: Optional[str]) -> str:
    """空规格填充默认文本"""
    if not text:
        return DEFAULT_SPEC_TEXT
    t = str(text).strip()
    if not t or t.lower() in ('', 'nan', 'none'):
        return DEFAULT_SPEC_TEXT
    return t


def clean_spec(spec_raw: Optional[str]) -> str:
    """统一入口：依次执行所有清洗步骤"""
    if not spec_raw:
        return fill_empty_spec(spec_raw)
    
    text = str(spec_raw).strip()
    if not text or text.lower() in ('nan', 'none'):
        return DEFAULT_SPEC_TEXT
    
    text = normalize_punctuation(text)
    text = normalize_field_names(text)
    # 分号转换行: 只在 "值; 参数名" 上下文替换（不拆分值内的分号如 "2.50-17;2.75-17"）
    text = re.sub(r';\s*(?=[A-Z\u4e00-\u9fff])', '\n', text)
    text = text.rstrip(';')
    text = inject_linebreaks(text)
    text = fix_truncated_spec(text)
    # 清除每行首尾空格，去掉所有空行（包括单行空白）
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    return text


def normalize_spec(text: Optional[str]) -> str:
    """Unified spec text processing entry: clean + format + truncation detection"""
    return clean_spec(text)
