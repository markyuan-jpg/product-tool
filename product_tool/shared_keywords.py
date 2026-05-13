# -*- coding: utf-8 -*-
"""
跨解析器共享关键词常量。
三个解析器（Excel/PDF/DOCX）统一引用此文件，避免关键词四处散落。
"""

# ─── 列角色映射（Excel/DOCX/PDF 共用） ───

COLUMN_SIGNALS = {
    'name': ['产品名称', '产品名', '品名', '名称', '商品名', '产品', 'product',
             'name', 'description', '描述', '项目', '物料名称', '货物名称',
             '品名规格', '商品名称', '产品描述', '物料描述',
             'item description', 'goods name', 'article name', '产品说明'],
    'model': ['型号', '产品编号', '物料编码', '料号', '货号', '编码', '商品代码',
              'model', 'part no', 'p/n', 'product no', 'sku', 'item no',
              '款号', 'item code', 'reference no', 'product code',
              'material code', '规格型号', '品号',
              'oe no', 'oem no', 'replacement no',
              'catalog no', 'style no', 'style#'],
    'spec': ['规格', 'spec', 'specification', '参数', '型号规格', '尺寸', '材质', '配置',
             'description', '描述', 'specifications', '说明',
             '颜色', 'color', 'size', '尺码', '面料', '成分',
             'material', 'dimension', '功率', 'voltage', 'capacity',
             'purity', '纯度', '含量', '浓度', 'concentration',
             'surface', 'finish', '工艺', '表面处理',
             '重量', 'weight', 'g.w.', 'n.w.', '净重', '毛重',
             'gross weight', 'net weight', 'dimension', 'measurement',
             '色温', '流明', 'lumens', '灯头', '显指',
             '适用车型', 'application', '适用年龄', 'age range',
             '容量', 'capacity', 'voltage', 'current', '频率', 'frequency'],
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
                'carton size', '测量', 'meas', 'cbm', '体积', '外箱尺寸'],
    'remark': ['备注', 'remark', 'remarks', '条款', 'note', '说明', '附注'],
}

COLUMN_SIGNALS_FLAT = ['产品名称', '产品名', '品名', '名称', 'name', 'product',
                       '价格', '单价', 'price', '规格', 'spec', '型号', 'model',
                       '编码', 'qty', '数量', '包装', '备注', '尺寸', '照片', '图片',
                       '款号', '货号', '色号', 'sku', 'item no',
                       '颜色', 'color', '材质', 'material', '面料',
                       '功率', 'voltage', 'capacity', '净重', '毛重',
                       '单价', 'cost', 'rmb', 'fob', 'cif', 'exw',
                       '等级', 'grade', '类别', 'category']

SKIP_COLUMN_SIGNALS = ['serial', 'no.', 'image', 'picture', 'photo', '序号', '图片', '照片']

PRICE_KEYWORDS = ['价格', '单价', '出厂价', '系统价格', '成本价', '成本', '报价', '金额', '含税', '成本价',
                  'exw', 'fob', 'cif', '批发价', '市场价', '零售价',
                  'price', 'cost', 'rmb', '总价', '总金额', 'subtotal',
                  '成交价', '到厂价', 'unit price', 'selling price', 'export price',
                  'fca', 'ddp', 'cpt', 'cip', 'c&f', 'cfr',
                  '退税', '含税价', '不含税']

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
                      ]


# ─── 内容推断 spec 关键词 ───

CONTENT_SPEC_KEYWORDS = ['规格', '尺寸', '参数', '材质', '颜色', 'spec', 'size', 'color',
                         '面料', '成分', 'material', 'dimension', 'weight', '重量',
                         '色温', '流明', '功率', 'voltage', '容量', 'capacity',
                         '纯度', '含量', '浓度', '表面', 'finish', '工艺']
