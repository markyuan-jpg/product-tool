"""
Price Configuration Module V2

Loads price_config.json, provides classification utilities
for multi-price extraction. Supports:

- Industry detection (--industry / env / filename inference)
- Regex keyword matching
- Price value validation per currency
- Priority resolution (first/last/largest/most_common)
- Config merge: user config overrides defaults
"""
import os
import json
import re
import logging
from typing import Dict, List, Tuple, Optional, Any

logger = logging.getLogger(__name__)

_PRICE_CONFIG: Optional[Dict[str, Any]] = None
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_CONFIG_PATH = os.path.join(_BASE_DIR, 'config', 'price_config.json')

# ─── Sector / Regular ───


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts. override values take precedence."""
    result = base.copy()
    for key, val in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(val, dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


def load_price_config(path: str = None) -> Dict[str, Any]:
    """Load price config. Chain: PRICE_CONFIG_PATH env > explicit path > default."""
    global _PRICE_CONFIG
    if _PRICE_CONFIG:
        return _PRICE_CONFIG

    # Use default bundled config first
    default_path = _DEFAULT_CONFIG_PATH
    if os.path.exists(default_path):
        with open(default_path, encoding='utf-8') as f:
            default = json.load(f)
    else:
        default = {"default_industry": "general", "industries": {"general": {}}}

    # Override with user-specified config
    if path is None:
        path = os.environ.get('PRICE_CONFIG_PATH', '')
    if path and os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                user_config = json.load(f)
            _PRICE_CONFIG = _deep_merge(default, user_config)
            logger.info(f"Price config loaded: {path} (merged with defaults)")
            return _PRICE_CONFIG
        except Exception as e:
            logger.warning(f"Failed to load price config {path}: {e}")

    _PRICE_CONFIG = default
    return _PRICE_CONFIG


def reload_price_config(path: str = None) -> Dict[str, Any]:
    """Clear cache and reload."""
    global _PRICE_CONFIG
    _PRICE_CONFIG = None
    return load_price_config(path)


def detect_industry(file_path: str = None, user_specified: str = None) -> str:
    """Detect industry: --industry param > PRICE_INDUSTRY env > filename match > default.
    
    The `user_specified` param corresponds to the CLI --industry argument.
    """
    # Priority 1: explicit user param
    if user_specified:
        return user_specified

    # Priority 2: environment variable
    env_industry = os.environ.get('PRICE_INDUSTRY', '').strip()
    if env_industry:
        return env_industry

    # Priority 3: filename pattern match
    if file_path:
        config = load_price_config()
        rules = config.get('industry_detection', {}).get('rules', [])
        fname_lower = os.path.basename(file_path).lower()
        for rule in rules:
            pattern = rule.get('pattern', '')
            try:
                if re.search(pattern, fname_lower, re.I):
                    return rule['industry']
            except re.error:
                continue

    # Priority 4: default
    return load_price_config().get('default_industry', 'general')


def get_industry_config(industry: str = None, file_path: str = None) -> Dict[str, Any]:
    """Get industry config with industry auto-detection."""
    if industry is None:
        industry = detect_industry(file_path)
    config = load_price_config()
    industries = config.get('industries', {})
    return industries.get(industry, industries.get('general', {}))


# ─── Keyword matching ───


def match_keyword(text: str, keywords: List[str], use_regex: bool = False) -> bool:
    """Match text against keyword list. Supports substring or regex match."""
    if not text or not keywords:
        return False
    text_lower = text.lower().strip()
    for kw in keywords:
        if use_regex:
            try:
                if re.search(kw, text_lower, re.I):
                    return True
            except re.error:
                if kw.lower() in text_lower:
                    return True
        else:
            if kw.lower() in text_lower:
                return True
    return False


# ─── Price classification ───


def classify_price(item_name: str, industry_config: Dict[str, Any]) -> Tuple[str, str, bool]:
    """Classify a price item name into a price type.

    Returns:
        (type, label, is_primary) where:
        - type: 'primary' or secondary key (e.g. 'battery', 'charger')
        - label: Display label (e.g. 'Battery Price')
        - is_primary: True if this is the main product price
    """
    name_lower = item_name.lower().strip()
    if not name_lower:
        return ('unclassified', item_name, False)

    use_regex = industry_config.get('use_regex', False)

    for kw in industry_config.get('primary_keywords', []):
        if match_keyword(name_lower, [kw], use_regex):
            return ('primary', item_name, True)

    for entry in industry_config.get('secondary_keywords', []):
        for kw in entry.get('keywords', []):
            if match_keyword(name_lower, [kw], use_regex):
                return (entry['type'], entry['label'], False)

    return ('unclassified', item_name, False)


def get_secondary_labels(industry_config: Dict[str, Any]) -> Dict[str, str]:
    """Build {type: label} mapping from industry config."""
    return {
        entry['type']: entry['label']
        for entry in industry_config.get('secondary_keywords', [])
    }


# ─── Price validation ───


def validate_price(value: float, currency: str = 'CNY', industry_config: Dict = None) -> bool:
    """Check if price is within allowed range for the currency."""
    if value is None or value <= 0:
        return False
    pd_config = (industry_config or {}).get('price_detection', {})
    ranges = pd_config.get('value_range', {})
    default_range = ranges.get('cny', [0.01, 999999])
    lo, hi = ranges.get(currency.upper(), default_range) if currency else default_range
    return lo <= value <= hi


# ─── Price priority resolution ───


def resolve_priority(prices: List[float], strategy: str = 'largest') -> Optional[float]:
    """Resolve which price to use as primary from a list of candidate prices."""
    if not prices:
        return None
    if strategy == 'first':
        return prices[0]
    if strategy == 'last':
        return prices[-1]
    if strategy == 'largest':
        return max(prices)
    if strategy == 'smallest':
        return min(prices)
    if strategy == 'most_common':
        from collections import Counter
        counter = Counter(prices)
        return counter.most_common(1)[0][0]
    # Default: largest
    return max(prices)
