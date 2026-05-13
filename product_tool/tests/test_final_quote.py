#!/usr/bin/env python
# Test final quote with images embedded
import os
import sys

BASE_DIR = r'C:\Users\marky\Desktop\production tool\product_tool'
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from src.product_manage import init_db, list_products
from src.output.quotation_excel import create_quotation_from_library

init_db()

products = list_products(user_id='ev_done_final')
print(f"Products: {len(products)}")
with_images = sum(1 for p in products if p.image_path)
print(f"With images: {with_images}")

# 生成报价 (前10个产品)
sample = products[:10]
output = create_quotation_from_library(
    product_ids=[p.id for p in sample],
    quantities=[5] * len(sample),
    output_path='output/ev_done_final_quote.xlsx',
    user_id='ev_done_final',
)
print(f"Quote: {output}")