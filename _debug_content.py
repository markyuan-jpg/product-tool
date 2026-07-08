import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'product_tool'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'product_tool', 'src'))
from src.core.pdf_parser import extract_tables_from_pdf, _classify_pdf_columns, _parse_pdf_by_content, _score_pdf_result, _is_valid_pdf_model

f = r"C:\Users\Administrator\Desktop\sample quote.pdf"
tables = extract_tables_from_pdf(f)
for ti, t in enumerate(tables):
    data = t[0] if isinstance(t, tuple) else t
    if isinstance(data, dict):
        rows = data.get('rows', [])
    else:
        rows = data
    
    if not rows:
        print("Table %d: empty" % ti)
        continue
    
    print("Table %d: %d rows" % (ti, len(rows)))
    roles = _classify_pdf_columns(rows)
    print("Roles:", roles)
    
    df = _parse_pdf_by_content(rows)
    if df is not None and not df.empty:
        print("Products: %d rows" % len(df))
        print("Columns:", df.columns.tolist())
        score = _score_pdf_result(df, 'content')
        print("Score:", score)
        for i in range(min(3, len(df))):
            r = df.iloc[i]
            print("  [%d] model=%s, name=%s, price=%s, qty=%s" % (
                i, r.get('model',''), r.get('name',''), r.get('price',''), r.get('qty','')))
        
        # Check which models fail validation
        for i in range(len(df)):
            m = df.iloc[i].get('model', '')
            valid = _is_valid_pdf_model(m)
            if not valid:
                print("  [%d] INVALID model: '%s'" % (i, m[:60]))
    else:
        print("Products: NONE")
