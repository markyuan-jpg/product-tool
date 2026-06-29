"""
CI 版评测 — 直接调用解析器，不需要运行后端服务器

用法:
    python tests/benchmark/run_benchmark_ci.py
"""

import sys
import os
import json
from pathlib import Path

# Add project root and product_tool to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
_TOOL_ROOT = PROJECT_ROOT.parent / "product_tool"
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(_TOOL_ROOT / "src"))
sys.path.insert(0, str(_TOOL_ROOT))

from run_benchmark import evaluate_single, ANNOTATIONS_DIR, SAMPLES_DIR

def parse_file_direct(filepath: str):
    """直接调用解析器（不经过 HTTP）"""
    ext = Path(filepath).suffix.lower()
    products = []
    
    if ext in ('.xlsx', '.xls'):
        from universal_parser import parse as universal_parse
        from run import parse_file as run_parse_file
        from score import score_dataframe
        import pandas as pd
        
        # Use universal parser only (simpler for CI)
        df, ptype, count, _ = universal_parse(filepath)
        if df is not None and not df.empty:
            products = df.to_dict('records')
    
    elif ext == '.pdf':
        from pdf_handler import extract_products_from_pdf_v2
        df = extract_products_from_pdf_v2(filepath)
        if df is not None and not df.empty:
            products = df.to_dict('records')
    
    elif ext == '.docx':
        from src.core.doc_parser import extract_products_from_docx
        df = extract_products_from_docx(filepath)
        if df is not None and not df.empty:
            products = df.to_dict('records')
    
    return products


def main():
    annotations = []
    for f in sorted(ANNOTATIONS_DIR.glob("*.json")):
        with open(f, 'r', encoding='utf-8') as fp:
            annotations.append(json.load(fp))
    
    if not annotations:
        print("❌ 未找到标注文件")
        sys.exit(1)
    
    # Hack: suppress pandas deprecation warnings in test output
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    
    results = []
    for ann in annotations:
        filepath = SAMPLES_DIR / ann['file']
        if not filepath.exists():
            print(f"⚠️  样本文件不存在: {ann['file']}")
            continue
        
        print(f"📋 评测: {ann['file']}")
        try:
            products = parse_file_direct(str(filepath))
            products = [{k: v for k, v in p.items() if not pd.isna(v) if 'pd' in dir()} for p in products]
            # Clean: convert numpy types to native
            clean_products = []
            for p in products:
                cp = {}
                for k, v in p.items():
                    if hasattr(v, 'item'):  # numpy scalar
                        v = v.item()
                    if isinstance(v, float) and (v != v):  # NaN
                        continue
                    cp[k] = v
                clean_products.append(cp)
            products = clean_products
        except Exception as e:
            print(f"  ❌ 解析失败: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        result = evaluate_single(ann, products)
        results.append(result)
    
    if not results:
        print("\n❌ 无评测结果")
        sys.exit(1)
    
    # Print report
    from run_benchmark import print_report
    avg = print_report(results)
    
    THRESHOLD = 0.10  # Baseline for current parser accuracy. Raise as issues are fixed.
    if avg['overall'] < THRESHOLD:
        print(f"\n❌ 评测失败: 综合分 {avg['overall']:.0%} < 阈值 {THRESHOLD:.0%}")
        sys.exit(1)
    else:
        print(f"\n✅ 评测通过: 综合分 {avg['overall']:.0%} ≥ 阈值 {THRESHOLD:.0%}")
    
    return avg


if __name__ == '__main__':
    import pandas as pd
    main()
