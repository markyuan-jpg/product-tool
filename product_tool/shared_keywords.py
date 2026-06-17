# -*- coding: utf-8 -*-
"""
跨解析器共享关键词常量。
三个解析器（Excel/PDF/DOCX）统一引用此文件，避免关键词四处散落。
"""

# ─── 列角色映射（Excel/DOCX/PDF 共用） ───

COLUMN_SIGNALS = {
    'name': ['产品名称', '产品名', '品名', '名称', '商品名', '产品', 'product',
             'name', '项目', '物料名称', '货物名称',
             '品名规格', '商品名称', '产品描述', '物料描述',
             'item description', 'goods name', 'article name'],
    'model': ['型号', '产品编号', '物料编码', '料号', '货号', '编码', '商品代码',
              'model', 'part no', 'p/n', 'product no', 'sku', 'item no',
              '款号', 'item code', 'reference no', 'product code',
              'material code', '规格型号', '品号',
              'oe no', 'oem no', 'replacement no',
              'catalog no', 'style no', 'style#'],
    'spec': ['规格', 'spec', 'specification', '参数', '尺寸', '材质', '配置',
             'description', '描述', 'specifications',
             '颜色', 'color', 'size', '尺码', '面料', '成分',
             'material', 'dimension', '功率', 'voltage', 'capacity',
             'purity', '纯度', '含量', '浓度', 'concentration',
             'surface', 'finish', '工艺', '表面处理',
             '色温', '流明', 'lumens', '灯头', '显指',
             '适用车型', 'application', '适用年龄', 'age range',
             '容量', 'voltage', 'current', '频率', 'frequency',
             '产品说明', 'detail', 'details',  '参数表', '技术参数',
             '产品参数', '性能参数', '规格参数', '主要规格', 'technical specification'],
    'category': ['类别', '产别', 'type', '种类', '分类', 'category', 'grade', '等级'],
    'price': ['价格', '单价', '出厂价', '系统价格', '成本价', '成本', '报价', '金额', '含税', '成本价',
              'exw', 'fob', 'cif', '批发价', '市场价', '零售价',
              'price', 'cost', 'rmb', '总价', '总金额', 'subtotal',
              '成交价', '到厂价', 'unit price', 'selling price', 'export price',
              'fca', 'ddp', 'cpt', 'cip', 'c&f', 'cfr',
              '退税', '含税价', '不含税'],
    'qty': ['数量', '订货量', '起订量', 'qty', 'quantity', '数量',
            'pcs', 'sets', 'pair', '件', '套', '双',
            'pack qty', '数量/箱', '装箱数', '每箱数量',
            '净含量', 'net weight', 'n.w.', '每箱', 'pcs/ctn'],
    'packing': ['包装', '内盒', '外箱', '每箱', 'packing', 'package', '装箱明细', 'packing list',
                'carton size', '测量', 'meas', 'cbm', '体积', '外箱尺寸',
                'carton', 'ctn', '箱规', '装箱', 'pack qty', '每箱数量', 'qty/ctn', 'pcs/ctn',
                '每箱重量', '体积重', '包装尺寸', 'packing size',
                '重量', 'weight', 'g.w.', 'n.w.', '净重', '毛重',
                'gross weight', 'net weight', 'dimension', 'measurement',
                'units per carton', 'carton weight'],
    'remark': ['备注', 'remark', 'remarks', '条款', 'note', '说明', '附注'],
}

COLUMN_SIGNALS_FLAT = ['产品名称', '产品名', '品名', '名称', 'name', 'product',
                       '价格', '单价', 'price', '规格', 'spec', '型号', 'model',
                       '编码', 'qty', '数量', '包装', '备注', '尺寸', '照片', '图片',
                       '款号', '货号', '色号', 'sku', 'item no',
                       '颜色', 'color', '材质', 'material', '面料',
                       '功率', 'voltage', 'capacity',
                       '单价', 'cost', 'rmb', 'fob', 'cif', 'exw',
                       '等级', 'grade', '类别', 'category',
                       '箱规', '装箱', 'carton', '每箱', 'packing', 'cbm']

SKIP_COLUMN_SIGNALS = ['serial no', 'sr.no', 'serial', 'image', 'picture', 'photo', '序号', '图片', '照片']

