#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Product CLI - Product Library Command Line Interface

交互式从产品库选品生成报价单
"""
import os
import sys
import argparse
from typing import List, Dict, Optional

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.product_manage import init_db, list_products, get_product_by_sku, get_categories
from src.output.quotation_excel import create_quotation_from_library
from src.output.pi_generator import generate_pi
from src.packing.generator import generate_packing_list, generate_commercial_invoice
from src.config import DEFAULT_SELLER_INFO


def parse_sku_list(sku_str: str) -> List[str]:
    """Parse SKU list from comma-separated string"""
    return [s.strip() for s in sku_str.split(',') if s.strip()]


def parse_quantity_list(qty_str: str) -> List[int]:
    """Parse quantity list from comma-separated string"""
    result = []
    for s in qty_str.split(','):
        s = s.strip()
        try:
            result.append(int(s))
        except ValueError:
            result.append(1)
    return result


def select_interactive(user_id: str = 'local') -> tuple:
    """Interactive product selection"""
    print("\n=== Product Library Selection ===\n")
    
    categories = get_categories(user_id)
    
    # Show categories
    print("Categories:")
    print("  0. All products")
    for i, cat in enumerate(categories, 1):
        print(f"  {i}. {cat}")
    
    choice = input("\nSelect category (number): ").strip()
    try:
        cat_idx = int(choice) if choice else 0
    except ValueError:
        cat_idx = 0
    
    category = categories[cat_idx - 1] if 0 < cat_idx <= len(categories) else None
    
    # List products
    products = list_products(category=category, user_id=user_id, limit=100)
    
    print(f"\n--- Products ({len(products)}) ---")
    for i, p in enumerate(products, 1):
        print(f"  {i:2}. {p.sku:15} | {p.name_zh[:30]:30} | ¥{p.price_rmb:,.0f}")
    
    print("\nEnter product numbers (e.g., 1,3-5,7 or all): ")
    sel = input("> ").strip().lower()
    
    product_ids = []
    quantities = []
    
    if sel == 'all':
        for p in products:
            product_ids.append(p.id)
            quantities.append(1)
    else:
        parts = sel.replace(',', ' ').split()
        parsed_indices = []
        for part in parts:
            if '-' in part:
                parts_range = part.split('-')
                if len(parts_range) != 2:
                    continue
                start, end = parts_range
                parsed_indices.extend(range(int(start), int(end) + 1))
            else:
                parsed_indices.append(int(part))
        
        # Convert 1-based display indices to actual DB IDs
        for idx in parsed_indices:
            if 1 <= idx <= len(products):
                product_ids.append(products[idx - 1].id)
        
        # Ask quantities
        print("\nEnter quantities (comma-separated, default=1): ")
        qty_input = input("> ").strip()
        if qty_input:
            quantities = parse_quantity_list(qty_input)
        else:
            quantities = [1] * len(product_ids)
    
    return product_ids, quantities


def select_from_excel(order_file: str, user_id: str = 'local') -> tuple:
    """Load selection from Excel order file"""
    import pandas as pd
    
    df = pd.read_excel(order_file)
    
    # Find columns
    sku_col = None
    qty_col = None
    
    for col in df.columns:
        col_lower = str(col).lower()
        if 'sku' in col_lower or 'model' in col_lower:
            sku_col = col
        if 'qty' in col_lower or 'quantity' in col_lower or '数量' in col_lower:
            qty_col = col
    
    if sku_col is None:
        raise ValueError("Excel must have 'sku' or 'model' column")
    
    if qty_col is None:
        df['quantity'] = 1
    else:
        df['quantity'] = df[qty_col].fillna(1).astype(int)
    
    product_ids = []
    quantities = []
    not_found = []
    
    for _, row in df.iterrows():
        sku = str(row[sku_col]).strip()
        product = get_product_by_sku(sku, user_id)
        
        if product:
            product_ids.append(product.id)
            quantities.append(row['quantity'])
        else:
            not_found.append(sku)
    
    if not_found:
        print(f"Warning: {len(not_found)} SKUs not found: {not_found}")
    
    return product_ids, quantities


def select_from_cli(sku_list: str, qty_list: str, user_id: str = 'local') -> tuple:
    """Direct CLI SKU selection"""
    skus = parse_sku_list(sku_list)
    quantities = parse_quantity_list(qty_list) if qty_list else [1] * len(skus)
    
    # Support "all" keyword
    if skus == ['all']:
        from src.product_manage import list_products
        all_products = list_products(user_id=user_id, limit=1000)
        product_ids = [p.id for p in all_products]
        quantities = [1] * len(product_ids)
        return product_ids, quantities
    
    # Extend quantities if needed
    while len(quantities) < len(skus):
        quantities.append(1)
    
    product_ids = []
    not_found = []
    filtered_quantities = []
    
    for i, sku in enumerate(skus):
        product = get_product_by_sku(sku, user_id)
        if product:
            product_ids.append(product.id)
            filtered_quantities.append(quantities[i] if i < len(quantities) else 1)
        else:
            not_found.append(sku)
    
    if not_found:
        print(f"Error: {len(not_found)} SKUs not found: {not_found}")
        return [], []
    
    return product_ids, filtered_quantities


DEFAULT_IMAGE_DIRS = ['data/新能源电动车/images', 'data/新能源电动车', 'data']


def generate_quotation(
    product_ids: List[int],
    quantities: List[int],
    output_path: str,
    user_id: str = 'local',
    currency: str = 'RMB',
    trade_terms: str = 'FOB Qingdao',
    payment_terms: str = 'T/T 30% deposit + 70% before shipment',
    image_search_dirs: list = None,
    with_images: bool = False,
    lang: str = 'chinese',
    industry: str = None,
    include_optional: bool = True,
) -> str:
    """Generate quotation from selected products"""
    if not product_ids:
        print("No products selected!")
        return ""
    
    print(f"\nGenerating quotation...")
    print(f"  Products: {len(product_ids)}")
    print(f"  Currency: {currency}")
    print(f"  Terms: {trade_terms}")
    print(f"  Language: {lang}")
    
    if image_search_dirs is None:
        image_search_dirs = DEFAULT_IMAGE_DIRS
    
    output = create_quotation_from_library(
        product_ids=product_ids,
        quantities=quantities,
        output_path=output_path,
        user_id=user_id,
        currency=currency,
        trade_terms=trade_terms,
        payment_terms=payment_terms,
        use_term_calculation=True,
        image_search_dirs=image_search_dirs,
        with_images=with_images,
        lang=lang,
        industry=industry,
        include_optional=include_optional,
    )
    
    print(f"\n-- Quotation saved: {output}")
    return output


# ─── 文档生成辅助函数（消除三模式重复） ───

def _build_items_from_ids(product_ids, quantities, user_id):
    """从产品 ID 列表构建 (pi_data, pi_items) 用于文档生成"""
    from src.product_manage.repository import get_products_by_ids
    prods = get_products_by_ids(product_ids, user_id, order_by_source=True)
    pi_data = []
    pi_items = []
    for pid, qty in zip(product_ids, quantities):
        p = prods.get(pid)
        if p:
            def _price(p):
                return p.price_usd or (p.price_rmb / 7.2 if p.price_rmb else 0)
            pi_data.append({
                'model': p.sku, 'name_zh': p.name_zh, 'spec_zh': p.spec_zh,
                'quantity': qty, 'price_usd': _price(p),
            })
            pi_items.append({
                'model': p.sku, 'name_zh': p.name_zh, 'spec_zh': p.spec_zh,
                'quantity': qty, 'unit_price': _price(p),
            })
    return pi_data, pi_items


def _generate_pi(product_ids, quantities, user_id, quote_path):
    """生成 PI (Proforma Invoice) PDF"""
    if not product_ids:
        return
    try:
        pi_data, _ = _build_items_from_ids(product_ids, quantities, user_id)
        if not pi_data:
            return
        import pandas as pd
        pi_df = pd.DataFrame(pi_data)
        buyer_info = {'company': 'Buyer', 'address': '', 'contact': ''}
        pi_path = quote_path.replace('.xlsx', '_PI.pdf')
        result = generate_pi(pi_df, buyer_info, DEFAULT_SELLER_INFO, pi_path, use_rmb=False)
        if result:
            print(f"  PI saved: {result}")
    except Exception as e:
        print(f"  PI generation skipped: {e}")


def _generate_packing(product_ids, quantities, user_id, quote_path,
                      buyer_name='', buyer_address='', destination='', port=''):
    """生成 Packing List + Commercial Invoice"""
    if not product_ids:
        return
    try:
        _, pi_items = _build_items_from_ids(product_ids, quantities, user_id)
        if not pi_items:
            return
        from datetime import datetime
        inv_no = datetime.now().strftime('INV%Y%m%d%H%M%S')
        base = quote_path.replace('.xlsx', '')
        p_result = generate_packing_list(
            pi_items, inv_no, datetime.now().strftime('%Y-%m-%d'),
            buyer_name=buyer_name, buyer_address=buyer_address,
            output_path=base + '_PackingList.xlsx'
        )
        if p_result:
            print(f"  Packing list saved: {p_result}")
        c_result = generate_commercial_invoice(
            pi_items, inv_no, datetime.now().strftime('%Y-%m-%d'),
            buyer_name=buyer_name, buyer_address=buyer_address,
            destination_country=destination, port_of_loading=port,
            output_path=base + '_Invoice.xlsx'
        )
        if c_result:
            print(f"  Commercial invoice saved: {c_result}")
    except Exception as e:
        print(f"  Packing/Invoice generation skipped: {e}")


def _generate_pdf(product_ids, quantities, user_id, quote_path):
    """生成 PDF 报价单"""
    if not product_ids:
        return
    try:
        from datetime import datetime
        from weasyprint import HTML
        pi_data, _ = _build_items_from_ids(product_ids, quantities, user_id)
        if not pi_data:
            return
        rows_html = ''
        for item in pi_data:
            rows_html += f'<tr><td>{item["model"]}</td><td>{item["name_zh"]}</td><td>{item["spec_zh"]}</td><td>{item["quantity"]}</td><td>${item["price_usd"]:.2f}</td></tr>'
        html = f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
h1 {{ text-align: center; color: #1a5fb4; }}
table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
th {{ background: #4472C4; color: white; padding: 8px; border: 1px solid #ccc; }}
td {{ padding: 6px 8px; border: 1px solid #ccc; }}
</style></head><body>
<h1>Quotation</h1>
<p>Date: {datetime.now().strftime("%Y-%m-%d")}</p>
<table><tr><th>Model</th><th>Name</th><th>Spec</th><th>Qty</th><th>Unit Price</th></tr>{rows_html}</table>
</body></html>'''
        pdf_path = quote_path.replace('.xlsx', '_Quote.pdf')
        HTML(string=html).write_pdf(pdf_path)
        print(f"  PDF saved: {pdf_path}")
    except ImportError:
        print(f"  PDF skipped: weasyprint not installed")
    except Exception as e:
        print(f"  PDF skipped: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Product Library CLI - Select products and generate quotations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive selection
  python product_cli.py select

  # Direct CLI selection
  python product_cli.py --sku XP,BOX,M6 --quantity 10,5,2 --quote quote.xlsx

  # Excel batch selection
  python product_cli.py --order-file order.xlsx --quote output.xlsx

  # List products
  python product_cli.py list
  python product_cli.py list --category 电动车
        """
    )
    
    # Selection mode
    parser.add_argument('--select', action='store_true', help='Interactive selection mode')
    parser.add_argument('--sku', type=str, help='Comma-separated SKU list')
    parser.add_argument('--quantity', type=str, help='Comma-separated quantity list')
    parser.add_argument('--order-file', type=str, help='Excel file with sku/quantity columns')
    
    # Quotation options
    parser.add_argument('--quote', type=str, default='output/quotation.xlsx', help='Output quotation file')
    parser.add_argument('--currency', type=str, default='RMB', choices=['RMB', 'USD', 'CNY'], help='Currency')
    parser.add_argument('--trade-terms', type=str, default='FOB Qingdao', help='Trade terms')
    parser.add_argument('--payment-terms', type=str, default='T/T 30% deposit + 70% before shipment', help='Payment terms')
    parser.add_argument('--with-images', action='store_true', help='Embed real images (slow for 20+ products)')
    parser.add_argument('--industry', type=str, default=None, help='Industry for price config (ev/medical/general)')
    parser.add_argument('--no-optional', action='store_true', help='Exclude optional accessory prices from total')
    
    # Language
    parser.add_argument('--lang', type=str, default='chinese', choices=['chinese', 'english', 'bilingual'],
                       help='Output language (default: chinese)')
    parser.add_argument('--pi', action='store_true', help='Also generate Proforma Invoice PDF')
    parser.add_argument('--packing', action='store_true', help='Also generate packing list + commercial invoice')
    parser.add_argument('--pdf', action='store_true', help='Also generate PDF quotation')
    
    # Buyer info for invoices
    parser.add_argument('--buyer', type=str, default='', help='Buyer company name')
    parser.add_argument('--buyer-address', type=str, default='', help='Buyer address')
    parser.add_argument('--destination', type=str, default='Uganda', help='Destination country (default: Uganda)')
    parser.add_argument('--port', type=str, default='Qingdao, China', help='Port of loading (default: Qingdao, China)')

    # Other modes
    parser.add_argument('--list', action='store_true', help='List all products')
    parser.add_argument('--category', type=str, help='Filter by category')
    parser.add_argument('--user-id', type=str, default='ev_alls', help='User ID (default: ev_alls)')
    parser.add_argument('--image-dir', type=str, help='Image search directory (default: data/新能源电动车/images)')
    
    args = parser.parse_args()
    
    # Initialize DB
    init_db()
    
    # List mode
    if args.list:
        products = list_products(category=args.category, user_id=args.user_id, limit=100)
        print(f"\n=== Products ({len(products)}) ===")
        for p in products:
            print(f"  {p.sku:15} | {p.name_zh[:30]:30} | {p.price_rmb:,.0f} | {p.category}")
        return
    
    # Interactive selection
    if args.select:
        product_ids, quantities = select_interactive(args.user_id)
        if product_ids:
            generate_quotation(
                product_ids, quantities, args.quote, args.user_id,
                args.currency, args.trade_terms, args.payment_terms,
                with_images=args.with_images, lang=args.lang,
                industry=args.industry, include_optional=not args.no_optional,
            )
            _generate_pi(product_ids, quantities, args.user_id, args.quote) if args.pi else None
            _generate_packing(product_ids, quantities, args.user_id, args.quote,
                              args.buyer, args.buyer_address, args.destination, args.port) if args.packing else None
            _generate_pdf(product_ids, quantities, args.user_id, args.quote) if args.pdf else None
        return
    
    # Direct CLI selection
    if args.sku:
        product_ids, quantities = select_from_cli(args.sku, args.quantity or '', args.user_id)
        if product_ids:
            image_dirs = [args.image_dir] if args.image_dir else DEFAULT_IMAGE_DIRS
            generate_quotation(
                product_ids, quantities, args.quote, args.user_id,
                args.currency, args.trade_terms, args.payment_terms,
                image_search_dirs=image_dirs, with_images=args.with_images,
                lang=args.lang,
                industry=args.industry, include_optional=not args.no_optional,
            )
            _generate_pi(product_ids, quantities, args.user_id, args.quote) if args.pi else None
            _generate_packing(product_ids, quantities, args.user_id, args.quote,
                              args.buyer, args.buyer_address, args.destination, args.port) if args.packing else None
            _generate_pdf(product_ids, quantities, args.user_id, args.quote) if args.pdf else None
        return
    
    # Excel batch selection
    if args.order_file:
        product_ids, quantities = select_from_excel(args.order_file, args.user_id)
        if product_ids:
            generate_quotation(
                product_ids, quantities, args.quote, args.user_id,
                args.currency, args.trade_terms, args.payment_terms,
                with_images=args.with_images, lang=args.lang,
                industry=args.industry, include_optional=not args.no_optional,
            )
            _generate_pi(product_ids, quantities, args.user_id, args.quote) if args.pi else None
            _generate_packing(product_ids, quantities, args.user_id, args.quote,
                              args.buyer, args.buyer_address, args.destination, args.port) if args.packing else None
            _generate_pdf(product_ids, quantities, args.user_id, args.quote) if args.pdf else None
        return
    
    # Default: show help
    parser.print_help()


if __name__ == '__main__':
    main()