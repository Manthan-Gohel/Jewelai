from app.services.catalogue.catalogue_service import CatalogueService
from app.models.models import Product, InstagramAccount


def test_catalogue_csv_bulk_import(db_session):
    account = db_session.query(InstagramAccount).first()
    cat_service = CatalogueService(db_session)

    csv_data = """sku,name,category,price,purity,weight,stock,description,image_url
CSV-RG-01,Diamond Floral Ring,Rings,42000,18K,3.5,4,Floral diamond ring,https://example.com/ring.jpg
CSV-NK-02,Heritage Gold Choker,Necklaces,95000,22K,24.0,2,Royal choker,https://example.com/choker.jpg
"""
    count, errors = cat_service.import_from_csv(account.id, csv_data)
    assert count == 2
    assert len(errors) == 0

    p1 = db_session.query(Product).filter(Product.sku == "CSV-RG-01").first()
    assert p1 is not None
    assert p1.price == 42000.0
    assert p1.gold_purity == "18K"
    assert len(p1.images) == 1
    assert p1.images[0].image_url == "https://example.com/ring.jpg"


def test_catalogue_csv_import_handles_errors(db_session):
    account = db_session.query(InstagramAccount).first()
    cat_service = CatalogueService(db_session)

    invalid_csv = """sku,name,category,price
,Missing SKU,Rings,15000
BAD-PRICE,Gold Ring,Rings,not_a_number
"""
    count, errors = cat_service.import_from_csv(account.id, invalid_csv)
    assert count == 0
    assert len(errors) == 2
