# -*- coding: utf-8 -*-
"""
Product Manage Module

Product library management: save, search, import, export.
"""
from .db import get_db_path, set_db_path, get_connection, close_connection, init_db
from .models import Product, create_product_from_parse_result
from .repository import (
    save_product,
    get_product_by_id,
    get_product_by_sku,
    list_products,
    search_products,
    delete_product,
    get_categories,
    get_product_count,
    update_price,
    update_product,
)
from .importer import import_from_df, import_from_list
from .exporter import export_to_excel, export_to_csv

__all__ = [
    # DB
    "get_db_path",
    "set_db_path",
    "get_connection",
    "close_connection",
    "init_db",
    # Models
    "Product",
    "create_product_from_parse_result",
    # Repository
    "save_product",
    "get_product_by_id",
    "get_product_by_sku",
    "list_products",
    "search_products",
    "delete_product",
    "get_categories",
    "get_product_count",
    "update_price",
    "update_product",
    # Importer
    "import_from_df",
    "import_from_list",
    # Exporter
    "export_to_excel",
    "export_to_csv",
]