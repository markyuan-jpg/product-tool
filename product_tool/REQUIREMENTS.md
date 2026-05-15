# Product Tool — Requirements & Module Audit

> ⚠️ **DOCUMENT SYNC RULE**: This English file and its Chinese counterpart (`产品需求文档.md`) MUST be updated together. Any change to one requires an identical update to the other. The Chinese version is the user-facing document; this English version is the AI/developer-facing technical reference.

---

## Product Positioning

| Dimension | Content |
|-----------|---------|
| **Target Users** | Foreign trade SOHO / 3-5 person micro teams who need to generate quotes quickly from messy source files |
| **Core Value** | Not a template tool — a **data integration engine**: parse once, reuse forever; data stays on server, files deleted after processing |
| **Output Files** | Excel quotation (with images), PDF quotation, Proforma Invoice PI, Packing List, Commercial Invoice (5 types, all connected) |
| **Non-Functional** | Upload-to-quote 3-60 seconds; Web-based (Next.js + FastAPI); Chinese-first UI |
| **Architecture** | Frontend: Next.js on Vercel. Backend: FastAPI on Railway. Universal parser handles table/KV/multi-product formats |
| **Current Status** | ✅ Universal parser (three-strategy: KV→Table→Content-driven, scored). ✅ PDF parser (three-strategy: layout→content→scored, +Docling fallback). ✅ DOCX parser. ✅ Image column filtering. ✅ Auto currency detection. ✅ Price configuration (JSON + multi-industry + regex). ✅ PostgreSQL migration (Supabase). ✅ Creem subscription payments (checkout + webhook). ✅ Dual-token auth (access + refresh httpOnly). ✅ Usage quota display. ✅ RMB price column (price_cny). ✅ Export column selection (11 checkboxes). ✅ Language fixes. ✅ CLI packing/invoice. ✅ Product library batch delete |
| **Web UI** | ✅ Live — Next.js web app. No longer using Streamlit plan |
| **Monetization** | Free tier (3 files) + Registered free + Pro ¥39/month (early bird, regular ¥69/month). Manual WeChat payment + manual activation |

---

## Overview

Foreign trade product catalog & quotation tool. Extract product data from multi-format source files (Excel/PDF/DOCX), manage product library, generate formatted quotations with images and trade term calculations.

### Data Pipeline

```
Browser (localhost:3000)
   │
   ▼
┌─────────────────────────────────────────────────┐
│  landing/ (Next.js, Vercel)                       │
│  ├── Home: upload files → generate quotation      │
│  ├── /pricing: pricing & feature comparison       │
│  ├── /how-it-works: 3-step workflow explainer     │
│  └── /login: workspace placeholder                │
└─────────────────────────────────────────────────┘
   │  API proxy (/api/* → backend:8000)
   ▼
┌─────────────────────────────────────────────────┐
│  backend/ (FastAPI, Railway)                     │
│                                                  │
│  POST /api/parse — file parsing (3-strategy scoring)│
│     ├── Universal parser (universal_parser.py)    │
│     │    ├── Strategy 1: KV layout → products     │
│     │    ├── Strategy 2: Table layout → col map   │
│     │    ├── Strategy 3: Content-driven → infer   │
│     │    ├── score_result() picks best             │
│     │    └── Currency detection (FOB→USD, else RMB)│
│     ├── PDF parser (pdf_parser.py) — 3 strategies  │
│     │    ├── Layout detection → col/row_based     │
│     │    ├── Content inference → _classify + parse │
│     │    └── _score_pdf_result() picks best        │
│     ├── DOCX parser (doc_parser.py) — 3 strategies │
│     │    ├── Header keyword matching → col map    │
│     │    ├── Content inference → column roles     │
│     │    ├── Paragraph text → key-value extraction│
│     │    └── _score_docx_result() picks best       │
│     └── Specialized parsers (legacy)              │
│                                                  │
│  POST /api/quotation — generate quotation         │
│  POST /api/pi — generate Proforma Invoice PDF     │
│  POST /api/packing — Packing List + Comm Invoice  │
│  POST /api/template — extract company info        │
│  GET /api/images/ — serve product images          │
└─────────────────────────────────────────────────┘
```

