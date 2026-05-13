import sys
sys.path.insert(0, 'C:/Users/marky/Desktop/production tool/product_tool')

print("=" * 50)
print("Phase 3 Test - Rates + Terms")
print("=" * 50)

# Test 1: Rates
print("\n[Test 1] Exchange rates...")
from src.rates import get_rate, convert, format_price, get_available_currencies

currencies = get_available_currencies()
print(f"  Available: {currencies}")

rate = get_rate('USD', 'CNY')
print(f"  USD -> CNY: {rate}")

converted = convert(1000, 'USD', 'CNY')
print(f"  1000 USD = {converted} CNY")

formatted = format_price(1234.56, 'USD')
print(f"  Format: {formatted}")

print("  OK: Rates working")

# Test 2: Trade Terms
print("\n[Test 2] Trade terms...")
from src.terms import calculate_price, get_term_info, get_common_terms

terms = get_common_terms()
print(f"  Terms: {terms}")

info = get_term_info('FOB')
print(f"  FOB: {info['name']}")

calc_cif = calculate_price(5000, 10, 'CIF', volume_cbm=2.5)
print(f"  CIF 50k×10: {calc_cif.total:.2f} CNY")

print("  OK: Terms working")

# Test 3: Quotation with terms
print("\n[Test 3] Quotation with terms...")
from src.product_manage.repository import list_products
from src.output.quotation_excel import create_quotation_from_library

products = list_products()
if products:
    product_ids = [p.id for p in products[:2]]
    quantities = [10, 5]
    
    output_fob = "C:/Users/marky/Desktop/production tool/product_tool/output/test_quotation_fob.xlsx"
    create_quotation_from_library(
        product_ids=product_ids,
        quantities=quantities,
        output_path=output_fob,
        use_term_calculation=True,
        trade_terms='FOB',
        volume_cbm=2.0,
    )
    print(f"  FOB: {output_fob}")
    
    output_cif = "C:/Users/marky/Desktop/production tool/product_tool/output/test_quotation_cif.xlsx"
    create_quotation_from_library(
        product_ids=product_ids,
        quantities=quantities,
        output_path=output_cif,
        use_term_calculation=True,
        trade_terms='CIF',
        volume_cbm=2.0,
    )
    print(f"  CIF: {output_cif}")
    
    print("  OK: Quotation with terms")
else:
    print("  SKIP: No products")

print("\n" + "=" * 50)
print("Phase 3 TESTS COMPLETE!")
print("=" * 50)