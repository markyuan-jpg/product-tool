import sys
sys.path.insert(0, 'C:/Users/marky/Desktop/production tool/product_tool')

print("=" * 50)
print("Phase 4 Test - Packing List + Commercial Invoice")
print("=" * 50)

# Test data - simulate PI items
test_items = [
    {'model': 'BOX', 'quantity': 10, 'unit_price': 680.0, 'specs': '3000W Motor'},
    {'model': 'M6', 'quantity': 5, 'unit_price': 764.0, 'specs': '4000W Motor'},
]

# Test 1: Packing List
print("\n[Test 1] Generate Packing List...")
from src.packing.generator import generate_packing_list

packing_path = generate_packing_list(
    pi_items=test_items,
    invoice_no="XSL2026-001",
    invoice_date="2026-05-01",
    buyer_name="ABC Motors Uganda",
    buyer_address="Kampala, Uganda",
    output_path="C:/Users/marky/Desktop/production tool/product_tool/output/packing_list_test.xlsx",
)
print(f"  Created: {packing_path}")

# Test 2: Commercial Invoice
print("\n[Test 2] Generate Commercial Invoice...")
from src.packing.generator import generate_commercial_invoice

invoice_path = generate_commercial_invoice(
    pi_items=test_items,
    invoice_no="XSL2026-001",
    invoice_date="2026-05-01",
    buyer_name="ABC Motors Uganda",
    buyer_address="Kampala, Uganda",
    destination_country="Uganda",
    output_path="C:/Users/marky/Desktop/production tool/product_tool/output/commercial_invoice_test.xlsx",
)
print(f"  Created: {invoice_path}")

# Test 3: Both together
print("\n[Test 3] Generate Both...")
from src.packing.generator import create_packing_and_invoice

result = create_packing_and_invoice(
    pi_items=test_items,
    invoice_no="XSL2026-002",
    invoice_date="2026-05-01",
    buyer_name="XYZ Trading Co.",
    buyer_address="Nairobi, Kenya",
    output_dir="C:/Users/marky/Desktop/production tool/product_tool/output",
)
print(f"  Packing: {result['packing_list']}")
print(f"  Invoice: {result['commercial_invoice']}")

print("\n" + "=" * 50)
print("Phase 4 TEST COMPLETE!")
print("=" * 50)