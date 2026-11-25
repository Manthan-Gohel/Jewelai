import csv
import io
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
import logging

from app.models.models import Product, ProductImage, InstagramAccount

logger = logging.getLogger(__name__)

STANDARD_FIELD_ALIASES = {
    "sku": ["sku", "code", "item code", "item_code", "design code", "barcode", "product code", "item no", "id"],
    "name": ["name", "item name", "item_name", "product name", "product_name", "title", "design name"],
    "category": ["category", "item group", "item_group", "type", "product type", "jewellery type", "classification"],
    "price": ["price", "mrp", "rate", "selling price", "retail price", "amount", "unit price"],
    "gold_purity": ["purity", "gold purity", "gold_purity", "karat", "kt", "carat", "touch", "metal purity"],
    "gross_weight": ["weight", "gross weight", "gross_weight", "gwt", "gross wt", "wt", "net weight", "weight (g)"],
    "stock": ["stock", "qty", "quantity", "inventory", "pieces", "available qty", "balance"],
    "description": ["description", "details", "remarks", "notes", "summary", "about"],
    "image_url": ["image", "image url", "image_url", "photo", "photo url", "picture", "img", "image link"]
}

INITIAL_SEED_PRODUCTS = [
    {
        "sku": "JW-ER-001",
        "name": "22K Traditional Gold Studs",
        "category": "Earrings",
        "description": "Handcrafted lightweight floral gold studs in hallmarked 22 Karat gold with fine granulation detailing.",
        "price": 8500.0,
        "gold_purity": "22K",
        "gross_weight": 2.2,
        "net_weight": 2.2,
        "diamond_specs": None,
        "stock": 8,
        "tags": ["gold", "studs", "dailywear", "22k"],
        "image_url": "https://images.unsplash.com/photo-1630019852942-f89202989a59?auto=format&fit=crop&w=600&q=80"
    },
    {
        "sku": "JW-ER-002",
        "name": "22K Classic Gold Hoops (Baali)",
        "category": "Earrings",
        "description": "Timeless 22 Karat yellow gold hoop earrings featuring polished finish and secure hinge closure. BIS Hallmarked.",
        "price": 11200.0,
        "gold_purity": "22K",
        "gross_weight": 2.9,
        "net_weight": 2.9,
        "diamond_specs": None,
        "stock": 6,
        "tags": ["hoops", "baali", "classic", "22k"],
        "image_url": "https://images.unsplash.com/photo-1535632066927-ab7c9ab60908?auto=format&fit=crop&w=600&q=80"
    },
    {
        "sku": "JW-RG-101",
        "name": "18K Solitaire Diamond Ring",
        "category": "Rings",
        "description": "Certified 0.25 Ct VVS-EF brilliant cut solitaire diamond perched on an 18 Karat rose gold band.",
        "price": 34000.0,
        "gold_purity": "18K",
        "gross_weight": 2.5,
        "net_weight": 2.45,
        "diamond_specs": {"carat": 0.25, "clarity": "VVS1", "color": "E"},
        "stock": 5,
        "tags": ["diamond", "solitaire", "engagement", "ring"],
        "image_url": "https://images.unsplash.com/photo-1605100804763-247f67b3557e?auto=format&fit=crop&w=600&q=80"
    }
]


