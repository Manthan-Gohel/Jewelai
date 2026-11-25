from typing import List, Optional, Dict, Any
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.core.database import get_db
from app.models.models import Product, ProductImage, InstagramAccount
from app.schemas.schemas import (
    ProductCreate, ProductUpdate, ProductResponse, ProductListResponse,
    CSVPreviewResponse
)
from app.api.deps import get_current_instagram_account
from app.services.catalogue.catalogue_service import CatalogueService

router = APIRouter()


@router.get("", response_model=ProductListResponse)
def list_products(
    category: Optional[str] = None,
    purity: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.instagram_account_id == account.id)

    if category and category != "All":
        query = query.filter(Product.category.ilike(f"%{category}%"))

    if purity and purity != "All":
        query = query.filter(Product.gold_purity == purity)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)

    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )

    total = query.count()
    products = query.order_by(desc(Product.created_at)).offset(offset).limit(limit).all()

    # Get distinct categories
    all_cats = db.query(Product.category).filter(
        Product.instagram_account_id == account.id
    ).distinct().all()
    categories = sorted([c[0] for c in all_cats if c[0]])

    return ProductListResponse(
        items=products,
        total=total,
        categories=categories
    )


@router.post("", response_model=ProductResponse)
def create_product(
    data: ProductCreate,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    # Check duplicate SKU
    existing = db.query(Product).filter(
        Product.instagram_account_id == account.id,
        Product.sku == data.sku
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Product with SKU '{data.sku}' already exists.")

    product = Product(
        instagram_account_id=account.id,
        sku=data.sku,
        name=data.name,
        category=data.category,
        description=data.description,
        price=data.price,
        gold_purity=data.gold_purity,
        gross_weight=data.gross_weight,
        net_weight=data.net_weight,
        diamond_specs=data.diamond_specs,
        stock=data.stock,
        status=data.status,
        tags=data.tags
    )
    db.add(product)
    db.flush()

    for idx, url in enumerate(data.image_urls):
        img = ProductImage(
            product_id=product.id,
            image_url=url,
            is_primary=(idx == 0),
            alt_text=data.name
        )
        db.add(img)

    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: str,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.instagram_account_id == account.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    update_data: ProductUpdate,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.instagram_account_id == account.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, val in update_data.model_dump(exclude_unset=True).items():
        if field == "image_urls":
            continue
        setattr(product, field, val)

    if update_data.image_urls is not None:
        db.query(ProductImage).filter(ProductImage.product_id == product.id).delete()
        for idx, url in enumerate(update_data.image_urls):
            img = ProductImage(
                product_id=product.id,
                image_url=url,
                is_primary=(idx == 0),
                alt_text=product.name
            )
            db.add(img)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(
    product_id: str,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.instagram_account_id == account.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully"}


@router.post("/csv-preview", response_model=CSVPreviewResponse)
def preview_products_csv(
    file: UploadFile = File(...),
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Parse uploaded CSV, extract headers, return top 5 sample rows,
    and generate suggested column mappings for client review before import.
    """
    content_bytes = file.file.read()
    try:
        csv_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1")

    cat_service = CatalogueService(db)
    preview = cat_service.preview_csv(csv_text)
    return preview


@router.post("/csv-import-mapped")
def import_products_csv_mapped(
    file: UploadFile = File(...),
    mapping: str = Form(...),  # JSON string of standard_field -> csv_header
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    Import jewellery products using explicit client column mappings
    with row-by-row data validation and error reporting.
    """
    try:
        mapping_dict = json.loads(mapping)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid mapping JSON: {e}")

    content_bytes = file.file.read()
    try:
        csv_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1")

    cat_service = CatalogueService(db)
    try:
        result = cat_service.import_mapped_csv(
            account_id=account.id,
            csv_content=csv_text,
            mapping=mapping_dict
        )
        return result
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))


@router.post("/import-csv")
def import_products_csv(
    file: UploadFile = File(...),
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """Bulk import jewellery items from uploaded CSV."""
    content_bytes = file.file.read()
    try:
        csv_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        csv_text = content_bytes.decode("latin-1")

    cat_service = CatalogueService(db)
    count, errors = cat_service.import_from_csv(account.id, csv_text)

    return {
        "imported_count": count,
        "errors": errors,
        "message": f"Successfully processed {count} products"
    }
