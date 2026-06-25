import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool'))

from src.core.image import match_images_to_products, extract_embedded_images
from universal_parser import parse

path = r'C:\Users\Administrator\Desktop\产品导入.xlsx'

# Extract all images
imgs = extract_embedded_images(path)
for sheet, rows in imgs.items():
    for r, paths in sorted(rows.items()):
        parts = paths.split('||')
        unique = set(parts)
        if len(parts) >= 2 and len(unique) == 1:
            print(f'DUPE ROW {r}: {len(parts)} paths, all SAME!')
        elif len(parts) >= 2:
            print(f'OK   ROW {r}: {len(parts)} paths, {len(unique)} unique')

print(f'\nTotal rows with images: {sum(len(v) for v in imgs.values())}')
