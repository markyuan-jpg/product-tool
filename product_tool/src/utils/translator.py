# -*- coding: utf-8 -*-
"""
简单多语言翻译 - 规则替换版
"""
import pandas as pd
from typing import Dict, Optional

# 中英对照词典
DICT_ZH_EN = {
    # 产品字段
    '型号': 'Model',
    '名称': 'Name',
    '品名': 'Product Name',
    '产品名称': 'Product Name',
    '规格': 'Specification',
    '规格参数': 'Specifications',
    '参数': 'Parameters',
    '价格': 'Price',
    '单价': 'Unit Price',
    '人民币': 'RMB',
    '产地': 'Origin',
    '品牌': 'Brand',
    '材质': 'Material',
    '铝合金': 'Aluminum Alloy',
    '铝合金框': 'Aluminum Alloy Frame',
    '不锈钢': 'Stainless Steel',
    '碳钢': 'Carbon Steel',
    '塑料': 'Plastic',
    '橡胶': 'Rubber',
    '硅胶': 'Silicone',
    '玻璃': 'Glass',
    '木材': 'Wood',
    '皮革': 'Leather',
    '面料': 'Fabric',
    '金属': 'Metal',
    '铁': 'Iron',
    '铜': 'Copper',
    '铝': 'Aluminum',
    '颜色': 'Color',
    '红色': 'Red',
    '蓝色': 'Blue',
    '绿色': 'Green',
    '白色': 'White',
    '黑色': 'Black',
    '灰色': 'Gray',
    '黄色': 'Yellow',
    '橙色': 'Orange',
    '银色': 'Silver',
    '金色': 'Gold',
    '尺寸': 'Size',
    '外形尺寸': 'Overall Dimension',
    '重量': 'Weight',
    '包装': 'Packaging',
    '包装方式': 'Packaging',
    '箱规': 'Carton Size',
    '数量': 'Quantity',
    '备注': 'Remarks',
    '描述': 'Description',
    '产品描述': 'Description',
    '说明': 'Note',
    '配置': 'Configuration',

    # 公司信息
    '公司': 'Company',
    '公司名称': 'Company Name',
    '联系人': 'Contact',
    '电话': 'Tel',
    '邮箱': 'Email',
    '地址': 'Address',
    '传真': 'Fax',
    '网址': 'Website',
    '供应商': 'Supplier',
    '生产商': 'Manufacturer',
    '制造商': 'Manufacturer',
    '客户': 'Customer',

    # 认证
    'CE': 'CE',
    'FDA': 'FDA',
    'ISO': 'ISO',
    '认证': 'Certification',
    '证书': 'Certificate',

    # 日期
    '日期': 'Date',
    '编号': 'No.',
    '序号': 'No.',
    '优惠': 'Discount',

    # === 电池/电气 ===
    '电池': 'Battery',
    '锂电池': 'Lithium Battery',
    '铅酸电池': 'Lead-Acid Battery',
    '磷酸铁锂电池': 'LiFePO4 Battery',
    '电池类型': 'Battery Type',
    '电池容量': 'Battery Capacity',
    '电压': 'Voltage',
    '额定电压': 'Rated Voltage',
    '工作电压': 'Working Voltage',
    '充电电压': 'Charging Voltage',
    '电流': 'Current',
    '充电电流': 'Charging Current',
    '工作电流': 'Working Current',
    '功率': 'Power',
    '额定功率': 'Rated Power',
    '最大功率': 'Max Power',
    '峰值功率': 'Peak Power',
    '电机功率': 'Motor Power',
    '容量': 'Capacity',
    '充电器': 'Charger',
    '充电时间': 'Charging Time',
    '续航': 'Range',
    '续航里程': 'Mileage Range',
    '电机': 'Motor',
    '电机类型': 'Motor Type',
    '无刷电机': 'Brushless Motor',
    '轮毂电机': 'Hub Motor',
    '中置电机': 'Mid Drive Motor',
    '控制器': 'Controller',
    '频率': 'Frequency',
    '扭矩': 'Torque',
    '转速': 'RPM',

    # === 车辆 ===
    '电动摩托车': 'Electric Motorcycle',
    '电动自行车': 'Electric Bicycle',
    '电动滑板车': 'Electric Scooter',
    '摩托车': 'Motorcycle',
    '自行车': 'Bicycle',
    '轮胎': 'Tire',
    '轮胎尺寸': 'Tire Size',
    '前轮胎': 'Front Tire',
    '后轮胎': 'Rear Tire',
    '刹车': 'Brake',
    '制动': 'Brake',
    '制动系统': 'Braking System',
    '刹车系统': 'Brake System',
    '前刹车': 'Front Brake',
    '后刹车': 'Rear Brake',
    '碟刹': 'Disc Brake',
    '鼓刹': 'Drum Brake',
    '速度': 'Speed',
    '最大速度': 'Max Speed',
    '最高速度': 'Max Speed',
    '经济速度': 'Economic Speed',
    '载重': 'Load Capacity',
    '最大载重': 'Max Load',
    '载荷': 'Load',
    '车架': 'Frame',
    '前叉': 'Front Fork',
    '后叉': 'Rear Fork',
    '减震': 'Shock Absorber',
    '前减震': 'Front Suspension',
    '后减震': 'Rear Suspension',
    '悬挂': 'Suspension',
    '灯光': 'Light',
    '前灯': 'Headlight',
    '大灯': 'Headlight',
    '尾灯': 'Tail Light',
    '转向灯': 'Turn Signal',
    '刹车灯': 'Brake Light',
    '仪表': 'Instrument',
    '仪表盘': 'Dashboard',
    '显示屏': 'Display',
    '座位': 'Seat',
    '座高': 'Seat Height',
    '座椅': 'Seat',
    '踏板': 'Footrest',
    '脚蹬': 'Pedal',
    '链条': 'Chain',
    '皮带': 'Belt',
    '喇叭': 'Horn',
    '报警器': 'Alarm',
    '后视镜': 'Rearview Mirror',
    '挡泥板': 'Fender',
    '货架': 'Rack',
    '边撑': 'Side Stand',
    '主支架': 'Main Stand',
    '爬坡能力': 'Climbing Ability',
    '轴距': 'Wheelbase',
    '离地间隙': 'Ground Clearance',

    # === 通用测量 ===
    '毫米': 'mm',
    '厘米': 'cm',
    '分米': 'dm',
    '米': 'm',
    '千米': 'km',
    '英寸': 'inch',
    '英尺': 'ft',
    '千克': 'kg',
    '公斤': 'kg',
    '克': 'g',
    '毫克': 'mg',
    '吨': 'ton',
    '磅': 'lb',
    '盎司': 'oz',
    '升': 'L',
    '毫升': 'ml',
    '加仑': 'gal',
    '伏': 'V',
    '安': 'A',
    '毫安': 'mA',
    '瓦': 'W',
    '千瓦': 'kW',
    '千瓦时': 'kWh',
    '毫安时': 'mAh',
    '安时': 'Ah',
    '瓦时': 'Wh',
    '赫兹': 'Hz',
    '牛米': 'N.m',
    '千米/小时': 'km/h',
    '公里/小时': 'km/h',
    '度': '°',

    # === 时间 ===
    '年': 'Year',
    '月': 'Month',
    '星期': 'Week',
    '天': 'Day',
    '小时': 'h',
    '分钟': 'min',
    '秒': 's',

    # === 贸易 ===
    'FOB价格': 'FOB Price',
    'FOB 价格': 'FOB Price',
    '出厂价': 'EXW Price',
    'EXW价格': 'EXW Price',
    '成本价': 'Cost Price',
    '批发价': 'Wholesale Price',
    '零售价': 'Retail Price',
    '总价': 'Total Amount',
    '总金额': 'Total Amount',
    '小计': 'Subtotal',
    '付款': 'Payment',
    '付款方式': 'Payment Terms',
    '发货': 'Delivery',
    '运输': 'Shipping',
    '海运': 'Sea Freight',
    '空运': 'Air Freight',
    '陆运': 'Land Transport',
    '毛重': 'Gross Weight',
    '净重': 'Net Weight',
    '库存': 'Stock',
    '现货': 'In Stock',
    '定制': 'Customized',
    '样品': 'Sample',
    '样品费': 'Sample Fee',
    '定金': 'Deposit',
    '尾款': 'Balance Payment',
    '港口': 'Port',
    '装运港': 'Port of Loading',
    '交期': 'Lead Time',
    '交货期': 'Delivery Time',
    '生产周期': 'Production Time',
    '贸易条款': 'Trade Terms',
    '有效期': 'Validity',

    # === 通用属性 ===
    '是': 'Yes',
    '否': 'No',
    '有': 'With',
    '无': 'Without',
    '含': 'Including',
    '不含': 'Excluding',
    '标准': 'Standard',
    '可选': 'Optional',
    '防水': 'Waterproof',
    '防尘': 'Dustproof',
    '智能': 'Smart',
    '电动': 'Electric',
    '自动': 'Automatic',
    '手动': 'Manual',
    '单速': 'Single Speed',
    '变速': 'Variable Speed',
    '前进': 'Forward',
    '后退': 'Reverse',
    '高': 'High',
    '中': 'Medium',
    '低': 'Low',
    '大': 'Large',
    '小': 'Small',
    '长': 'Length',
    '宽': 'Width',
    '高': 'Height',
    '厚': 'Thickness',
    '直径': 'Diameter',
    '输入': 'Input',
    '输出': 'Output',
    '最大': 'Max',
    '最小': 'Min',
    '额定': 'Rated',
    '平均': 'Average',
}