PRICE_KEYWORDS = ['价格', '单价', '出厂价', '系统价格', '成本价', '成本', '报价', '金额', '含税', '成本价',
                   'exw', 'fob', 'cif', '批发价', '市场价', '零售价',
                   'price', 'cost', 'rmb', '总价', '总金额', 'subtotal',
                   '成交价', '到厂价', 'unit price', 'selling price', 'export price',
                   'fca', 'ddp', 'cpt', 'cip', 'c&f', 'cfr',
                   '退税', '含税价', '不含税', 'usd', '$', 'cny', '¥']

SKIP_HEADER_KEYWORDS = ['公司', '地址', '电话', '联系人', 'mail', 'website', '供应商', 'supplier',
                        'tel', 'fax', 'add', 'buyer', 'consignee', 'shipper', 'invoice', 'date',
                        'shipment', 'delivery', 'payment', '信用证', 'l/c', 't/t',
                        'shipping mark', '唛头', 'mark', '合同', 'contract', 'po', 'order',
                        '有效期', 'validity', 'offer valid', 'valid until',
                        '检验', 'inspection', 'test report', '质检', 'quality',
                        'loading port', 'port of loading', 'port of discharge',
                        '装运港', '目的港', '船期', '原产地', 'certificate', '产地证',
                        'oem', 'customized', '定制', 'logo']


# ─── DOCX 表头检测关键词 ───

DOCX_HEADER_KEYWORDS = ['型号', 'model', 'item', '产品', '名称', '品名', 'goods',
                        'price', '价格', '单价', '规格', 'spec', '参数', '数量', 'qty',
                        'sku', '货号', '款号', 'product', 'description',
                        '尺寸', 'size', 'color', '颜色', '材质', 'material',
                        '重量', 'weight', '功率', 'voltage', 'capacity',
                        '总额', '金额', 'cost', 'rmb', 'fob', 'cif', 'exw',
                        '包装', 'packing', 'qty/ctn', '每箱']


# ─── PDF 布局检测关键词 ───

PDF_MODEL_KEYWORDS = {'model', '型号', 'item', 'name', 'product', '产品', '名称', '品名', 'sku'}
PDF_PARAM_KEYWORDS = {'motor', 'battery', 'weight', 'speed', 'dimension', 'wheelbase',
                      'tire', 'tyre', 'brake', 'material', 'color', 'length', 'width',
                      'height', 'power', 'voltage', 'current', 'torque', 'range',
                      '规格', '参数', '材质', '颜色', '尺寸', '型号',
                      '马达', '电机', '电池', '重量', '速度', '刹车'}
PDF_SKIP_COLUMN_KEYWORDS = ['serial', 'no.', '序号', 'image', 'picture', 'photo', '图片', '备注', 'remark']
PDF_PACKAGING_KEYWORDS = {
    'gw', 'nw', 'g.w.', 'n.w.', 'gross weight', 'net weight',
    'gross', 'net', 'carton size', 'carton', 'package size',
    'packing size', 'cbm', 'meas', 'measurement',
    'qty/ctn', 'pcs/ctn', '每箱数量', '毛重', '净重', '外箱尺寸',
    '包装尺寸', '体积', 'cartons', '包装', '测量',
}
PDF_PACKAGING_CONTENT_KEYWORDS = {'carton', 'box', 'package', 'packing', 'ctn', '箱', '包', '袋'}


# ─── 产品名跳过词（_is_product_row 用） ───

PRODUCT_SKIP_WORDS = ['条款', '备注', '说明', '合计', 'total', 'subtotal',
                      '小计', '汇总', '总计',
                      '报关', '合同', 'header', 'price term', 'warranty', 'oem', 'validity',
                      'shipment', 'delivery', 'payment', '信用证', 'l/c', 't/t',
                      '唛头', 'mark', 'shipping mark',
                      '检验', 'inspection', 'test', '质检', 'quality report',
                      '有效期', 'offer valid', 'valid until',
                      '合同', 'contract', 'po', 'order',
                      'loading', 'discharge', 'port',
                      'certificate', '产地证', '原产地',
                      'customized', '定制', 'logo',
                      # 定价条款（避免 "50件以下...包邮" 被误判为产品）
                      '包邮', '执行', '经销价',
                      '件以下', '件起', '非偏远',
                      '系统价格', '零售价', '批发价',
                      '不含税', '含税价',
                      '偏远地区',
                      'total amount', 'grand total', '总计金额', '合计金额',
                      ]


# ─── 内容推断 spec 关键词 ───

