# -*- coding: utf-8 -*-
"""
Phase 1-2 Test Script

Tests: product library + quotation from library
"""
import sys
import os
sys.path.insert(0, 'C:/Users/marky/Desktop/production tool/product_tool')

print("=" * 50)
print("Phase 1-2 Integration Test")
print("=" * 50)

# Test 1: Product DB
print("\n[Test 1] Initialize DB...")
from src.product_manage.db import get_db_path, init_db
print(f"  DB path: {get_db_path()}")
init_db()
print("  OK: DB initialized")

# Test 2: Company Config
print("\n[Test 2] Company config...")
from src.company import init_company_config, load_company, save_company
config = init_company_config(overwrite=True)
config["name"] = "SONLINK E-MOTORCYCLE CO., LTD"
config["name_en"] = "SONLINK E-MOTORCYCLE CO., LTD"
config["address"] = "NO.576 Fengyi Road, Fengxian, Jiangsu, China"
config["tel"] = "+86-13926156666"
config["email"] = "gwlong926@163.com"
save_company(config)
loaded = load_company()
print(f"  Company: {loaded['name']}")
print("  OK: Company config saved")

# Test 3: Import from parsed data
print("\n[Test 3] Import products...")
from src.parsers.param_price_parser import parse_table
from src.product_manage.importer import import_from_df

file_path = 'C:/Users/marky/Desktop/production tool/product_tool/data/新能源电动车/车型价格表EXW、FOB价（26年2月）的副本.xlsx'
df = parse_table(file_path)
print(f"  Parsed: {len(df)} rows")

result = import_from_df(df, category="电动车")
print(f"  Import result: {result}")
print("  OK: Products imported")

# Test 4: List products
print("\n[Test 4] List products...")
from src.product_manage.repository import list_products, search_products, get_categories

products = list_products()
print(f"  Total: {len(products)} products")
categories = get_categories()
print(f"  Categories: {categories}")
if products:
    p = products[0]
    print(f"  First: sku={p.sku}, price_rmb={p.price_rmb}")
print("  OK: Products listed")

# Test 5: Search
print("\n[Test 5] Search products...")
results = search_products("BOX")
print(f"  Search 'BOX': {len(results)} results")
print("  OK: Search works")

# Test 6: Export
print("\n[Test 6] Export to Excel...")
from src.product_manage.exporter import export_to_excel
output_path = "C:/Users/marky/Desktop/production tool/product_tool/output/test_products.xlsx"
export_to_excel(output_path)
print(f"  Exported: {output_path}")
print("  OK: Export works")

# Test 7: Quotation from library
print("\n[Test 7] Quotation from library...")
from src.output.quotation_excel import create_quotation_from_library

if products:
    # Use first 2 products
    product_ids = [p.id for p in products[:2]]
    quantities = [10, 5]
    output_path = "C:/Users/marky/Desktop/production tool/product_tool/output/test_quotation_from_lib.xlsx"
    
    create_quotation_from_library(
        product_ids=product_ids,
        quantities=quantities,
        output_path=output_path,
        currency='RMB',
    )
    print(f"  Created: {output_path}")
    print("  OK: Quotation from library")

print("\n" + "=" * 50)
print("ALL TESTS PASSED!")
print("=" * 50)