---

## Core Modules (数据流水线核心)

These modules are REQUIRED for the main workflow: import source files → generate English quotation. If any core module is broken, the tool cannot produce correct output.

### 1. CLI Entry Points

| Module | `product_cli.py` (recommended) | `run.py` (legacy) |
|--------|-------------------------------|-------------------|
| **Tech** | argparse, sqlite3, openpyxl | argparse, openpyxl, pandas |
| **Status** | 100% — production ready | 95% — still used by run.py tests |
| **Function** | Interactive/Direct/Excel batch product selection → quotation | File parsing → optional DB save → output |
| **How it works** | 3 selection modes: (1) `--select` interactive browse categories (2) `--sku` comma-separated SKUs (3) `--order-file` Excel SKU list. Calls `create_quotation_from_library()`. | Parses args → detects parser type → dispatches file → optional dedup/categorize/DB save → styled Excel or quotation output |
| **Connection** | Entry point, calls quotation_excel + product_manage | Entry point, calls parsers + product_manage + quotation_excel |
| **Flags** | `--select`, `--sku`, `--quantity`, `--quote`, `--currency`, `--trade-terms`, `--lang`, `--with-images`, `--user-id` | `--input`, `--output`, `--lang`, `--quotation`, `--save-to-db`, `--merge`, `--category`, `--supplier` |

### 2. Parser Layer

| Module | Tech | Status | Function | How it works | Connected via |
|--------|------|--------|----------|-------------|--------------|
| `excel_parser_v3.py` | openpyxl, pandas, zipfile | 95% | **Main Excel parser** — auto-detects 6 layout types | `classify_format()` scans sheet for markers: `param_list` > `invoice` > `price` > `horizontal` > `single_spec` > `vertical`. Dispatches to specialized parsers or built-in fallbacks. Extracts embedded images via zipfile. | `run.py:parse_file()` |
| `param_price_parser.py` | openpyxl, pandas | 95% | Parses `Model:`/`型号:`/`Item:` marker format | Scans first rows for marker, then reads key:value pairs per column. Handles price markers (Price:, 价格:). Extracts embedded images. | `run.py:detect_parser_type()` → `parse_file()` |
| `invoice_parser.py` | openpyxl, pandas | 90% | Parses Proforma Invoice format | Finds "Description of Goods" header, extracts model/spec/qty/price columns. Skip keywords filter footer rows. | Same dispatch chain |
| `price_table_parser.py` | openpyxl, pandas | 95% | Parses 车型价格表 (vehicle price table) | Fixed column mapping: col 2=model, col 4=price, cols 6-12=motor specs. | Same dispatch chain |
| `single_spec_parser.py` | openpyxl, pandas | 85% | Parses single-product spec sheets | Handles files with one product and many param rows. Composite price splitting (`"EV: CNY 4980 / Battery: CNY 2530"`). | Same dispatch chain |
| `spec_formatter.py` | re | 98% | Spec post-processing | Removes duplicates, standardizes units, formats key:value pairs. Handles space-separated specs (`"Motor: 4000W Battery: 72V"` → splits to newlines). Called on all parsed specs. | Called by `excel_parser_v3.py` after parser dispatch |
| `pdf_parser.py` | pdfplumber, fitz, pandas | **95%** | Extracts products from PDF (3-strategy, scored) | `extract_products_from_pdf_v2()`: extracts tables via pdfplumber → **3 strategies**: layout detection (col/row_based) → content inference (`_classify_pdf_columns()`) → `_score_pdf_result()` picks best → `_associate_images_to_products()` | `run.py:parse_file()` (ext=.pdf) |

### 3. Data Processing Layer

