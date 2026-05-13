# -*- coding: utf-8 -*-
"""
Trade Terms Calculator

Calculate prices with different trade terms (FOB, CIF, EXW, DDP, etc.)
"""
from typing import Dict, Optional, List
from dataclasses import dataclass

from .rates import convert, get_rate


# Trade term definitions
TRADE_TERMS = {
    "EXW": {
        "name": "Ex Works",
        "description": "Ex Works - Buyer arranges all transportation",
        "included": ["factory_price"],
    },
    "FOB": {
        "name": "Free On Board",
        "description": "FOB Port of Shipment - Seller delivers onboard, buyer arranges freight",
        "included": ["factory_price", "export_clearance"],
    },
    "CFR": {
        "name": "Cost and Freight",
        "description": "CFR Destination Port - Seller pays freight to destination port",
        "included": ["factory_price", "ocean_freight", "export_clearance"],
    },
    "CIF": {
        "name": "Cost Insurance Freight",
        "description": "CIF Destination Port - Includes marine insurance",
        "included": ["factory_price", "ocean_freight", "export_clearance", "insurance", "destination_port_charges"],
    },
    "DAP": {
        "name": "Delivered At Place",
        "description": "DAP Buyer's Warehouse - Seller delivers to buyer's warehouse",
        "included": ["factory_price", "freight", "insurance", "duty", "delivery"],
    },
    "DDP": {
        "name": "Delivered Duty Paid",
        "description": "DDP - All inclusive, duty paid",
        "included": ["factory_price", "freight", "insurance", "duty", "delivery", "tax"],
    },
}


@dataclass
class CostItem:
    """Cost item for calculation"""
    name: str
    amount: float
    currency: str = "CNY"
    description: str = ""


@dataclass
class PriceCalculation:
    """Price calculation result"""
    base_price: float
    currency: str
    terms: str
    
    items: List[CostItem]
    total: float
    quantity: int = 1
    
    freight_cost: float = 0
    insurance_cost: float = 0
    duty_cost: float = 0
    other_cost: float = 0
    
    @property
    def fob_price(self) -> float:
        """FOB price only"""
        return self.base_price + self.freight_cost
    
    @property
    def cif_price(self) -> float:
        """CIF price"""
        return self.fob_price + self.insurance_cost
    
    @property
    def dap_price(self) -> float:
        """DAP price"""
        return self.cif_price + self.duty_cost
    
    @property
    def ddp_price(self) -> float:
        """DDP price"""
        return self.cif_price + self.duty_cost + self.other_cost


def get_term_info(term: str) -> Dict:
    """Get trade term info
    
    Args:
        term: Trade term (EXW/FOB/CFR/CIF/DAP/DDP)
        
    Returns:
        dict with name and description
    """
    return TRADE_TERMS.get(term.upper(), {})


