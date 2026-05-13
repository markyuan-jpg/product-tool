# -*- coding: utf-8 -*-
"""
Company Configuration Module

Manage company information template for quotations.
Default: ~/.product_tool/company.json
Override: COMPANY_CONFIG_PATH environment variable
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Default directory and file
DEFAULT_DIR = Path.home() / ".product_tool"
DEFAULT_CONFIG_FILE = "company.json"
DEFAULT_CONFIG_PATH = DEFAULT_DIR / DEFAULT_CONFIG_FILE

# Environment variable override
CONFIG_PATH = os.environ.get("COMPANY_CONFIG_PATH", str(DEFAULT_CONFIG_PATH))


def get_company_path() -> str:
    """Get company config path"""
    return CONFIG_PATH


def set_company_path(path: str) -> None:
    """Set custom config path (runtime only)"""
    global CONFIG_PATH
    CONFIG_PATH = path


def ensure_dir(path: str) -> None:
    """Ensure directory exists"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)


def get_default_config() -> Dict[str, Any]:
    """Get default company configuration template"""
    return {
        "name": "",
        "name_en": "",
        "address": "",
        "address_en": "",
        "city": "",
        "tel": "",
        "email": "",
        "website": "",
        "logo_path": "",
        "contact_person": "",
        "bank": {
            "beneficiary": "",
            "bank_name": "",
            "bank_address": "",
            "account_no": "",
            "swift_code": "",
        },
    }


def load_company(config_path: str = None) -> Dict[str, Any]:
    """Load company configuration
    
    Args:
        config_path: Custom config path (None = default)
        
    Returns:
        Company config dict
        
    If file doesn't exist, returns default config.
    """
    path = config_path or CONFIG_PATH
    
    if not os.path.exists(path):
        return get_default_config()
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_company(config: Dict[str, Any], config_path: str = None) -> str:
    """Save company configuration
    
    Args:
        config: Company config dict
        config_path: Custom config path (None = default)
        
    Returns:
        config_path
    """
    path = config_path or CONFIG_PATH
    ensure_dir(path)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    return path


def init_company_config(overwrite: bool = False) -> Dict[str, Any]:
    """Initialize company config file
    
    Args:
        overwrite: If True, overwrite existing
        
    Returns:
        Company config dict
    """
    ensure_dir(CONFIG_PATH)
    if not overwrite and os.path.exists(CONFIG_PATH):
        return load_company()
    
    config = get_default_config()
    save_company(config)
    return config


def get_company_name(config: Dict[str, Any] = None) -> str:
    """Get company name from config"""
    cfg = config or load_company()
    return cfg.get("name", "")


def get_company_name_en(config: Dict[str, Any] = None) -> str:
    """Get company English name from config"""
    cfg = config or load_company()
    return cfg.get("name_en", "")


def get_bank_info(config: Dict[str, Any] = None) -> Dict[str, str]:
    """Get bank info from config"""
    cfg = config or load_company()
    return cfg.get("bank", {})


def format_company_header(config: Dict[str, Any] = None) -> str:
    """Format company header for quotations
    
    Args:
        config: Company config (None = load)
        
    Returns:
        Formatted multi-line string
    """
    cfg = config or load_company()
    
    name = cfg.get("name_en", "") or cfg.get("name", "")
    addr = cfg.get("address_en", "") or cfg.get("address", "")
    
    lines = [name] if name else []
    if addr:
        lines.append(addr)
    
    tel = cfg.get("tel", "")
    email = cfg.get("email", "")
    contact = ""
    if tel or email:
        parts = []
        if tel: parts.append(f"Tel: {tel}")
        if email: parts.append(f"Email: {email}")
        contact = " | ".join(parts)
    if contact:
        lines.append(contact)
    
    website = cfg.get("website", "")
    if website:
        lines.append(website)
    
    return "\n".join(line for line in lines if line)


def format_bank_info(config: Dict[str, Any] = None) -> str:
    """Format bank info for PI/invoices
    
    Args:
        config: Company config (None = load)
        
    Returns:
        Formatted multi-line string
    """
    cfg = config or load_company()
    bank = cfg.get("bank", {})
    
    if not bank.get("beneficiary"):
        return ""
    
    lines = [
        f"Beneficiary: {bank.get('beneficiary', '')}",
        f"Bank Name: {bank.get('bank_name', '')}",
        f"Bank Address: {bank.get('bank_address', '')}",
        f"Account No.: {bank.get('account_no', '')}",
        f"Swift Code: {bank.get('swift_code', '')}",
    ]
    
    return "\n".join(line for line in lines if line)


if __name__ == "__main__":
    # Test: initialize config
    print(f"Config path: {get_company_path()}")
    
    # Initialize
    config = init_company_config(overwrite=True)
    print(f"Initialized: {config['name']}")
    
    # Update
    config["name"] = "SONLINK E-MOTORCYCLE CO., LTD"
    config["address"] = "NO.576 Fengyi Road, Fengxian, Jiangsu, China"
    config["tel"] = "+86-13926156666"
    config["email"] = "gwlong926@163.com"
    save_company(config)
    print("Saved config")
    
    # Load back
    loaded = load_company()
    print(f"Loaded: {loaded['name']}")