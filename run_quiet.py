# -*- coding: utf-8 -*-
import sys
import os
import shutil

# Add path
basedir = r"C:\Users\marky\Desktop\production tool\product_tool"
sys.path.insert(0, basedir)

# Clean output folder first
output_dir = os.path.join(basedir, "output")
if os.path.exists(output_dir):
    for f in os.listdir(output_dir):
        if f.endswith('.xlsx'):
            try:
                os.remove(os.path.join(output_dir, f))
            except:
                pass

output_lines = []

try:
    from src.core.parser import load_documents
    output_lines.append("Loading PDF files...")
    df = load_documents('./data', 7.2, file_type='pdf', fetch_rate=False)
    output_lines.append(f"Total products: {len(df)}")
    output_lines.append(f"Columns: {df.columns.tolist()}")
    
    # Show first few rows
    output_lines.append("\n=== Sample Data (first 3) ===")
    if not df.empty:
        for idx, row in df.head(3).iterrows():
            name = row.get('name_zh', '') or ''
            model = row.get('model', '') or ''
            output_lines.append(f"  {model} | {name}")
    
    # Generate Excel - using original data as Chinese version
    # (since PDF content IS in Chinese in some fields)
    output_lines.append("\n=== Generating Excel files ===")
    from src.output.excel_writer import save_all_outputs
    saved = save_all_outputs(df, './output', with_price=True, without_price=True)
    output_lines.append(f"Saved {len(saved)} files:")
    for f in saved:
        output_lines.append(f"  {os.path.basename(f)}")
        
    output_lines.append("\n=== DONE ===")
        
except Exception as e:
    output_lines.append(f"ERROR: {str(e)}")
    import traceback
    output_lines.append(traceback.format_exc())

# Write to output folder
outfile = os.path.join(basedir, "output", "test_result.txt")
with open(outfile, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print("Done - check output/test_result.txt")