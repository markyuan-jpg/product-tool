"""
Output module - Excel/PDF generation
"""
from .excel_enhanced import (
    apply_template,
    merge_excel_files,
    export_to_template,
)

from .pdf_generator import (
    create_quote_pdf,
)

__all__ = [
    'apply_template',
    'merge_excel_files',
    'export_to_template',
    'create_quote_pdf',
]