"""
解析准确率评测脚本

用法:
    python tests/benchmark/run_benchmark.py
    python tests/benchmark/run_benchmark.py --ci     # CI 模式: 低于阈值 exit 1
    
评测指标:
    - 产品数量匹配率
    - 型号提取率
    - 价格提取率 (容差 ±N%)
    - 规格关键词覆盖率
    - 综合得分
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

SAMPLES_DIR = Path(__file__).parent / "samples"
ANNOTATIONS_DIR = Path(__file__).parent / "annotations"

# ─── 评测指标 ───

def fuzzy_match(expected: str, actual: str) -> bool:
    """模糊匹配: 忽略大小写和空格"""
    if not actual:
        return False
    return expected.lower().strip() == actual.lower().strip()

def price_match(expected: float, actual: float, tolerance_pct: float = 5) -> bool:
    """价格匹配: 允许 ±tolerance% 误差"""
    if actual == 0 and expected == 0:
        return True
    if actual == 0 or expected == 0:
        return False
    diff_pct = abs(actual - expected) / expected * 100
    return diff_pct <= tolerance_pct

def spec_coverage(expected_keywords: list, actual_spec: str) -> float:
    """规格关键词覆盖率: 期望关键词在实际规格中出现的比例"""
    if not expected_keywords or not actual_spec:
        return 0.0
    actual_lower = actual_spec.lower()
    matched = sum(1 for kw in expected_keywords if kw.lower() in actual_lower)
    return matched / len(expected_keywords)

def name_match(expected_keywords: list, actual_name: str) -> bool:
    """产品名匹配: 至少一个关键词匹配"""
    if not expected_keywords or not actual_name:
        return False
    actual_lower = actual_name.lower()
    return any(kw.lower() in actual_lower for kw in expected_keywords)


# ─── 评测核心 ───

def evaluate_single(annotation: dict, products: list) -> dict:
    """评测单个文件的解析结果
    
    Returns:
        dict with scores per metric
    """
    expected = annotation['expected_products']
    expected_count = annotation.get('expected_product_count', len(expected))
    actual_count = len(products)
    
    # 1. 产品数量
    count_score = 1.0 if actual_count == expected_count else (
        0.5 if abs(actual_count - expected_count) == 1 else 0.0
    )
    
    # 2-4. 逐产品匹配
    model_matches = 0
    price_matches = 0
    name_matches = 0
    spec_scores = []
    
    for exp_p in expected:
        model = exp_p.get('model', '')
        price = exp_p.get('price_rmb', 0)
        tolerance = exp_p.get('price_tolerance', 5)
        name_kw = exp_p.get('name_keywords', [])
        spec_kw = exp_p.get('spec_keywords', [])
        
        # Find best matching product
        best_prod = None
        for p in products:
            if fuzzy_match(model, p.get('model', '')):
                best_prod = p
                break
        
        if best_prod:
            model_matches += 1
            if price_match(price, best_prod.get('price_rmb', 0), tolerance):
                price_matches += 1
            if name_match(name_kw, best_prod.get('name_zh', '') or best_prod.get('name', '')):
                name_matches += 1
            spec_scores.append(spec_coverage(spec_kw, best_prod.get('spec_zh', '') or best_prod.get('spec', '')))
        else:
            spec_scores.append(0.0)
    
    n = len(expected) if expected else 1
    model_rate = model_matches / n
    price_rate = price_matches / n
    name_rate = name_matches / n
    spec_rate = sum(spec_scores) / n if spec_scores else 0
    
    # 综合得分: 型号 35% + 价格 30% + 数量 15% + 规格 15% + 品名 5%
    overall = model_rate * 0.35 + price_rate * 0.30 + count_score * 0.15 + spec_rate * 0.15 + name_rate * 0.05
    
    return {
        "file": annotation['file'],
        "description": annotation.get('description', ''),
        "expected_count": expected_count,
        "actual_count": actual_count,
        "count_score": round(count_score, 2),
        "model_rate": round(model_rate, 2),
        "price_rate": round(price_rate, 2),
        "name_rate": round(name_rate, 2),
        "spec_coverage": round(spec_rate, 2),
        "overall": round(overall, 2),
    }


def run_benchmark():
    """批量评测所有样本"""
    annotations = []
    for f in sorted(ANNOTATIONS_DIR.glob("*.json")):
        with open(f, 'r', encoding='utf-8') as fp:
            annotations.append(json.load(fp))
    
    if not annotations:
        print("[ERROR] No annotation files found")
        return None
    
    import httpx
    import asyncio
    
    async def _run():
        results = []
        async with httpx.AsyncClient(base_url="http://127.0.0.1:8000") as client:
            for ann in annotations:
                filepath = SAMPLES_DIR / ann['file']
                if not filepath.exists():
                    print(f"  [WARN] Sample file missing: {ann['file']}")
                    continue
                
                print(f"[PARSE] {ann['file']} — {ann.get('description', '')}")
                
                with open(filepath, 'rb') as f:
                    files = {'file': (ann['file'], f, 'application/octet-stream')}
                    try:
                        resp = await client.post("/api/parse", files=files, timeout=180)
                        if resp.status_code == 200:
                            data = resp.json()
                            products = data.get('products', [])
                            result = evaluate_single(ann, products)
                            results.append(result)
                        else:
                            print(f"  [ERR] HTTP {resp.status_code}: {resp.text[:200]}")
                    except Exception as e:
                        print(f"  [ERR] Request failed: {e}")
        
        return results
    
    return asyncio.run(_run())


def print_report(results: list) -> dict:
    """打印评测报告，返回汇总"""
    if not results:
        print("\n[ERR] No benchmark results")
        return {"overall": 0}
    
    print("\n" + "=" * 70)
    print("  Parse Accuracy Benchmark Report")
    print("=" * 70)
    print(f"{'File':<25} {'Count':>4} {'Model':>6} {'Price':>6} {'Spec':>6} {'Overall':>6}")
    print("-" * 70)
    
    for r in results:
        status = "PASS" if r['overall'] >= 0.70 else "WARN" if r['overall'] >= 0.50 else "FAIL"
        print(f"{status} {r['file']:<22} {r['actual_count']:>3}/{r['expected_count']:<3} {r['model_rate']:.0%} {r['price_rate']:.0%} {r['spec_coverage']:.0%} {r['overall']:.0%}")
    
    # Overall averages
    avg = {
        "count_score": sum(r['count_score'] for r in results) / len(results),
        "model_rate": sum(r['model_rate'] for r in results) / len(results),
        "price_rate": sum(r['price_rate'] for r in results) / len(results),
        "spec_coverage": sum(r['spec_coverage'] for r in results) / len(results),
        "overall": sum(r['overall'] for r in results) / len(results),
        "files_tested": len(results),
    }
    
    print("-" * 70)
    print(f"  [AVG] ({len(results)} files): Count{avg['count_score']:.0%} Model{avg['model_rate']:.0%} Price{avg['price_rate']:.0%} Spec{avg['spec_coverage']:.0%} -> Overall {avg['overall']:.0%}")
    print("=" * 70)
    
    return avg


# ─── 阈值配置 ───

CI_THRESHOLD = 0.60  # CI 模式下综合分低于 60% 视为失败


def main():
    parser = argparse.ArgumentParser(description="解析准确率评测")
    parser.add_argument("--ci", action="store_true", help="CI 模式: 低于阈值 exit 1")
    parser.add_argument("--threshold", type=float, default=CI_THRESHOLD, help=f"CI 阈值 (默认 {CI_THRESHOLD})")
    args = parser.parse_args()
    
    # 检查后端是否运行
    import httpx
    try:
        resp = httpx.get("http://127.0.0.1:8000/api/health", timeout=5)
        if resp.status_code != 200:
            print("[WARN] Backend not ready, start with: uvicorn main:app")
            if args.ci:
                sys.exit(1)
            return
    except Exception:
        print("[WARN] Backend not running, start with: uvicorn main:app")
        if args.ci:
            sys.exit(1)
        return
    
    results = run_benchmark()
    if results is None:
        if args.ci:
            sys.exit(1)
        return
    
    avg = print_report(results)
    
    # Save JSON report
    report_path = Path(__file__).parent / "benchmark_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({"results": results, "averages": avg, "threshold": args.threshold}, f, ensure_ascii=False, indent=2)
    print(f"\n[REPORT] Report saved: {report_path}")
    
    # CI check
    if args.ci:
        if avg['overall'] < args.threshold:
            print(f"\n[ERR] CI FAIL: Overall {avg['overall']:.0%} < threshold {args.threshold:.0%}")
            sys.exit(1)
        else:
            print(f"\n[OK] CI 通过: 综合分 {avg['overall']:.0%} ≥ 阈值 {args.threshold:.0%}")


if __name__ == '__main__':
    main()
