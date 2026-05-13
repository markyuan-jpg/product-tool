#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Price calculation engine for export quotations.

Provides FOB and CIF price calculations based on factory prices.
"""
from typing import Optional
import pandas as pd


DEFAULT_EXCHANGE_RATE = 7.2  # Default RMB to USD exchange rate


def calculate_fob(
    price_rmb: float,
    domestic_fee: float = 0,
    exchange_rate: float = DEFAULT_EXCHANGE_RATE
) -> float:
    """
    Calculate FOB (Free On Board) price in USD.
    
    FOB = (Factory Price + Domestic Fees) / Exchange Rate
    
    Args:
        price_rmb: Factory price in RMB
        domestic_fee: Domestic fees ( inland freight, customs clearance, documentation, etc.) in RMB
        exchange_rate: Exchange rate (RMB per USD). Default 7.2
    
    Returns:
        FOB price in USD
    """
    if pd.isna(price_rmb) or price_rmb is None:
        return 0.0
    
    try:
        total_rmb = float(price_rmb) + float(domestic_fee or 0)
        return round(total_rmb / exchange_rate, 2)
    except (TypeError, ValueError):
        return 0.0


def calculate_cif(
    fob_price: float,
    ocean_freight: float = 0,
    insurance_rate: float = 0.003
) -> float:
    """
    Calculate CIF (Cost, Insurance, Freight) price in USD.
    
    CIF = FOB + Ocean Freight + Insurance
    Insurance = FOB * Insurance Rate (default 0.3%)
    
    Args:
        fob_price: FOB price in USD
        ocean_freight: Ocean freight cost in USD
        insurance_rate: Insurance rate (default 0.003 = 0.3%)
    
    Returns:
        CIF price in USD
    """
    if pd.isna(fob_price) or fob_price is None:
        return 0.0
    
    try:
        fob = float(fob_price)
        freight = float(ocean_freight or 0)
        insurance = fob * float(insurance_rate or 0)
        return round(fob + freight + insurance, 2)
    except (TypeError, ValueError):
        return 0.0


def add_price_columns(
    df: pd.DataFrame,
    price_type: str = "factory",
    domestic_fee: float = 0,
    ocean_freight: float = 0,
    insurance_rate: float = 0.003,
    exchange_rate: float = DEFAULT_EXCHANGE_RATE
) -> pd.DataFrame:
    """
    Add price columns based on price type.
    
    Args:
        df: DataFrame with product data (must have price_rmb or price_usd)
        price_type: Type of price calculation:
            - "factory": Keep original price_usd as 工厂价 (default)
            - "fob": Calculate FOB price
            - "cif": Calculate CIF price
        domestic_fee: Domestic fees in RMB (for FOB calculation)
        ocean_freight: Ocean freight in USD (for CIF calculation)
        insurance_rate: Insurance rate (for CIF calculation)
        exchange_rate: Exchange rate (RMB per USD)
    
    Returns:
        DataFrame with additional price columns:
        - price_factory: Original factory price in USD
        - price_fob: FOB price in USD (if price_type in ["fob", "cif"])
        - price_cif: CIF price in USD (if price_type == "cif")
    """
    if df is None or df.empty:
        return df
    
    result = df.copy()
    
    # Ensure we have factory price in USD
    if "price_usd" not in result.columns:
        if "price_rmb" in result.columns:
            result["price_usd"] = pd.to_numeric(result["price_rmb"], errors="coerce") / exchange_rate
        else:
            result["price_usd"] = None
    
    # Rename original price_usd as factory price
    result["price_factory"] = result["price_usd"]
    
    # Calculate based on price_type
    if price_type.lower() in ["fob", "cif"]:
        # Need price_rmb for FOB calculation
        price_rmb = result["price_rmb"] if "price_rmb" in result.columns else None
        
        if price_rmb is not None:
            result["price_fob"] = result.apply(
                lambda row: calculate_fob(
                    row["price_rmb"] if "price_rmb" in row else None,
                    domestic_fee,
                    exchange_rate
                ),
                axis=1
            )
        else:
            # Use existing price_usd if no RMB available
            result["price_fob"] = result["price_usd"]
    
    if price_type.lower() == "cif":
        if "price_fob" not in result.columns:
            # Calculate FOB first if not already done
            price_rmb = result["price_rmb"] if "price_rmb" in result.columns else None
            if price_rmb is not None:
                result["price_fob"] = result.apply(
                    lambda row: calculate_fob(
                        row["price_rmb"] if "price_rmb" in row else None,
                        domestic_fee,
                        exchange_rate
                    ),
                    axis=1
                )
        
        # Calculate CIF
        if "price_fob" in result.columns:
            result["price_cif"] = result.apply(
                lambda row: calculate_cif(
                    row["price_fob"] if "price_fob" in row else None,
                    ocean_freight,
                    insurance_rate
                ),
                axis=1
            )
    
    return result


def get_price_columns(price_type: str = "factory") -> list:
    """
    Get list of column names for a given price type.
    
    Args:
        price_type: "factory", "fob", or "cif"
    
    Returns:
        List of column names
    """
    base_cols = ["model", "name_zh", "name_en", "spec_zh", "spec_en", "color", "package"]
    
    if price_type.lower() == "factory":
        return base_cols + ["price_rmb", "price_usd"]
    elif price_type.lower() == "fob":
        return base_cols + ["price_rmb", "price_factory", "price_fob"]
    elif price_type.lower() == "cif":
        return base_cols + ["price_rmb", "price_factory", "price_fob", "price_cif"]
    
    return base_cols + ["price_rmb", "price_usd"]