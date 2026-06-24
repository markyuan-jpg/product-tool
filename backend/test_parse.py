import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool'))

from src.core.image import match_images_to_products
from universal_parser import parse
import time

path = r'C:\Users\Administrator\Desktop\产品导入.xlsx'

# Parse + match images
start = time.time()
df, ptype, count, ck = parse(path)
df_img = match_images_to_products(df, path)
elapsed = time.time() - start

print(f'解析+图片匹配: {elapsed:.1f}s')
print(f'产品数: {count}')

# Count products with images
n_with_img = sum(1 for _, r in df_img.iterrows() if r.get('_image_path'))
n_with_both = sum(1 for _, r in df_img.iterrows() 
                  if '||' in str(r.get('_image_path', '')))

print(f'有图片的产品: {n_with_img}/{len(df_img)}')
print(f'有双图片(picture+drawing)的产品: {n_with_both}/{len(df_img)}')

# Show first 5
for i, row in df_img.head(5).iterrows():
    m = str(row.get('model',''))[:20]
    img = str(row.get('_image_path',''))
    parts = img.split('||')
    print(f'  [{i}] {m}')
    for pi, p in enumerate(parts):
        print(f'       img{pi+1}: {p[:80]}')

# Count total unique images
all_paths = set()
for _, r in df_img.iterrows():
    img = str(r.get('_image_path',''))
    for p in img.split('||'):
        if p and p != 'nan':
            all_paths.add(p)
print(f'\n不重复图片文件数: {len(all_paths)}')
