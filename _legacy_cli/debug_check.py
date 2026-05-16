# -*- coding: utf-8 -*-
from src.core.parser import load_documents
df = load_documents('./data', 7.2, file_type='pdf')

print('=== DataFrame shape ===')
print(df.shape)
print()

print('=== Columns ===')
print(df.columns.tolist())
print()

print('=== Model column (first 25 rows) ===')
if 'model' in df.columns:
    for i, m in enumerate(df['model'].head(25)):
        print(f'{i}: |{m}|')

print()
print('=== Price USD (first 25 rows) ===')
if 'price_usd' in df.columns:
    for i, p in enumerate(df['price_usd'].head(25)):
        print(f'{i}: |{p}|')