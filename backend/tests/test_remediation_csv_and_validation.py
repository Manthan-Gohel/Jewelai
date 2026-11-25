import pytest
import json
import io
from fastapi.testclient import TestClient
from app.services.catalogue.catalogue_service import CatalogueService
from app.services.ai.validator import factual_validator
from app.models.models import Product, InstagramAccount, Conversation, Message, Customer, AutomationLog
from app.workers.tasks import process_webhook_event_logic


def test_csv_preview_auto_detects_client_headers(db_session):
    """
    Test CSV Preview parsing and fuzzy header recognition across
    typical jewellery ERP/accounting field names.
    """
    cat_service = CatalogueService(db_session)
    client_csv = """Item Code,Item Title,Item Group,M.R.P.,Gold Purity,Weight (g),Available Qty,Photo URL
JW-TEST-501,22K Royal Peacock Choker,Necklaces,"₹125,000",22K,28.5,2,https://images.unsplash.com/peacock.jpg
JW-TEST-502,18K Diamond Solitaire Ring,Rings,"₹45,000",18K,3.2,5,https://images.unsplash.com/solitaire.jpg
"""
    preview = cat_service.preview_csv(client_csv)
    
    assert len(preview["headers"]) == 8
    assert "Item Code" in preview["headers"]
    assert "M.R.P." in preview["headers"]
    assert len(preview["sample_rows"]) == 2

    # Check suggested mappings
    mappings = preview["suggested_mappings"]
    assert mappings.get("sku") == "Item Code"
    assert mappings.get("name") == "Item Title"
    assert mappings.get("category") == "Item Group"
    assert mappings.get("price") == "M.R.P."
    assert mappings.get("gold_purity") == "Gold Purity"
    assert mappings.get("gross_weight") == "Weight (g)"
    assert mappings.get("stock") == "Available Qty"
    assert mappings.get("image_url") == "Photo URL"


def test_csv_import_mapped_success(db_session):
    """
    Test transactional mapped CSV import.
    """
    account = db_session.query(InstagramAccount).first()
    cat_service = CatalogueService(db_session)

    client_csv = """Design Code,Product Name,Classification,Selling Price,Touch,Gross Wt,Qty
MAP-001,Handcrafted 22K Kada,Bangles,68500,22KT,18.4,3
MAP-002,18K Emerald Drop Earrings,Earrings,32000,18KT,4.1,6
"""
    mapping = {
        "sku": "Design Code",
        "name": "Product Name",
        "category": "Classification",
        "price": "Selling Price",
        "gold_purity": "Touch",
        "gross_weight": "Gross Wt",
        "stock": "Qty"
    }

    result = cat_service.import_mapped_csv(
        account_id=account.id,
        csv_content=client_csv,
        mapping=mapping
    )

    assert result["imported_count"] == 2
    assert len(result["errors"]) == 0

    p = db_session.query(Product).filter(Product.sku == "MAP-001").first()
    assert p is not None
    assert p.name == "Handcrafted 22K Kada"
    assert p.price == 68500.0
    assert p.gold_purity == "22K"
    assert p.gross_weight == 18.4
    assert p.stock == 3


def test_csv_import_validation_errors_reported_gracefully(db_session):
    """
    Test that invalid prices (negative or alphabetic) and missing SKUs are caught,
    reported with row numbers, and valid rows are still imported safely.
    """
    account = db_session.query(InstagramAccount).first()
    cat_service = CatalogueService(db_session)

    bad_csv = """Code,Title,Price
VAL-GOOD-1,Valid Gold Ring,18500
,Missing SKU Ring,22000
VAL-BAD-2,Negative Price Ring,-5000
VAL-BAD-3,Invalid Non-numeric Price,CallForPrice
"""
    mapping = {
        "sku": "Code",
        "name": "Title",
        "price": "Price"
    }

    result = cat_service.import_mapped_csv(
        account_id=account.id,
        csv_content=bad_csv,
        mapping=mapping
    )

    assert result["imported_count"] == 1
    assert len(result["errors"]) == 3
    assert any("Row 3" in e and "Missing SKU" in e for e in result["errors"])
    assert any("Row 4" in e and "positive" in e for e in result["errors"])
    assert any("Row 5" in e and "Invalid numeric" in e for e in result["errors"])


def test_factual_firewall_detects_phantom_availability_when_no_products():
    """
    Verify that claiming stock availability or quoting specific prices when
    no products match is blocked by the factual validator firewall.
    """
    hallucinated_text = "Yes, we have that in stock in our showroom ready to ship for ₹14,500!"
    
    is_valid, violations, fallback = factual_validator.validate_response(
        response_text=hallucinated_text,
        products=[],  # Zero matching products found in catalogue
        language="en"
    )
    assert is_valid is False
    assert len(violations) > 0
    assert "stock" in violations[0].lower() or "price" in violations[0].lower()
    # Safely substituted with store expert connection
    assert "jewellery specialist" in fallback.lower()


def test_factual_firewall_detects_unverified_purity():
    """
    Verify that claiming 24K pure gold for an 18K item is flagged.
    """
    product = Product(
        sku="DIA-18K-01",
        name="Diamond Ring",
        category="Rings",
        price=35000.0,
        gold_purity="18K"
    )

    bad_purity_text = "This gorgeous piece is crafted in 24K pure gold for ₹35,000."
    is_valid, violations, fallback = factual_validator.validate_response(
        response_text=bad_purity_text,
        products=[product],
        language="en"
    )
    assert is_valid is False
    assert any("24k" in v.lower() for v in violations)


def test_api_csv_preview_and_mapped_endpoints(client: TestClient):
    """
    Test FastAPI endpoints /api/v1/products/csv-preview and /api/v1/products/csv-import-mapped
    """
    csv_bytes = b"Item Code,Product,Rate\nAPI-01,Gold Chain,35000\nAPI-02,Silver Coin,2500\n"
    
    # 1. Preview
    res_preview = client.post(
        "/api/v1/products/csv-preview",
        files={"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")}
    )
    assert res_preview.status_code == 200
    p_data = res_preview.json()
    assert "headers" in p_data
    assert "Item Code" in p_data["headers"]

    # 2. Mapped Import
    mapping_payload = {
        "sku": "Item Code",
        "name": "Product",
        "price": "Rate"
    }
    res_import = client.post(
        "/api/v1/products/csv-import-mapped",
        files={"file": ("test.csv", io.BytesIO(csv_bytes), "text/csv")},
        data={"mapping": json.dumps(mapping_payload)}
    )
    assert res_import.status_code == 200
    imp_data = res_import.json()
    assert imp_data["imported_count"] == 2
