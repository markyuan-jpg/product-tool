#!/usr/bin/env python
# Test quote generation with image support
import os
import sys

# Add paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from src.product_manage import init_db, list_products
from src.output.quotation_excel import create_quotation_from_library

# Initialize DB
init_db()

# Get products
products = list_products(user_id='ev_test')
print(f"Products: {len(products)}")

# Select some products with images
sample_ids = []
sample_qtys = []
for p in products[:5]:
    sample_ids.append(p.id)
    sample_qtys.append(5)
    print(f"  {p.sku}: image_path = {p.image_path[:50] if p.image_path else '(empty)'}")

# Generate quotation
if sample_ids:
    output = create_quotation_from_library(
        product_ids=sample_ids,
        quantities=sample_qtys,
        output_path='output/test_with_images.xlsx',
        user_id='ev_test',
        image_search_dirs=['data/新能源电动车/images', 'data/新能源电动车', 'data'],
    )
    print(f"Quotation saved: {output}")