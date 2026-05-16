# -*- coding: utf-8 -*-
"""
PDF quotation generator
"""
import os, sys, tempfile, logging
from typing import List, Dict, Optional
from datetime import datetime
from src.utils.translator import translate_doc as _translate_doc
from .doc_shared import translate_items
from ..parsers.spec_cleaner import clean_spec

try:
    import win32com.client as win32
    _HAS_WIN32 = True
except ImportError:
    _HAS_WIN32 = False

# reportlab 
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    _HAS_REPORTLAB = True
except ImportError:
    _HAS_REPORTLAB = False


def xlsx_to_pdf(xlsx_path: str, pdf_path: str) -> bool:
    """Convert xlsx to pdf via Excel/WPS"""
    if not _HAS_WIN32:
        logging.warning("pywin32 not installed, cannot use Excel/WPS to convert")
        return False

    abs_xlsx = os.path.abspath(xlsx_path)
    abs_pdf = os.path.abspath(pdf_path)

    for app_name in ["Excel.Application", "Ket.Application"]:
        try:
            excel = win32.Dispatch(app_name)
            excel.Visible = False
            excel.DisplayAlerts = False
            wb = excel.Workbooks.Open(abs_xlsx)
            ws = wb.Worksheets(1)
            ws.PageSetup.Zoom = False
            ws.PageSetup.FitToPagesWide = 1
            ws.PageSetup.FitToPagesTall = 1
            ws.PageSetup.Orientation = 2  # landscape
            wb.ExportAsFixedFormat(0, abs_pdf)  # xlTypePDF
            wb.Close(False)
            excel.Quit()
            return os.path.exists(pdf_path)
        except Exception as e:
            logging.warning(f"{app_name} failed: {e}")
            try:
                excel.Quit()
            except Exception:
                pass
            continue
    return False


def create_quote_pdf(data: List[Dict], output_path: str,
                     title: str = "",
                     company: str = "",
                     contact: str = "",
                     lang: str = "chinese",
                     payment_terms: str = "",
                     currency: str = "CNY",
                     with_images: bool = True) -> bool:
    """"""
    if not data:
        return False

    #  create_quotation 
    doc_title = title or _translate_doc('FOREIGN TRADE QUOTATION', lang)

    # ???xlsx
    try:
        from src.output.quotation_excel import create_quotation
    except Exception:
        return _fallback_reportlab(data, output_path, doc_title, company, contact, with_images=with_images)

    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    tmp_xlsx = os.path.join(tempfile.gettempdir(), f"_pdf_tmp_{ts}.xlsx")

    try:
        create_quotation(data, tmp_xlsx, lang=lang, with_images=with_images, payment_terms=payment_terms, currency=currency)
    except Exception as e:
        logging.error(f"xlsx generation failed: {e}")
        return _fallback_reportlab(data, output_path, doc_title, company, contact, currency, lang, with_images)

    # xlsx ???PDF
    if xlsx_to_pdf(tmp_xlsx, output_path):
        try:
            os.remove(tmp_xlsx)
        except Exception:
            pass
        return True

    # Excel/WPS  reportlab
    try:
        os.remove(tmp_xlsx)
    except Exception:
        pass
    return _fallback_reportlab(data, output_path, title, company, contact, currency, lang, with_images)


