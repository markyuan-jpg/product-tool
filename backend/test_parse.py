import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'product_tool'))

from universal_parser import parse
path = r'C:\Users\Administrator\Desktop\产品导入.xlsx'

df, ptype, count, ck = parse(path)
print(f'解析: {count} 产品\n')
for i, row in df.head(5).iterrows():
    m = str(row.get('model',''))[:25]
    n = str(row.get('name_zh',''))[:60]
    p = row.get('price_rmb')
    q = row.get('qty')
    has_dispimg = 'DISPIMG' in n.upper()
    print(f'  [{i}] model={m} | name={n} | dispimg?={has_dispimg} | price={p} | qty={q}')
