# -*- coding: utf-8 -*-
"""
Exchange Rate Module
"""
import os, json, time, requests
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta

DEFAULT_RATES = {"USD":1.0,"CNY":7.2,"EUR":0.92,"GBP":0.79,"JPY":149.5,"KRW":1320.0,"INR":83.0,"BRL":4.97,"RUB":92.0,"VND":24500.0,"THB":35.5,"MYR":4.7,"SGD":1.34,"PHP":55.5,"IDR":15600.0}

CACHE_DIR = Path.home() / ".product_tool"
CACHE_FILE = CACHE_DIR / "rates_cache.json"
CACHE_TTL_HOURS = 24

def ensure_dir():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_path():
    return str(CACHE_FILE)

def load_cache() -> Optional[Dict[str, float]]:
    if not CACHE_FILE.exists():
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01"))
        cached_rates = data.get("rates", {})
        age = datetime.now() - cached_at
        if age.total_seconds() > CACHE_TTL_HOURS * 3600:
            return None
        return cached_rates
    except Exception:
        return None

def save_cache(rates: Dict[str, float]):
    ensure_dir()
    data = {"cached_at": datetime.now().isoformat(), "rates": rates}
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_rates(base: str = "USD") -> Dict[str, float]:
    cached = load_cache()
    if cached:
        return cached
    url = f"https://api.exchangerate.host/latest?base={base}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("success") and data.get("rates"):
            rates = data["rates"]
            save_cache(rates)
            return rates
    except Exception:
        pass
    return DEFAULT_RATES.copy()

def get_rate(from_currency: str, to_currency: str = "CNY") -> float:
    rates = fetch_rates()
    from_rate = rates.get(from_currency.upper(), 1.0)
    to_rate = rates.get(to_currency.upper(), 1.0)
    if from_currency.upper() == "USD":
        return to_rate
    return to_rate / from_rate

def convert(amount: float, from_currency: str, to_currency: str = "CNY") -> float:
    rate = get_rate(from_currency, to_currency)
    return round(amount * rate, 2)

def format_price(amount: float, currency: str = "CNY", show_currency: bool = True) -> str:
    symbols = {"CNY":"¥","USD":"$","EUR":"€","GBP":"£","JPY":"¥"}
    symbol = symbols.get(currency.upper(), currency.upper()) if show_currency else ""
    if currency.upper() == "JPY":
        return f"{symbol}{amount:,.0f}"
    else:
        return f"{symbol}{amount:,.2f}"

def get_all_rates(base: str = "USD") -> Dict[str, float]:
    rates = fetch_rates(base)
    if base.upper() != "USD":
        base_rate = rates.get("USD", 1.0)
        return {curr: rate / base_rate for curr, rate in rates.items()}
    return rates

def get_available_currencies() -> list:
    return list(DEFAULT_RATES.keys())

def force_refresh() -> Dict[str, float]:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    return fetch_rates()

if __name__ == "__main__":
    print("Currencies:", get_available_currencies())
    rates = fetch_rates()
    print("Rates:", rates)
    print(f"100 USD = {convert(100, 'USD', 'CNY')} CNY")
    print(f"Format: {format_price(1234.56, 'USD')}")