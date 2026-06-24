import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool'))

from universal_parser import parse

path = r'C:\Users\Administrator\Desktop\产品导入.xlsx'
result = parse(path)
df, ptype, count, ck = result

print(f'类型: {ptype}, 产品数: {count}')
if df is not None and not df.empty:
    print(f'\n{list(df.columns)}')
    for i, row in df.head(10).iterrows():
        m = str(row.get('model',''))[:25]
        n = str(row.get('name_zh',''))[:40]
        p = row.get('price_rmb')
        q = row.get('qty')
        s = str(row.get('spec_zh',''))[:50]
        print(f'  [{i}] {m} | {p} | qty={q} | {n} | {s}')
else:
    print('空!')
