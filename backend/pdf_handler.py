"""
pdf_handler.py — PDF 解析入口，每次直接 import 确保使用最新代码。
"""
import sys, os

SRC = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'product_tool', 'src')
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def extract_products_from_pdf_v2(pdf_path: str):
    """导入并调用 PDF 解析器"""
    import importlib
    # 清除缓存确保加载最新源码
    for mod in list(sys.modules.keys()):
        if 'pdf_parser' in mod:
            del sys.modules[mod]
    from src.core.pdf_parser import extract_products_from_pdf_v2 as fn
    return fn(pdf_path)