DICT_EN_ZH = {v: k for k, v in DICT_ZH_EN.items()}


_TRANSLATE_CACHE = {}

def translate_text(text: str, mode: str = 'zh_en') -> str:
    """翻译单个文本（带结果缓存）"""
    if not text:
        return text
    cache_key = (text, mode)
    if cache_key in _TRANSLATE_CACHE:
        return _TRANSLATE_CACHE[cache_key]

    dict_map = DICT_ZH_EN if mode == 'zh_en' else DICT_EN_ZH

    # 按key长度降序排列,避免"锂电池"被"电池"部分替换
    for src, dst in sorted(dict_map.items(), key=lambda x: len(x[0]), reverse=True):
        if src in str(text):
            text = text.replace(src, dst)

    _TRANSLATE_CACHE[cache_key] = text
    return text


def batch_translate(texts: list, mode: str = 'zh_en') -> dict:
    """批量翻译，返回 {原文: 译文} 映射（自动去重 + 缓存复用）"""
    if not texts:
        return {}
    unique = list(dict.fromkeys(texts))  # 去重保序
    result = {}
    for t in unique:
        result[t] = translate_text(t, mode)
    return result


def translate_row(row: dict, mode: str = 'zh_en') -> dict:
    """翻译整行"""
    result = {}
    for key, value in row.items():
        if isinstance(value, str):
            result[key] = translate_text(value, mode)
        else:
            result[key] = value

    # 翻译key
    result_new = {}
    for key, value in result.items():
        new_key = translate_text(key, mode)
        result_new[new_key] = value

    return result_new