class CatalogueService:
    def __init__(self, db: Session):
        self.db = db

    def seed_initial_products_if_empty(self, account_id: str):
        """Seed initial products for test accounts or manual developer sandbox."""
        count = self.db.query(Product).filter(Product.instagram_account_id == account_id).count()
        if count == 0:
            for item in INITIAL_SEED_PRODUCTS:
                product = Product(
                    instagram_account_id=account_id,
                    sku=item["sku"],
                    name=item["name"],
                    category=item["category"],
                    description=item["description"],
                    price=item["price"],
                    gold_purity=item["gold_purity"],
                    gross_weight=item["gross_weight"],
                    net_weight=item["net_weight"],
                    diamond_specs=item["diamond_specs"],
                    stock=item["stock"],
                    status="active",
                    tags=item["tags"]
                )
                self.db.add(product)
                self.db.flush()
                if item.get("image_url"):
                    img = ProductImage(
                        product_id=product.id,
                        image_url=item["image_url"],
                        is_primary=True,
                        alt_text=item["name"]
                    )
                    self.db.add(img)
            self.db.commit()

    def preview_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        Parse CSV content, extract headers, return top 5 sample rows,
        and auto-detect candidate column mappings based on jewellery client terminology.
        """
        # Handle possible UTF-8 BOM
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]

        f = io.StringIO(csv_content)
        reader = csv.reader(f)
        try:
            raw_headers = next(reader)
        except StopIteration:
            return {"headers": [], "sample_rows": [], "suggested_mappings": {}, "total_preview_rows": 0}

        headers = [h.strip() for h in raw_headers if h.strip()]

        sample_rows = []
        for i, row in enumerate(reader):
            if i >= 5:
                break
            if row:
                row_dict = {}
                for h_idx, h in enumerate(headers):
                    val = row[h_idx].strip() if h_idx < len(row) else ""
                    row_dict[h] = val
                sample_rows.append(row_dict)

        # Intelligent fuzzy header matching
        suggested_mappings = {}
        for std_field, aliases in STANDARD_FIELD_ALIASES.items():
            matched_header = None
            for h in headers:
                clean_h = re.sub(r'[^a-zA-Z0-9\s]', '', h.lower()).strip()
                clean_aliases = [re.sub(r'[^a-zA-Z0-9\s]', '', a.lower()).strip() for a in aliases]
                if clean_h in clean_aliases or any(alias == clean_h for alias in clean_aliases):
                    matched_header = h
                    break
                elif any(alias in clean_h for alias in clean_aliases):
                    matched_header = h
                    break
            if matched_header:
                suggested_mappings[std_field] = matched_header

        return {
            "headers": headers,
            "sample_rows": sample_rows,
            "suggested_mappings": suggested_mappings,
            "total_preview_rows": len(sample_rows)
        }

    def import_mapped_csv(
        self,
        account_id: str,
        csv_content: str,
        mapping: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Transactionally import products using client-specified column mappings
        with strict data validation (prices, purities, weights, and non-empty keys).
        """
        if csv_content.startswith('\ufeff'):
            csv_content = csv_content[1:]

        f = io.StringIO(csv_content)
        reader = csv.DictReader(f)
        
        imported_count = 0
        updated_count = 0
        errors: List[str] = []

        sku_col = mapping.get("sku")
        name_col = mapping.get("name")
        price_col = mapping.get("price")
        cat_col = mapping.get("category")
        purity_col = mapping.get("gold_purity")
        weight_col = mapping.get("gross_weight")
        stock_col = mapping.get("stock")
        desc_col = mapping.get("description")
        img_col = mapping.get("image_url")

        if not sku_col or not name_col or not price_col:
            raise ValueError("Mapping must include at least 'sku', 'name', and 'price'.")

        for idx, row in enumerate(reader, start=2):  # Start at row 2 (row 1 is header)
            sku = (row.get(sku_col) or "").strip()
            name = (row.get(name_col) or "").strip()
            price_raw = (row.get(price_col) or "").strip()

            if not sku:
                errors.append(f"Row {idx}: Missing SKU/Product Code")
                continue
            if not name:
                errors.append(f"Row {idx}: Missing Product Name")
                continue
            if not price_raw:
                errors.append(f"Row {idx}: Missing Price")
                continue

            # Clean and validate price (handle currency symbols, commas, negative values)
            clean_price_str = re.sub(r'[^\d.-]', '', price_raw)
            try:
                price = float(clean_price_str)
                if price <= 0:
                    errors.append(f"Row {idx}: Price must be positive (got '{price_raw}')")
                    continue
            except ValueError:
                errors.append(f"Row {idx}: Invalid numeric price '{price_raw}'")
                continue

            # Category
            category = (row.get(cat_col) or "General").strip() if cat_col else "General"
            if not category:
                category = "General"

            # Gold Purity normalization
            purity = "22K"
            if purity_col and row.get(purity_col):
                raw_purity = row.get(purity_col, "").strip().upper()
                if "24" in raw_purity:
                    purity = "24K"
                elif "22" in raw_purity:
                    purity = "22K"
                elif "18" in raw_purity:
                    purity = "18K"
                elif "14" in raw_purity:
                    purity = "14K"
                elif "PLAT" in raw_purity:
                    purity = "Platinum"
                else:
                    purity = raw_purity

            # Weight validation
            gross_weight = None
            if weight_col and row.get(weight_col):
                clean_wt = re.sub(r'[^\d.]', '', row.get(weight_col, ""))
                try:
                    gross_weight = float(clean_wt) if clean_wt else None
                except ValueError:
                    pass

            # Stock validation
            stock = 1
            if stock_col and row.get(stock_col):
                clean_stock = re.sub(r'\D', '', row.get(stock_col, ""))
                if clean_stock:
                    stock = int(clean_stock)

            description = (row.get(desc_col) or "").strip() if desc_col else ""
            image_url = (row.get(img_col) or "").strip() if img_col else ""

            # Check existing product by SKU
            product = self.db.query(Product).filter(
                Product.instagram_account_id == account_id,
                Product.sku == sku
            ).first()

            if not product:
                product = Product(
                    instagram_account_id=account_id,
                    sku=sku,
                    name=name,
                    category=category,
                    price=price,
                    gold_purity=purity,
                    gross_weight=gross_weight,
                    stock=stock,
                    description=description,
                    status="active"
                )
                self.db.add(product)
                self.db.flush()
                imported_count += 1
            else:
                product.name = name
                product.category = category
                product.price = price
                product.gold_purity = purity
                product.gross_weight = gross_weight
                product.stock = stock
                if description:
                    product.description = description
                updated_count += 1

            if image_url:
                has_img = self.db.query(ProductImage).filter(
                    ProductImage.product_id == product.id,
                    ProductImage.image_url == image_url
                ).first()
                if not has_img:
                    img = ProductImage(
                        product_id=product.id,
                        image_url=image_url,
                        is_primary=True,
                        alt_text=name
                    )
                    self.db.add(img)

        self.db.commit()
        return {
            "imported_count": imported_count,
            "updated_count": updated_count,
            "errors": errors,
            "total_processed": imported_count + updated_count
        }

    def import_from_csv(self, account_id: str, csv_content: str) -> Tuple[int, List[str]]:
        """Backwards-compatible standard CSV import with auto-mapping."""
        preview = self.preview_csv(csv_content)
        mapping = preview.get("suggested_mappings", {})
        # Ensure default fallbacks
        if "sku" not in mapping and "sku" in preview["headers"]:
            mapping["sku"] = "sku"
        if "name" not in mapping and "name" in preview["headers"]:
            mapping["name"] = "name"
        if "price" not in mapping and "price" in preview["headers"]:
            mapping["price"] = "price"

        result = self.import_mapped_csv(account_id, csv_content, mapping)
        return result["imported_count"] + result["updated_count"], result["errors"]