def _fallback_reportlab(data: List[Dict], output_path: str,
                        title: str, company: str, contact: str,
                        currency: str = 'CNY', lang: str = 'chinese',
                        with_images: bool = True) -> bool:
    """reportlab """
    if not _HAS_REPORTLAB:
        logging.error("reportlab not available and Excel/WPS conversion failed")
        return False

    # 
    _cn_font = 'Helvetica'
    _cn_font_bold = 'Helvetica-Bold'
    _font_ok = False
    for _p in [
        'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/simsun.ttc',
        'C:/Windows/Fonts/msyhbd.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        os.path.expanduser('~/Library/Fonts/NotoSansCJKsc-Regular.otf'),
        '/System/Library/Fonts/PingFang.ttc',
    ]:
        if os.path.exists(_p):
            try:
                if 'bd' in _p.lower() or 'bold' in _p.lower():
                    pdfmetrics.registerFont(TTFont('CBF', _p))
                    _cn_font_bold = 'CBF'
                else:
                    pdfmetrics.registerFont(TTFont('CF', _p))
                    _cn_font = 'CF'
                _font_ok = True
            except Exception as ex:
                logging.warning(f"Font registration failed for {_p}: {ex}")

    doc = SimpleDocTemplate(output_path, pagesize=A4,
                           leftMargin=10*mm, rightMargin=10*mm,
                           topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    elements = []

    h_style = ParagraphStyle('H', fontName=_cn_font_bold, fontSize=12,
                             textColor=colors.HexColor('#1F4E79'), spaceAfter=2)
    if company:
        elements.append(Paragraph(company, h_style))
    i_style = ParagraphStyle('I', fontName=_cn_font, fontSize=8,
                            textColor=colors.HexColor('#555555'), spaceAfter=2)
    if contact:
        elements.append(Paragraph(f'Tel: {contact}', i_style))
    elements.append(Paragraph(f'{datetime.now().strftime("%Y-%m-%d")}', i_style))
    elements.append(Spacer(1, 5*mm))

    t_style = ParagraphStyle('T', fontName=_cn_font_bold, fontSize=16,
                            alignment=1, spaceAfter=5*mm)
    elements.append(Paragraph(title or 'QUOTATION', t_style))
    if not _font_ok:
        warn_style = ParagraphStyle('Warn', fontName='Helvetica', fontSize=8,
                                     textColor=colors.red, spaceAfter=10)
        elements.append(Paragraph('* Chinese font not available. Some text may not display correctly.', warn_style))

    cur_sym = '$' if currency in ('USD', 'US') else ('¥' if currency in ('CNY', 'RMB', '') else currency)
    headers = [_translate_doc(h, lang) for h in ['No.', 'Photo', 'Model / Name', 'Specifications', 'Qty', f'Unit Price ({cur_sym})', f'Total ({cur_sym})']]
    table_data = [headers]
    col_widths = [10*mm, 18*mm, 48*mm, 58*mm, 12*mm, 22*mm, 22*mm]

    # ???Paragraph 
    cell_style = ParagraphStyle('Cell', fontName=_cn_font, fontSize=8,
                                leading=10, wordWrap='CJK')
    name_style = ParagraphStyle('Name', fontName=_cn_font, fontSize=8,
                                leading=10, wordWrap='CJK')
    
    total_amount = 0
    for i, item in enumerate(data, 1):
        qty = int(item.get('qty', item.get('quantity', 1)))
        price = float(item.get('price_rmb', 0))
        total = qty * price
        total_amount += total
        model = item.get('model', '')
        name = item.get('name_zh', '')
        spec = clean_spec(item.get('spec_zh', ''))
        display_name = f"{model}\n{name}" if name and name != model else model
        img_path = item.get('_image_path', '') or item.get('image_path', '')
        photo = ''
        if with_images and img_path and os.path.exists(img_path):
            try:
                first = img_path.split(';')[0].strip()
                if os.path.exists(first):
                    from src.core.image import resize_image
                    _resized = resize_image(first, max_w=300)
                    photo = RLImage(_resized if hasattr(_resized, 'read') else first, width=13*mm, height=13*mm)
            except Exception: pass
        table_data.append([i, photo,
                          Paragraph(display_name, name_style),
                          Paragraph(spec, cell_style) if spec else '',
                          qty, price, total])

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), _cn_font_bold),
        ('FONTNAME', (0, 1), (-1, -1), _cn_font),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (3, -1), 'LEFT'),
        ('ALIGN', (4, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F8FC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4*mm))

    total_style = ParagraphStyle('Total', fontName=_cn_font_bold, fontSize=10,
                                textColor=colors.HexColor('#1F4E79'), alignment=2)
    elements.append(Paragraph(f'TOTAL: {total_amount:,.2f}', total_style))

    try:
        doc.build(elements)
        return True
    except Exception as e:
        logging.error(f"reportlab PDF generation failed: {e}")
        return False

