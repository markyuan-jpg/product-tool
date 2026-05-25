# Fix Plan: PDF Images + Performance + OCR Detection

## Goal
Fix 3 issues with PDF parsing and Excel performance

## Phases

### Phase 1: PDF Image Matching
- **Problem**: `_associate_images_to_products()` matches model string vs generic filename `page1_img1.png` → always fail. Also PDF image dir not in whitelist.
- **Fix**: Position-based matching (by page order), add PDF image dir to whitelist
- **Files**: `product_tool/src/core/pdf_parser.py`, `backend/main.py`
- **Status**: pending

### Phase 2: Scanned PDF Detection (Clear Error Message)
- **Problem**: pdfplumber/Docling can't parse scanned PDF → returns "文件中未找到产品数据", misleading
- **Fix**: Detect textless PDF → show "当前PDF为扫描件，请上传文字型PDF文件"
- **Files**: `backend/main.py` or `product_tool/src/core/pdf_parser.py`
- **Status**: pending

### Phase 3: Performance Optimization
- **Problem**: Multiple redundant `load_workbook`, duplicate image extraction, unconditional strategy runs
- **Fix**: Cache workbook, early exit from strategies, reduce redundant image work
- **Files**: `backend/universal_parser.py`, `product_tool/src/parse/excel_parser_v3.py`, `product_tool/src/core/image.py`, `backend/run.py`
- **Status**: pending

## Final Verification
- Upload PDF with embedded images → images show up
- Upload scanned PDF → clear error "扫描件，不支持"
- Upload Excel file → parse speed noticeably faster
- All existing tests pass
