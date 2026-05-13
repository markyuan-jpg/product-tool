#!/usr/bin/env python
# Test Excel image extraction
import os
import sys

BASE_DIR = r'C:\Users\marky\Desktop\production tool\product_tool'
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from src.core.excel_parser_v3 import parse_excel_v3
from src.parsers.param_price_parser import parse_param_price

# Test param_price.xlsx
xlsx_path = 'data/新能源电动车/param_price.xlsx'
if os.path.exists(xlsx_path):
    df = parse_excel_v3(xlsx_path)
    print(f"Excel parsed (parse_excel_v3): {len(df)} products")
    if '_image_path' in df.columns:
        for i, row in df.head(5).iterrows():
            img = row.get('_image_path', '')
            print(f"  {row.get('model', 'N/A')}: {img[:60] if img else '(empty)'}")

# Also test parse_param_price directly
df2 = parse_param_price(xlsx_path)
print(f"\nparse_param_price: {len(df2)} products")
if '_image_path' in df2.columns:
    for i, row in df2.head(5).iterrows():
        img = row.get('_image_path', '')
        print(f"  {row.get('model', 'N/A')}: {img[:60] if img else '(empty)'}")