#!/usr/bin/env python
# Test PDF parsing for images
import os
import sys

BASE_DIR = r'C:\Users\marky\Desktop\production tool\product_tool'
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from src.core.pdf_parser import extract_products_from_pdf_v2

# Test with e-motorcycle.pdf
pdf_path = 'data/新能源电动车/e-motorcycle.pdf'
if os.path.exists(pdf_path):
    df = extract_products_from_pdf_v2(pdf_path)
    print(f"PDF parsed: {len(df)} products")
    if '_image_path' in df.columns:
        for i, row in df.head(5).iterrows():
            img = row.get('_image_path', '')
            print(f"  {row['model']}: {img[:60] if img else '(empty)'}")
    else:
        print("No _image_path column!")
else:
    print(f"PDF not found: {pdf_path}")