| Module | Tech | Status | Function | How it works | Connected via |
|--------|------|--------|----------|-------------|--------------|
| `price.py` | re | **100%** ✅ | Price cleaning & conversion | `clean_price_value()`: extracts numbers, detects currency ($/¥/€/£), handles K/W expansion (5K=5000, 10W=100000), converts all to CNY via live rates. **Bug fixed: K-expansion no longer blocked by 'USD' guard.** | Called by parsers + importer |
| `image.py` | openpyxl, zipfile, xml.etree | **100%** ✅ | **Image extraction engine (3-way + column filter + merged propagation)** | Three-way: ① openpyxl `_images` + anchor row (standard embedded); ② DISPIMG formula parsing + worksheet XML (WPS files); ③ drawing XML parsing (standard xlsx). **`_detect_image_column()` auto-detects "产品图片" column → `image_col` filter excludes packaging/compatibility images (col 8)**. Unified `match_images_to_products()` entry, with `match_sku_folder()` fallback, `extract_images_from_docx()` for DOCX. **Merged cell image propagation**: merged group rows share the first row's image. | Auto-called by all parsers |
| `detector.py` | pandas, re | 95% | Column type detection | `smart_detect_columns()`: scores each column as price/model/spec/name based on content pattern analysis. | Called by parsers |
| `dedup_engine.py` | pandas, numpy | 100% | 7-step fuzzy dedup pipeline | Steps: (1) normalize model, (2) strip suffixes, (3) fuzzy key grouping, (4) score matching, (5) filter by threshold, (6) merge duplicates, (7) report stats. **Bug fixed: total_input stat now uses input count, not filtered output.** | Called by `run.py` before DB import |
| `categorizer.py` | pandas, JSON | 100% | Auto-categorization | `categorize_data()`: matches products against categories from JSON config using keyword rules. | Called by `run.py` |

### 4. Storage Layer

| Module | Tech | Status | Function | How it works | Connected via |
|--------|------|--------|----------|-------------|--------------|
| `product_manage/db.py` | sqlite3 | 100% | Database init & schema | Creates `products` table with columns: id, user_id, sku (unique per user), name_zh, name_en, category, price_rmb, price_usd, moq, specs (JSON), spec_zh, spec_en, image_path, source_file, timestamps. Indexes on sku, category, name_zh, user_id. | Called by all other product_manage modules |
| `product_manage/models.py` | dataclasses | 100% | Product data model | `Product` dataclass with `to_row()` / `from_row()` for DB serialization. `specs` is dict, serialized as JSON. | Used by repository + importer |
| `product_manage/repository.py` | sqlite3 | 100% | DB CRUD operations | Functions: `save_product()`, `get_product_by_sku()`, `get_products_by_skus()` (batch, **N+1 fixed**), `get_products_by_ids()` (batch, **N+1 fixed**, supports `order_by_source`), `list_products()`, `search_products()`, `get_categories()`, `delete_product()`. All queries parameterized. | Called by importer, exporter, product_cli |
| `product_manage/importer.py` | pandas, sqlite3 | 100% | Import parsed data to DB | `import_from_df()`: iterates rows, checks duplicate via batch SKU lookup, auto-generates suffix (-A, -B) on collision, auto-translates name_zh→name_en if empty, inserts with timestamps. | Called by `run.py` (--save-to-db) |
| `product_manage/exporter.py` | pandas, openpyxl | 100% | Export DB to Excel | `export_to_excel()`: reads all products for a user, writes styled Excel file. | Called by test scripts |

### 5. Business Logic Layer

| Module | Tech | Status | Function | How it works | Connected via |
|--------|------|--------|----------|-------------|--------------|
| `terms.py` | dataclasses | 100% | Trade terms calculation | `calculate_price()`: computes EXW/FOB/CIF/DAP/DDP per Incoterms 2020. Inputs: base price, quantity, destination, volume. Outputs: detailed breakdown with freight, insurance, duties. | Called by `quotation_excel.py` |
| `rates.py` | requests, JSON | 100% | Live exchange rates | `get_rate(from_ccy, to_ccy)`: fetches from rates.convert API, caches to JSON, fallback to hardcoded rates on network failure. | Called by `terms.py`, `price.py`, `importer.py` |
| `translator.py` | re (dict-based) | 100% | ZH↔EN translation | `translate_text(text, mode)`: dictionary replace with 160+ trade terms. Keys sorted by length (longest first) to avoid partial-match corruption. `translate_dataframe()` translates all string columns. Used at import time and quote time. | Called by `run.py`, `product_cli.py`, `quotation_excel.py` via `--lang` flag |
| `company.py` | json, pathlib | 100% | Company config management | `load_company()` / `save_company()`: reads/writes company info (name, contact, address, etc.) from `company.json`. | Called by `quotation_excel.py` |