CONTENT_SPEC_KEYWORDS = ['规格', '尺寸', '参数', '材质', '颜色', 'spec', 'size', 'color',
                         '面料', '成分', 'material', 'dimension', '重量',
                         '色温', '流明', '功率', 'voltage', '容量', 'capacity',
                          '纯度', '含量', '浓度', '表面', 'finish', '工艺',
                          '毛重', '净重', 'carton', 'packing', '每箱']


# ═══════════════════════════════════════════════════════════════
# 统一非产品行过滤模式 — universal_parser + excel_parser_v3 共用
# 由 build_non_product_patterns() 生成编译后的正则列表
# ═══════════════════════════════════════════════════════════════

_NON_PRODUCT_RAW_PATTERNS = [
    # English field labels
    r'^(contract|seller|buyer|payment|shipping|delivery|transshipment|remarks?|note|terms|conditions?|address|tel[.:\s]|fax[.:\s]|email|phone|website|bank|account|beneficiary|swift|contact|signature|date|invoice|validity|description)',
    # Totals
    r'^(total\s+amount|total\s+payment|grand\s+total|sub\s*total|total\s*[:：]|总计金额|合计金额)',
    # Numbered clauses (English)
    r'^\d+[.、\s]\s*(transshipment|payment|delivery|packing|insurance|bank|inspection|arbitration|force\s*majeure|shipping|terms?|conditions?|warranty|validity|quality|port|brand|motorcycle|e[\-\s]?bike|destination|notice|handling)',
    # Chinese field labels
    r'^(合同|卖方|买方|付款|交货|运输|包装|条款|备注|说明|地址|电话|邮箱|日期|受益|银行|账户|签名|签字|合计|总计|金额|小计|编号|序号)',
    # Bare price/currency
    r'^(\u00a5|\$|eur|usd|cny)\s*[\d,]+',
    # Company info
    r'^(company|supplier|customer|buyer|seller)(\s|$)',
    # Chinese numbered clauses
    r'^\d+[.、]\s*[（(]?\s*(本合|支付|交[货付]|运[输送]|包[装]|条[款]|备[注]|说[明]|地[址]|电[话]|日[期]|银[行]|账[户]|签[名字]|仲裁|保险)',
    # Document titles
    r'^(proforma\s+invoice|sales\s+contract|to\s*:|the\s+(seller|buyer)|sign(ed|ature)|date\s+of\s+)',
    r'^total\s+payment',
    # Port/brand/handling clauses
    r'^\d+[.、]\s*(port\s+of|brand\s+name|handling\s+method|other\s+notices|motorcycle\s+brand)',
    # Signature/stamp lines
    r'^(\(signed|\(stamp|\(seal|signature\s+by|authorized\s+sign)',
    r'^(sign(ed|ature)?|approv(ed|al)?|authoriz(ed|ation)?|seal|stamp|公章|签字|签名|盖章|审批)',
    # Doc/order reference numbers
    r'^(contract\s*no|order\s*no|po\s*no|invoice\s*no|ref\s*no|payment\s*no|shipment\s*no|delivery\s*no|doc\s*no|quotation\s*no|quote\s*no)\s*[:\-.]?\s*[\w\-]+',
    r'^(PO|SO|CO|DO|WO|IV|INV|CT|CN|QT|RFQ|PI|DN|GRN)[\d\-]{8,20}$',
    # Packing list headers
    r'^(packing\s*(list|detail|info)|装箱(单|明细|清单))',
    # Notification/declaration
    r'^(notify\s+party|consignee|carrier|forwarder|agent)',
    # Quality/test reports
    r'^(test\s+report|inspection\s+report|certificate\s+of)',
    # Unit of measure
    r'^(unit\s+(of|in)|uom|计量单位|单位[：:])',
    # Country of origin / manufacturer
    r'^(country\s+of\s+origin|made\s+in|原产地|manufacturer)',
    # Legal/business clauses
    r'^(仲裁|保险|商检|产地证|原产地|信用证|l/?c|t/?t|不可抗力)',
    # Auto-generated model placeholders
    r'^(产品_r\d+|商品_×\d+)$',
]

import re as _re

def build_non_product_patterns():
    """返回编译后的非产品行过滤正则列表"""
    return [_re.compile(p, _re.I) for p in _NON_PRODUCT_RAW_PATTERNS]

# 预编译（模块加载时）
NON_PRODUCT_PATTERNS = build_non_product_patterns()
