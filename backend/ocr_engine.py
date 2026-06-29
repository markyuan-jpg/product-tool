"""
OCR 文本提取模块 — 支持图片和扫描件 PDF

依赖: easyocr (可选, pip install easyocr)
降级: 未安装时返回 None, 调用方应检查并用友好错误提示
"""

import logging
import os
from pathlib import Path
from typing import Optional, List
import tempfile

logger = logging.getLogger(__name__)

_reader = None
_reader_available = None  # None=未检测, True=可用, False=不可用

def _get_reader():
    """懒加载 easyocr Reader，失败返回 None"""
    global _reader, _reader_available
    if _reader_available is not None:
        return _reader if _reader_available else None
    try:
        import easyocr
        # Chinese + English reader, GPU if available
        _reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
        _reader_available = True
        logger.info("EasyOCR loaded (CPU mode)")
        return _reader
    except ImportError:
        logger.warning("EasyOCR not installed. pip install easyocr to enable OCR.")
        _reader_available = False
        return None
    except Exception as e:
        logger.error(f"EasyOCR init failed: {e}")
        _reader_available = False
        return None


def ocr_available() -> bool:
    """检查 OCR 是否可用"""
    return _get_reader() is not None


def extract_text_from_image(image_path: str) -> Optional[str]:
    """
    从图片文件提取文字。
    
    Args:
        image_path: 图片文件路径
    
    Returns:
        提取的文字字符串，或 None（OCR 不可用时）
    """
    reader = _get_reader()
    if reader is None:
        return None
    
    try:
        results = reader.readtext(image_path, detail=0)  # detail=0 只返回文字
        return '\n'.join(results) if results else ''
    except Exception as e:
        logger.error(f"OCR failed for {image_path}: {e}")
        return None


def extract_text_from_pdf_images(pdf_path: str, max_pages: int = 5) -> Optional[str]:
    """
    从扫描件 PDF 提取文字（将每页渲染为图片后 OCR）。
    
    Args:
        pdf_path: PDF 文件路径
        max_pages: 最大处理页数（防止超大文件超时）
    
    Returns:
        提取的文字字符串，或 None
    """
    reader = _get_reader()
    if reader is None:
        return None
    
    try:
        import fitz  # PyMuPDF
    except ImportError:
        logger.warning("PyMuPDF not available for PDF image extraction")
        return None
    
    all_text = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return None
    
    try:
        for page_num in range(min(len(doc), max_pages)):
            page = doc[page_num]
            # Render page to image at 200 DPI
            pix = page.get_pixmap(dpi=200)
            
            # Save to temp file for easyocr (it prefers file path)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                tmp_path = tmp.name
                pix.save(tmp_path)
            
            try:
                results = reader.readtext(tmp_path, detail=0)
                if results:
                    all_text.extend(results)
            finally:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
        
        return '\n'.join(all_text) if all_text else ''
    finally:
        doc.close()


def is_scanned_pdf(pdf_path: str, text_threshold: int = 50) -> bool:
    """
    检测 PDF 是否为扫描件（文字量极少 → 很可能是图片 PDF）。
    """
    try:
        import fitz
    except ImportError:
        return False
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return False
    
    try:
        total_chars = 0
        pages_checked = min(len(doc), 3)
        for i in range(pages_checked):
            total_chars += len(doc[i].get_text().strip())
        return total_chars < text_threshold
    except Exception:
        return False
    finally:
        doc.close()
