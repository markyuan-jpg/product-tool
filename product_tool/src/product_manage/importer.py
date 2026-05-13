# -*- coding: utf-8 -*-

# -*- coding: utf-8 -*-

"""

Product importer

"""

import pandas as pd

from typing import Dict, List, Any

from datetime import datetime



from .db import init_db

from .models import Product

from .repository import save_product, get_product_by_sku, get_products_by_skus

from ..rates import convert as convert_currency



try:

    from ..utils.translator import translate_text

except ImportError:

    from utils.translator import translate_text





def import_from_df(

    df: pd.DataFrame,

    category: str = "",

    update_existing: bool = False,

    user_id: str = "local"

) -> Dict[str, int]:

    """Import products from DataFrame"""

    

    """

        df: DataFrame from param_price_parser or similar

        category: Category to assign

        update_existing: Update if SKU exists

        user_id: User ID

        

    Returns:

        dict with imported, skipped, errors counts

    """

    init_db()

    

    result = {

        "imported": 0,

        "skipped": 0,

        "errors": 0

    }

    

    # Batch pre-fetch all products for these SKUs (one query, not N)

    unique_models = list(set(

        str(row.get("model", "")).strip()

        for _, row in df.iterrows()

        if row.get("model") and not pd.isna(row.get("model"))

    ))

    products_by_sku = get_products_by_skus(unique_models, user_id) if unique_models else {}

    

    for _, row in df.iterrows():

        try:

            # Skip if no model

            model = row.get("model", "")

            if not model or pd.isna(model):

                result["skipped"] += 1

                continue

            

            # SKU: 

            final_sku = str(model).strip()

            existing = products_by_sku.get(final_sku) or get_product_by_sku(final_sku, user_id)

            suffix = 0

            while existing:

                if update_existing:

                    break

                suffix += 1

                if suffix <= 26:

                    final_sku = f"{model}-{chr(64 + suffix)}"

                else:

                    final_sku = f"{model}-{chr(64 + (suffix - 1) // 26)}{chr(64 + (suffix - 1) % 26 + 1)}"

                existing = products_by_sku.get(final_sku) or get_product_by_sku(final_sku, user_id)

            

            # Create product

            row_copy = row.to_dict() if hasattr(row, 'to_dict') else dict(row)

            row_copy['model'] = final_sku

            product = _row_to_product(row_copy, category, user_id)

            

            # Save

            save_product(product, update_if_exists=update_existing)

            result["imported"] += 1

        

        except Exception as e:

            result["errors"] += 1

    

    return result





def import_from_list(

    data: List[Dict[str, Any]],

    category: str = "",

    update_existing: bool = True,

    user_id: str = "local"

) -> Dict[str, int]:

    """

    

    Args:

        data: List of product dicts

        category: Category to assign

        update_existing: Update if SKU exists

        user_id: User ID

        

    Returns:

        dict with imported, skipped, errors counts

    """

    df = pd.DataFrame(data)

    return import_from_df(df, category, update_existing, user_id)





def _row_to_product(

    row: pd.Series,

    category: str,

    user_id: str

) -> Product:

    """
    
    

    Args:

        row: DataFrame row

        category: Category

        user_id: User ID

        

    Returns:

        Product instance

    """

    # Extract model (SKU)

    sku = str(row.get("model", "")).strip()

    if not sku:

        raise ValueError("Empty model")

    

    # Name

    name_zh = str(row.get("name_zh", row.get("spec_zh", sku)))

    if pd.isna(name_zh):

        name_zh = sku

    name_en = str(row.get("name_en", ""))

    if pd.isna(name_en):

        name_en = ""

    # Auto-translate name_en if empty

    if not name_en and name_zh:

        name_en = translate_text(name_zh)

    

    # Price

    price_rmb = 0.0

    pr = row.get("price_rmb")

    if pr and not pd.isna(pr):

        try:

            price_rmb = float(pr)

        except (ValueError, TypeError):

            pass

    

    # MOQ

    moq = 1

    m = row.get("moq")

    if m and not pd.isna(m):

        try:

            moq = int(m)

        except (ValueError, TypeError):

            pass

    

    # Specs - convert spec_zh to dict

    specs = {}

    spec_zh = row.get("spec_zh", "")

    if spec_zh and not pd.isna(spec_zh):

        for part in str(spec_zh).split(";"):

            part = part.strip()

            if ": " in part:

                key, value = part.split(": ", 1)

                specs[key.strip()] = value.strip()

            elif ":" in part:

                key, value = part.split(":", 1)

                specs[key.strip()] = value.strip()

    

    # Image path - support both _image_path and image_path

    image_path = ""

    for key in ['_image_path', 'image_path']:

        img = row.get(key)

        if img and not pd.isna(img):

            image_path = str(img)

            break

    

    # Source file - support both _source_file and _source

    source_file = ""

    for key in ['_source_file', '_source']:

        src = row.get(key)

        if src and not pd.isna(src):

            source_file = str(src)

            break

    

    # Prices dict from parsed data

    prices = {}

    for key in ['prices', '_prices']:

        p = row.get(key)

        if p and not pd.isna(p):

            if isinstance(p, dict):

                prices = p

            break

    

    # 

    carton_size = str(row.get('carton_size', '')) if not pd.isna(row.get('carton_size', '')) else ''

    gross_weight = 0.0

    try: gross_weight = float(row.get('gross_weight', 0) or 0)

    except Exception: pass

    net_weight = 0.0

    try: net_weight = float(row.get('net_weight', 0) or 0)

    except Exception: pass

    cbm = 0.0

    try: cbm = float(row.get('cbm', 0) or 0)

    except Exception: pass

    units_per_carton = 0

    try: units_per_carton = int(row.get('units_per_carton', 0) or 0)

    except Exception: pass

    packing_type = str(row.get('packing_type', '')) if not pd.isna(row.get('packing_type', '')) else ''

    

    now = datetime.now().isoformat()

    

    return Product(

        sku=sku,

        name_zh=name_zh,

        name_en=name_en,

        category=category,

        price_rmb=price_rmb,

        price_usd=round(convert_currency(price_rmb, 'CNY', 'USD'), 2) if price_rmb else 0,

        moq=moq,

        specs=specs,

        spec_zh=str(spec_zh) if spec_zh and not pd.isna(spec_zh) else "",

        prices=prices,

        image_path=image_path,

        source_file=source_file,

        carton_size=carton_size,

        gross_weight=gross_weight,

        net_weight=net_weight,

        cbm=cbm,

        units_per_carton=units_per_carton,

        packing_type=packing_type,

        user_id=user_id,

        created_at=now,

        updated_at=now,

    )





if __name__ == "__main__":

    # Test import

    test_data = [

        {"model": "BOX", "price_rmb": 4900, "spec_zh": ": mid-flat wire; : 3000W"},

        {"model": "M6", "price_rmb": 5500, "spec_zh": ": mid-flat wire; : 4000W"},

    ]

    

    result = import_from_list(test_data, category="")

    print(f"Result: {result}")