### 6. Output Layer

| Module | Tech | Status | Function | How it works | Connected via |
|--------|------|--------|----------|-------------|--------------|
| `quotation_excel.py` | openpyxl, pandas | **100%** ✅ | **Quotation generator** — core output | `QuotationExcel.write()`: styled Excel with company info block (name/address/tel/email), 7-column headers (No./Photo/Model+Name/Specs/Qty/Unit Price/**Total**), smart Model/Name dedup, auto-wrap specs, image embedding, bottom Total row, trade terms, payment terms. `create_quotation_from_library()`: reads from DB → spec fallback (compare specs dict vs spec_zh length, use longer) → filter "nan" from name_zh/nane_en → resolve image path → compute price. Supports `--lang english/bilingual`. | Called by `product_cli.py` + `run.py` |

---

## Non-Core Modules (辅助/待接线)

These modules are NOT required for the main workflow. Some are written but unconnected; others are standalone utilities.

| Module | Tech | Status | Function | Why non-core | Action needed to connect |
|--------|------|--------|----------|-------------|--------------------------|
| `doc_parser.py` | python-docx, zipfile, re | **95%** | DOCX parsing (3-strategy: header match→content→paragraph) | `parse_product_docx()` 3 strategies: ① Header keyword matching (extended model/price/spec synonyms) → column mapping → extract; ② `_infer_docx_columns()` content-driven column role inference → extract; ③ `_extract_products_from_text()` paragraph key-value extraction (prefers ¥ over $). `_score_docx_result()` picks best. Built-in `extract_images_from_docx()`. | `run.py:parse_file()` routes `.docx` |
| `pi_generator.py` | weasyprint, jinja2 | 90% | PI generation (HTML→PDF) | Downstream document, not needed for basic quoting | ✅ Connected via `--pi` flag. `pip install weasyprint` required. |
| `pdf_generator.py` | reportlab (legacy) / weasyprint | 85% | PDF quotation | Replaced reportlab (Chinese font issue) with weasyprint-based inline generation | ✅ Connected via `--pdf` flag. Uses weasyprint HTML→PDF, handles CJK via system fonts. |
| `packing/generator.py` | openpyxl | 100% | Packing list + commercial invoice | Downstream document, needed after quote accepted | ✅ Connected via `--packing` flag. **Bug fixed: bare except → except Exception** |
| `excel_writer.py` | openpyxl | 95% | Styled Excel output | Redundant — quotation_excel.py handles styling | Already replacing `df.to_excel()` in run.py |
| `excel_enhanced.py` | openpyxl | 90% | Freeze/filter/template | Cosmetic enhancement to Excel output | Integrate into quotation_excel |
| `pricing.py` | dataclasses | 100% | Tiered pricing (volume breaks) | Business rule, not required for basic quoting | Connect to `create_quotation_from_library()` |
| `tracker.py` | json | 100% | Quote version tracking | CRM feature, not core | Add `--track` flag. **Bug fixed: created_at/expires_at now both float timestamps** |
| `folder_watcher.py` | watchdog | 100% | Directory watching for auto-import | Standalone utility | No connection needed — runs as independent script |
| `image_matcher.py` | PIL, re | 100% | Image filename → product matching | Standalone utility | No connection needed — runs as independent script |
| `filter.py` | pandas | 100% | Product filtering by criteria | Optional enhancement | Integrate into product_cli search |
| `config.py` | Python stdlib | 100% | Global constants | Infrastructure | Used by various modules indirectly |

---

## Bug Fix Status (all resolved)

| Severity | File | Problem | Fix |
|----------|------|---------|-----|
| 🔴 HIGH | `price.py:148-151` | K-expansion guard `'USD' not in text_upper` blocked USD pricing (e.g. "5K USD" → ¥36, not ¥36000) | Removed the 'USD' guard from both K and W expansion conditions |
| 🔴 HIGH | `pdf_parser.py:275` | `detect_table_layout` one-liner could fail on pdfplumber ragged rows | Replaced with robust iteration — checks isinstance, len, None/empty guard |
| 🟡 MED | `excel_parser_v3.py:498` | `parse_price_list` never triggered empty-row break → parsed footer content as products | Added `consecutive_empty` counter, breaks on 2+ empties after 2+ products found |
| 🟡 MED | `excel_parser_v3.py:82-131` | 50 lines dead code after `return` | Deleted entire block; restored helper functions (`is_numeric`, `is_model_code`, `is_spec_keyword`, etc.) |
| 🟡 MED | `packing/generator.py:59,222` | Bare `except:` caught SystemExit/KeyboardInterrupt | Changed both to `except Exception:` |
| 🟡 MED | `tracker.py:62-63` | `created_at` (ISO string) vs `expires_at` (float) — incomparable types | Changed `created_at` to `.timestamp()` (float) |
| 🟡 MED | `dedup_engine.py:321` | `total_input` stat used filtered output count, not input | Moved capture to start of `run()` before filtering |
| 🟡 MED | `repository.py/quotation_excel.py` | N+1 query: `get_product_by_id()` per product in loop | Added batch `get_products_by_ids()` — single query |
| 🟡 MED | `importer.py:52-62` | N+1 query: `get_product_by_sku()` per row in loop | Added batch `get_products_by_skus()` — single query |
| 🟢 LOW | `db.py:76-84` | Missing index on `user_id` | Added `CREATE INDEX idx_products_user_id` |
| 🟢 LOW | `translator.py:48` | Duplicate key `'备注'` overwrote 'Remarks' with 'Note' | Fixed — 'Remarks' kept, duplicate removed |
| 🟢 LOW | `excel_parser_v3.py` | Helper functions deleted with dead code | Restored: `is_numeric`, `count_numeric`, `is_model_code`, `count_model_code`, `is_spec_keyword`, `count_spec_keywords` |

### 2026-05-05 Fixes

| Severity | File | Problem | Fix |
|----------|------|---------|-----|
| 🔴 HIGH | `image.py:71,265` | `row <= 2` filter skipped product images at row 2 (XP) | Changed to `row <= 1`, only skip header row |
| 🟡 MED | `quotation_excel.py:740-748` | `create_quotation_from_library()` only reads `product.specs` dict; empty specs = empty output even when `spec_zh` has full text | Length comparison: prefer whichever is longer (specs dict output vs spec_zh text) |
| 🟡 MED | `quotation_excel.py:772` | `name_zh=null` becomes string "nan" in output | Filter "nan"/"none"/"" → fallback to `sku` |
| 🟡 MED | `quotation_excel.py:774` | `name_en="nan"` creates "XP / nan" in bilingual mode | Same filter for name_en; skip `bilingual_text` when name_en is empty |
| 🟡 MED | `spec_cleaner.py` | `1360*` only got generic `(may be incomplete)` marker | Per-pattern markers (`(尺寸单位缺失)` for `\d+\*`), long-text short-word tail detection |

---

## Image Performance Fix

**Before:** 80-product quotation took **6 minutes**. Root cause: recursive glob scan (`**/*.jpg`).

**After:** `image_path` stored in DB. Three-way matching engine (openpyxl _images / DISPIMG / drawing XML) + DOCX + SKU folder fallback covers all source file types. No glob scan.

**Result:** 80-product quotation in **~10 seconds**. Image coverage **99%** (79/80).

---

## Translation System

| Feature | Status | Usage |
|---------|--------|-------|
| Dictionary | ✅ 160+ trade-specific terms (battery, vehicle, measurement, color, material, certification) | `translator.py` |
| Key sorting | ✅ Longest-first to avoid partial-match corruption | `translate_text()` |
| Output modes | `chinese` (default), `english`, `bilingual` | `--lang` flag |
| CLI wiring | ✅ `run.py` + `product_cli.py` both support `--lang` | Full integration |
| Column headers | ✅ Translated to English when `--lang english` | `quotation_excel.py` |
| Product name | ✅ Auto-translates `name_zh` → `name_en` at import time if empty | `importer.py` |
| Spec content | ✅ Translated via dictionary replacement | `translator.translate_dataframe()` |

---

## Product Integration Results

| Metric | Value |
|--------|-------|
| **Source files** | `param_price.xlsx`, `车型价格表...xlsx`, `quotation.pdf`, `e-motorcycle.pdf`, `SONLINK PI.xlsx`, `BAOSHIMA_...xlsx` |
| **Raw products** | 118 |
| **Final products** | 80 (filtered) |
| **Image coverage** | **79/80 = 99%** |
| **User priority** | `ev_alls` > all other users (dedup winner) |
| **Data sources** | ev_alls: 80 products, local: 54 products, total ~109 (80 after dedup) |

---

## Product Source Distribution

| Source File | Products |
|------------|----------|
| param_price.xlsx | 56 |
| 车型价格表...xlsx | 12 |
| SONLINK PI.xlsx | 7 |
| quotation.pdf | 3 |
| e-motorcycle.pdf | 1 |
| BAOSHIMA_...xlsx | 1 |
| **Total** | **80** |

---

## New Features (2026-05-04)

### 1. Product Ordering by Source

| Feature | Description |
|---------|-------------|
| **Function** | `get_products_by_ids(product_ids, user_id, order_by_source=True)` |
| **Location** | `src/product_manage/repository.py` |
| **Behavior** | Products grouped by `source_file`, then by `created_at` |
| **Usage** | All 9 calls in `product_cli.py` updated with `order_by_source=True` |
| **Result** | Products from same source file appear together in output |

### 2. Space-Separated Spec Formatting

| Feature | Description |
|---------|-------------|
| **Location** | `src/parsers/spec_formatter.py` |
| **Input** | `"Motor: 4000W Battery: 72V 20AH"` (space-separated params) |
| **Output** | `Motor: 4000W\nBattery: 72V 20AH` (newline-separated) |
| **Logic** | Split on space before new `参数名:` pattern |
| **Functions Updated** | `format_spec_spec()`, `split_spec_to_dict()` |

---

## New Features (2026-05-05)

### 1. Three-Way Image Matching Engine

`image.py` completely rewritten to support three xlsx image systems:

| Method | File Types | How |
|--------|-----------|-----|
| **openpyxl `_images`** | Standard xlsx (param_price.xlsx etc.) | Read anchor row (1-indexed), match product `_row` |
| **DISPIMG formula** | WPS files (SONLINK PI.xlsx etc.) | Parse `cellimages.xml` + worksheet `_xlfn.DISPIMG` formulas → (row, file) |
| **drawing XML** | Standard xlsx without _images | Parse `drawingN.xml` → twoCellAnchor → (row, rId) → media/file |

Matching: exact `_row` → ±1 tolerance → order-based (fallback).

### 2. Quotation Column Layout

| Feature | Description |
|---------|-------------|
| **Company info block** | Name/address/tel/email below title (from `company.json`) |
| **Total column** | 7th column `Qty × Unit Price`, bottom summary row |
| **Model/Name dedup** | `model == name_zh` → show model only; else `model\nname_zh` |
| **Spec fallback** | Compare specs dict vs spec_zh length, use longer |
| **"nan" filter** | `name_zh`/`name_en` null/"nan" → fallback to `sku`; skip bilingual_text when name_en empty |

### 3. DOCX Image Extraction

New `extract_images_from_docx()`: extracts from `word/media/`, assigns by file order.

### 4. Truncation Detection Enhancement

`spec_cleaner.py`: new `normalize_spec()` entry; per-pattern markers (`(尺寸单位缺失)` for `\d+\*`); long-text short-word tail detection.

---

## New Features (2026-05-06)

### 1. Three-Strategy Scoring (Excel / PDF / DOCX)

All parsers share a unified 3-strategy architecture. Internal per-parser scoring selects the best strategy within each parser:

| Parser | Strategy A | Strategy B | Strategy C | Internal Score |
|--------|-----------|-----------|-----------|----------------|
| `universal_parser.py` | KV → Table layout | Content-driven column inference | — | `score_result()` |
| `pdf_parser.py` | col_based / row_based | Content-driven (`_classify_pdf_columns`) | — | `_score_pdf_result()` |
| `doc_parser.py` | Header keyword match | Content-driven column roles | Paragraph text extraction | `_score_docx_result()` |

### Cross-Parser Selection (`backend/score.py`)

The universal and specialized parser outputs are compared using a **signal combination scoring system**:

| Signal Combination | Score | Description |
|-------------------|-------|-------------|
| Real model + price + params | +7 | Strongest signal |
| Real model + price | +5 | Strong |
| Real model + params | +4 | Medium |
| Real model only | +2 | Acceptable |
| Price only, no model | +1 | Weak |
| Fake model (商品_R/产品_R) | -3 | Auto-generated |
| Empty model + no price | -3 | Noise row |
| Model has colon or too long | -2 | Misaligned column |

Global consistency bonus: ≥3 unique real models +3, ≥3 products with prices +2, noise ratio<20% +1.

Final score = (sum of per-row scores + bonus) ÷ product count. Higher score wins.

### 2. Column-Based Image Filtering

`_detect_image_column()` scans headers for "产品图片"/"图片"/"Picture" keywords → locates product image column. All 3 extractors (openpyxl/DISPIMG/drawing XML) take `image_col` parameter, extracting only near that column. `_image_col_matches()` tolerance ±1.

**Effect:** Files with "适合图/包装图" columns (compatibility/packaging images) no longer mix those into product images.

### 3. Auto Currency Detection

`_detect_currency()`: checks price column header for FOB/CIF/USD/$ → sets USD, else RMB. `web_products` table has new `currency` column (default 'RMB'). UI displays: `currency === 'USD' ? '$' : '¥'`.

### 4. Remark Attachment System

Non-product rows (notes, battery prices, charger prices, general remarks) are no longer discarded or made into separate products — they attach to the previous product's `remark` field:

- `_is_general_remark()` / `_is_battery_or_charger()` classification
- `remark_text` excludes price column to avoid price numbers in remarks
- `quotation_excel.py` renders gray italic remark rows

### 5. Merged Cell Handling

`extract_table_products()` builds `merge_map` from `ws.merged_cells.ranges`: non-top-left cells read from top-left. `parse()` also propagates images across merged cell groups.

### 6. Auto-Refresh Product Library & Quotation History

`WorkspacePage` adds `productRefreshKey` + `quotationRefreshKey`. State increments after save/generate → `useEffect` dependency triggers re-fetch.

### 7. Quotation History Download & Delete

New endpoints:
- `GET /api/quotations/{id}/download` — serves file from `file_path`
- `DELETE /api/quotations/{id}` — deletes record + file

Quotations auto-save to `web_quotations` (with `file_path`) on generation — no manual "Save to History" needed.

### 8. Product Library Batch Delete

New `POST /api/products/batch-delete` endpoint + frontend "Delete Selected (N)" button.

---

## Data Quality Rules

| Rule | Implementation |
|------|----------------|
| **Bad SKU filter** | Skip SKUs containing `\n` or `:` before position 5 |
| **Test user exclusion** | Skip products where `user_id='test'` |
| **Dedup priority** | When same SKU exists across users, keep `user_id='ev_alls'` version |
| **Model column** | Contains clean SKU only (no spec leakage) |
| **Specs column** | Each param on new line (not semicolon-separated) |

---

## Known Issues

| Severity | File | Issue | Status |
|-----------|------|-------|--------|
| 🟡 MED | 24 files | Bare `except:` catches SystemExit/KeyboardInterrupt | Needs fix |
| 🟢 LOW | `config.py`, `company.py` | Placeholder values (XXX) | Known limitation |

---

- **Duplicate SKUs**: auto-add suffix (-A, -B, ... -AA, -AB) instead of overwrite
- **Image association**: three-way matching engine auto-handles all file types. DISPIMG files require WPS format
- **Image performance**: Pre-store `image_path` in DB, read directly during quote generation. `--with-images` optional
- **Exchange rate**: live via `rates.convert()`, fallback to cache
- **FOB Incoterms 2020**: seller delivers onboard, does NOT arrange ocean freight
- **User ID**: 80 products stored under `user_id='ev_alls'`. Change with `--user-id`.
- **Translation**: Dictionary-based (no external API dependency). Trade-specific terms prioritized.