def translate_dataframe(df: pd.DataFrame, mode: str = 'zh_en') -> pd.DataFrame:
    """翻译整个DataFrame"""
    # 翻译列名
    df_new = df.copy()
    df_new.columns = [translate_text(col, mode) for col in df_new.columns]

    # 翻译数据
    for col in df_new.columns:
        if df_new[col].dtype == 'object':
            df_new[col] = df_new[col].apply(lambda x: translate_text(str(x), mode) if pd.notna(x) else x)

    return df_new


def translate_file(input_path: str, output_path: str = None, mode: str = 'zh_en') -> str:
    """翻译文件"""
    if output_path is None:
        if input_path.endswith('.csv'):
            output_path = input_path.replace('.csv', f'_{mode}.csv')
        else:
            output_path = input_path + f'_{mode}'

    df = pd.read_csv(input_path)
    df_translated = translate_dataframe(df, mode)
    df_translated.to_csv(output_path, index=False, encoding='utf-8-sig')

    return output_path


# ─── 文档专用中英对照（标题、表头、条款等固定文本） ───
DOC_TRANSLATIONS = {
    # 文档标题
    'FOREIGN TRADE QUOTATION': '外贸报价单',
    'PROFORMA INVOICE': '形式发票',
    'PACKING LIST': '装箱单',
    'COMMERCIAL INVOICE': '商业发票',
    'QUOTATION': '报价单',
    # 表头
    'No.': '序号', 'Model': '型号', 'Product Name': '产品名称',
    'Model / Product Name': '型号 / 产品名称', 'Photo': '图片',
    'Specifications': '规格参数', 'Specification': '规格',
    'Qty': '数量', 'Unit Price': '单价',
    'Total Amount': '总金额', 'Total': '合计',
    'Description of Goods': '货物描述', 'DESCRIPTION OF GOODS': '货物描述',
    'Quantity': '数量', 'Unit': '单位',
    'Item No.': '项号',
    # 公司/地址
    'Seller': '卖方', 'Buyer': '买方', 'Shipper': '发货人',
    'Consignee': '收货人', 'Exporter': '出口商',
    'Port of Loading': '启运港', 'Port of Discharge': '目的港',
    'Port of Loading:': '启运港：', 'Port of Discharge:': '目的港：',
    'Vessel': '船名', 'Flight No.': '航班号',
    'B/L No.': '提单号', 'B/L No.:': '提单号：',
    'Marks': '唛头', 'N/M': '无唛头',
    'NW': '净重', 'GW': '毛重', 'Meas': '体积',
    'NW (kg)': '净重 (kg)', 'GW (kg)': '毛重 (kg)',
    'Meas (m\u00b3)': '体积 (m\u00b3)',
    'Carton Size': '外箱尺寸', 'Carton Size (cm)': '外箱尺寸 (cm)',
    'Qty/Carton': '每箱数量', 'Marks & Nos.': '唛头与编号',
    'Country of Origin': '原产国', 'HS Code': 'HS编码',
    # 文档标签
    'Packing List': '装箱单',
    '1. Shipper (Exporter):': '1. 发货人（出口商）',
    'Packing List No.': '装箱单号',
    '2. Consignee (Buyer):': '2. 收货人（买方）',
    '3. Transport Details:': '3. 运输详情',
    'Vessel/Flight:': '船名/航班：',
    '4. Shipping Marks:': '4. 唛头',
    '5. No. of Packages:': '5. 包装件数',
    '6. Total Packages (in words):': '6. 总件数（大写）：',
    '7. Remarks:': '7. 备注：',
    '8. Signature:': '8. 签章',
    '1. Seller:': '1. 卖方',
    '2. Buyer:': '2. 买方',
    'S/C No.': '合同号',
    'L/C No.': '信用证号',
    'Incoterms:': '贸易术语：',
    '4. Marks & No.:': '4. 唛头与编号',
    '6. Freight & Charges:': '6. 运费与杂费',
    'Freight:': '运费：',
    'Insurance:': '保险：',
    'Handling:': '装卸费：',
    'Others:': '其他：',
    '9. Country of Origin:': '9. 原产国',
    'HS Code:': 'HS编码：',
    '10. Bank Information:': '10. 银行信息',
    'Beneficiary:': '收款人：',
    'Bank name:': '银行名称：',
    'Bank add.:': '银行地址：',
    'Bank account no.:': '银行账号：',
    'Swift code.:': 'Swift代码：',
    '11. Remarks: All disputes subject to jurisdiction of China.': '11. 备注：所有争议由中国管辖。',
    '12. Signature:': '12. 签章',
    'Commercial Invoice': '商业发票',
    'pcs': '件',
    # 贸易
    'Trade Terms': '贸易条款',     'Payment Terms': '付款条款', 'Payment Terms:': '付款条款：',
    'Delivery Date': '交货日期', 'Lead Time': '交货期',
    'Validity': '有效期', 'Remarks': '备注',
    'Signature': '签章', 'Date': '日期', 'Date: ': '日期：',
    'Invoice No.': '发票号',     'Invoice No.: ': '发票号：',
    'Date: ': '日期：',
    'To: ': '致：',
    '[Company Name]': '[公司名称]',
    '[Address]': '[地址]',
    'PROFORMA INVOICE': '形式发票',
    'Quantity\n(sets)': '数量\n（套）',
    'The seller:': '卖方：',
    'The buyer:': '买方：',
    'Bank Information:': '银行信息：',
    'Other Notices: The supplier provide the Certificate of Origin (C/O) to the buyer ONLY. Other documents or certificates will be charged additionally.': '其他通知：供应商仅向买方提供原产地证（C/O）。其他文件或证书将另行收费。',
    'Packing List No.': '装箱单号',
    # 条款
    'Payment': '付款', 'Delivery': '交货',
    'Transshipment': '转运', 'Insurance': '保险',
    'Freight': '运费', 'Handling': '装卸费',
    'Bank Information': '银行信息',
    'Beneficiary': '收款人', 'Account No.': '账号',
    'Swift Code': 'Swift代码',
    # 报价单
    'Quotation No.': '报价单号',
    'Valid Until': '有效期至',
    'Standard export packing': '标准出口包装',
    '15-25 days after deposit': '收到定金后15-25天',
    'Please confirm within validity period': '请在有效期内确认',
    'Tel': '电话', 'Email': '邮箱',
    'TOTAL:': '合计：',
    # PI 文档标签
    'FOB': 'FOB',
    'TOTAL AMOUNT': '总金额',
    'TOTAL PAYMENT': '付款总额',
    'SAY': '合计',
    'ONLY.': '整。',
    'ZERO': '零',
    'Brand Name:': '品牌名：',
    'Port of destination:': '目的港：',
    # PI 条款（长文本）
    'Delivery date: 60 days upon receipt of payment.': '交货日期：收到付款后60天内。',
    'Transshipment: not allowed; Partial shipment: not allowed.': '转运：不允许；分批装运：不允许。',
    'Validity: This quotation is valid for 30 days from the date above.': '有效期：本报价自上述日期起30天内有效。',
    'Insurance: To be covered by the buyer.': '保险：由买方承担。',
    'Documents required: Commercial Invoice, Packing List, Bill of Lading, Certificate of Origin.': '所需文件：商业发票、装箱单、提单、原产地证。',
    'Handling method on the expiry order: The contract will automatically become void if the buyer does not provide any instruction before the delivery date.': '到期订单处理方式：若买方在交货日前未提供任何指示，合同将自动失效。',
    'Handling method on discrepancy of quality & quantity: In case of quality discrepancy, claim should be filed within 30 days after arrival of goods.': '质量数量异议处理：如发生质量异议，应在货物到港后30天内提出索赔。',
    'Arbitration: All disputes shall be settled through friendly negotiation. If no settlement can be reached, the case shall be submitted to China International Economic and Trade Arbitration Commission for arbitration.': '仲裁：所有争议应通过友好协商解决。协商不成，应提交中国国际经济贸易仲裁委员会仲裁。',
    # 通用
    'TOTAL': '合计', 'Subtotal': '小计', 'Subtotal:': '小计：',
    'signed & stamped': '签名盖章',
    'All disputes subject to jurisdiction of China.': '所有争议由中国管辖。',
    'Thank you for your business!': '感谢您的合作！',
}


def translate_doc(text: str, lang: str) -> str:
    """翻译文档静态文本（标题/表头/条款等）
    lang: 'chinese'=中文, 'english'=保持英文, 'bilingual'=中英对照
    直接查 DOC_TRANSLATIONS 英→中，不调用 translate_text（那是中→英）
    """
    if lang == 'english':
        return text
    translated = DOC_TRANSLATIONS.get(text, text)
    if lang == 'bilingual' and translated != text:
        return f"{text} / {translated}"
    return translated


def bilingual_text(text_zh: str, text_en: str = None) -> str:
    """生成双语对照文本（相同内容不重复）"""
    if text_en is None:
        text_en = translate_text(text_zh, 'zh_en')
    if not text_en or text_en == text_zh:
        return text_zh
    return f"{text_zh} / {text_en}"


if __name__ == '__main__':
    # 测试
    test_text = "型号: ABC-123, 价格: ¥100, 规格: 100x200mm"
    result = translate_text(test_text, 'zh_en')
    print(f"原文: {test_text}")
    print(f"翻译: {result}")
