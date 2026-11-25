from app.models.models import Product, BusinessSettings
from app.services.ai.validator import factual_validator


def test_verified_price_passes_validation():
    product = Product(
        sku="TEST-001",
        name="22K Classic Gold Hoops",
        category="Earrings",
        price=11200.0,
        gold_purity="22K"
    )
    
    reply = "Hello! Yes, our 22K Classic Gold Hoops are available for ₹11,200. Would you like to see more details?"
    
    is_valid, violations, final_text = factual_validator.validate_response(
        response_text=reply,
        products=[product],
        language="en"
    )
    assert is_valid is True
    assert len(violations) == 0
    assert final_text == reply


def test_hallucinated_price_triggers_fallback():
    product = Product(
        sku="TEST-001",
        name="22K Classic Gold Hoops",
        category="Earrings",
        price=11200.0,
        gold_purity="22K"
    )
    
    # Fabricated price 6,500 that does not match 11,200
    hallucinated_reply = "We have gold hoops for only ₹6,500 in 22K gold."
    
    is_valid, violations, final_text = factual_validator.validate_response(
        response_text=hallucinated_reply,
        products=[product],
        language="en"
    )
    assert is_valid is False
    assert len(violations) > 0
    assert "₹6,500" in violations[0]
    # Replaced with polite human assistance guarantee
    assert "jewellery specialist" in final_text.lower()


def test_gujarati_safe_fallback_on_unverified_claim():
    product = Product(sku="P1", name="Ring", category="Rings", price=25000.0)
    fake_reply = "આ રિંગ તમને ₹12,000 માં મળી જશે."

    is_valid, violations, final_text = factual_validator.validate_response(
        response_text=fake_reply,
        products=[product],
        language="gu"
    )
    assert is_valid is False
    assert "જ્વેલરી એક્સપર્ટ" in final_text
