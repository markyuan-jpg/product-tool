# -*- coding: utf-8 -*-
"""
全局配置
集中管理所有配置常量
"""
import os

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
TEMP_DIR = os.path.join(BASE_DIR, 'temp_images')

# Excel 列关键词
COLUMN_KEYWORDS = {
    'price': ['价格', 'price', 'rmb', '/pc', '元', '单价'],
    'spec': ['规格', 'spec', '参数', 'description', '描述'],
    'name': ['名称', 'name', '品名', 'product', '产品'],
    'model': ['型号', 'model', 'item', '编号', 'no.', 'code', 'sku'],
}

# 图片文件夹
IMAGE_FOLDERS = ['images', 'imgs', 'pics', 'img', 'photos']
IMAGE_EXTS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

# ==================== 表头检测 ====================

# 表头关键词
HEADER_KEYWORDS = [
    '型号', 'model', '名称', 'name', '规格', 'spec', '参数',
    '价格', 'price', '售价', '报价', '单价',
    '单位', 'unit', '数量', 'quantity', 'qty',
    '包装', 'packing', 'description', '描述'
]

# 公司关键词 (剔除表头行)
COMPANY_KEYWORDS = [
    '有限公司', 'co.', 'ltd', 'tel:', 'email:', 'quotation', '报价单'
]

# ==================== 列检测 ====================

# 型号特征正则
MODEL_PATTERN = r'^[A-Z0-9]{2,}$|^[A-Z]{2,}-\d+|^[A-Z]{1,3}[\-\d]+'

# 名称关键词
NAME_KEYWORDS = ['产品名称', '品名', '名称', 'product name', 'description', '商品']

# 规格关键词
SPEC_KEYWORDS = ['规格', 'spec', '参数', 'description', '产品描述', 'specification']

# ==================== 价格清洗 ====================

# 价格范围 (人民币)
MIN_PRICE = 0.01
MAX_PRICE = 100000

# 空行阈值
EMPTY_ROW_THRESHOLD = 3

# ==================== Spec格式化 ====================

# 规格单位
SPEC_UNITS = [
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

# 自定义正则规则
SPEC_PATTERNS = [
    # (pattern, param_name)
]

# 文件监听
WATCH_EXTENSIONS = ('.xlsx', '.xls', '.docx')
WATCH_DEBOUNCE = 1.0

# LLM配置
LLM_MODEL = 'llama3'
LLM_BASE_URL = 'http://localhost:11434'
LLM_MAX_TOKENS = 8000

# 分类配置
CATEGORIES_FILE = 'categories.json'

# 输出样式
STYLE_CONFIG = {
    'header_bg': '366092',
    'header_font': 'FFFFFF',
    'row_even': 'F2F2F2',
    'row_odd': 'FFFFFF',
}

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# 默认卖家信息 (PI/报价单用)
DEFAULT_SELLER_INFO = {
    'company': 'Your Company Name',
    'address': 'Your Address',
    'contact': 'Sales Department',
    'phone': '+86-000-00000000',
    'email': 'sales@company.com',
    'bank_info': 'Bank: XXX Bank, Account: XXXX-XXXX-XXXX-XXXX',
}