def calculate_price(
    base_price: float,
    quantity: int,
    term: str = "FOB",
    currency: str = "CNY",
    destination_country: str = "",
    weight_kg: float = 0,
    volume_cbm: float = 0,
    freight_per_cbm: float = 120,
    insurance_rate: float = 0.001,
    duty_rate: float = 0.10,
    delivery_cost: float = 500,
) -> PriceCalculation:
    """Calculate price with trade terms
    
    Args:
        base_price: Unit price in CNY
        quantity: Order quantity
        term: Trade term (EXW/FOB/CFR/CIF/DAP/DDP)
        currency: Target currency
        destination_country:Destination country (for duty estimation)
        weight_kg: Total weight in kg
        volume_cbm: Total volume in CBM
        freight_per_cbm: Freight per CBM (CNY)
        insurance_rate: Insurance rate (default 0.1%)
        duty_rate: Duty rate (default 10%)
        delivery_cost: Domestic delivery cost (CNY)
        
    Returns:
        PriceCalculation object
    """
    term = term.upper()
    
    # Currency conversion to CNY first
    if currency.upper() != "CNY":
        base_price_cny = convert(base_price, currency, "CNY")
    else:
        base_price_cny = base_price
    
    # Calculate items
    items = []
    
    # 1. Factory/Ex Works price
    factory_total = base_price_cny * quantity
    items.append(CostItem(
        name="Ex Works Price",
        amount=factory_total,
        currency="CNY",
        description=f"{base_price_cny:.2f} × {quantity}"
    ))
    
    # Calculate components
    freight_cost = 0
    insurance_cost = 0
    duty_cost = 0
    other_cost = 0
    
    if term in ["FOB", "CFR", "CIF", "DAP", "DDP"]:
        # Ocean freight (per CBM or per weight whichever is higher)
        if weight_kg > 0 and volume_cbm > 0:
            freight_cbm = max(volume_cbm, weight_kg / 500)  # 1 CBM = 500kg
        elif volume_cbm > 0:
            freight_cbm = volume_cbm
        else:
            # Estimate: assume 0.5 CBM per unit for motorcycles
            freight_cbm = 0.5 * quantity
        
        freight_cost = freight_cbm * freight_per_cbm
        
        items.append(CostItem(
            name="Ocean Freight",
            amount=freight_cost,
            currency="CNY",
            description=f"{freight_cbm:.2f} CBM × {freight_per_cbm}"
        ))
    
    # Export clearance (fixed small fee)
    export_clearance = 200 if term in ["FOB", "CFR", "CIF", "DAP", "DDP"] else 0
    if export_clearance:
        other_cost += export_clearance
        items.append(CostItem(
            name="Export Clearance",
            amount=export_clearance,
            currency="CNY"
        ))
    
    if term in ["CIF", "DAP", "DDP"]:
        # Marine insurance (0.1% of CIF value)
        cif_value = factory_total + freight_cost
        insurance_cost = cif_value * insurance_rate
        items.append(CostItem(
            name="Marine Insurance",
            amount=insurance_cost,
            currency="CNY",
            description=f"{insurance_rate*100:.2f}%"
        ))
    
    if term in ["DAP", "DDP"]:
        # Import duty estimation
        duty_cost = factory_total * duty_rate
        items.append(CostItem(
            name="Import Duty (est.)",
            amount=duty_cost,
            currency="CNY",
            description=f"{duty_rate*100:.0f}%"
        ))
    
    if term == "DDP":
        # Delivery to warehouse
        other_cost += delivery_cost
        items.append(CostItem(
            name="Delivery Cost",
            amount=delivery_cost,
            currency="CNY"
        ))
    
    # Total in CNY
    total_cny = factory_total + freight_cost + insurance_cost + duty_cost + other_cost
    
    # Convert to target currency
    if currency.upper() != "CNY":
        final_total = convert(total_cny, "CNY", currency)
    else:
        final_total = total_cny
    
    return PriceCalculation(
        base_price=base_price * quantity,
        quantity=quantity,
        currency=currency,
        terms=term,
        items=items,
        total=final_total,
        freight_cost=freight_cost,
        insurance_cost=insurance_cost,
        duty_cost=duty_cost,
        other_cost=other_cost,
    )


def format_calculation(calc: PriceCalculation) -> str:
    """Format calculation for display
    
    Args:
        calc: PriceCalculation
        
    Returns:
        Formatted string
    """
    from .rates import format_price as format_rates
    
    lines = [f"Price Calculation ({calc.terms})", "=" * 40]
    
    for item in calc.items:
        formatted = format_rates(item.amount, item.currency)
        desc = f" - {item.description}" if item.description else ""
        lines.append(f"  {item.name}: {formatted}{desc}")
    
    lines.append("-" * 40)
    formatted_total = format_rates(calc.total, calc.currency)
    lines.append(f"  TOTAL: {formatted_total}")
    lines.append(f"  Per Unit: {format_rates(calc.total / calc.quantity if calc.quantity else 0, calc.currency)}")
    
    return "\n".join(lines)


def get_common_terms() -> List[str]:
    """Get list of common trade terms"""
    return list(TRADE_TERMS.keys())


if __name__ == "__main__":
    # Test calculation
    calc = calculate_price(
        base_price=5000,
        quantity=10,
        term="CIF",
        destination_country="UGA",
        volume_cbm=2.5,
    )
    
    print(format_calculation(calc))
    
    print(f"\nFOB: {calc.fob_price}")
    print(f"CIF: {calc.cif_price}")