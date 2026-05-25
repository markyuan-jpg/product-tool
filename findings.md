# Findings

## PDF Image Matching (Phase 1)

### Root Cause
- `pdf_parser.py` line 1154-1178 `_associate_images_to_products()`: checks if `product_model in img_filename`
- PyMuPDF saves images as `page{N}_img{M}.{ext}` → never contains model number → always fails
- PDF image directory `{pdf_dir}/images/{name}/` not in `/api/images` whitelist (main.py lines 824-864)

### Solution: Position-based matching
- `extract_images_from_pdf()` returns `[{'page': int, 'index': int, 'image_path': str}]`
- Tables are extracted per page → we know which products are on which page
- Match: for products on page N, assign images from page N sequentially

## Scanned PDF Detection (Phase 2)

### Root Cause
- pdfplumber reads zero text from scanned/image PDFs
- All 3 strategies produce empty results
- Docling fallback fails with "this model does not support pdf input"
- `extract_products_from_pdf_v2()` returns None → main.py shows "文件中未找到产品数据"

### Solution
- After pdfplumber reads all pages, check total extracted text length
- If text < threshold (e.g. 50 chars), mark as likely scanned
- Return specific status: scanned_pdf=true

## Performance Optimization (Phase 3)

### Redundancy Details
1. `load_workbook` called 3-4x per Excel parse:
   - universal_parser.py:757 (data_only=True)
   - run.py:149 (detect_parser_type, read_only=True)
   - excel_parser_v3.py:837 (image extraction, read_only=False)
   - excel_parser_v3.py:925 (fallback, read_only=True)

2. Image extraction 2-3x per Excel:
   - universal_parser calls match_images_to_products()
   - run.parse_file calls match_images_to_products()
   - excel_parser_v3 calls extract_images_from_worksheet() internally

3. All 4 universal parser strategies run unconditionally:
   - KV, Table, Content, No-header — even if KV already perfect

4. sys.modules cache clearing on every PDF parse:
   - pdf_handler.py deletes 'pdf_parser' from sys.modules → forces re-import

### Quick Wins
- Cache openpyxl Workbook object across calls
- After KV strategy, check score → skip remaining if high enough
- Extract images once, pass result between functions
- Run universal + specialized in parallel via asyncio.gather
