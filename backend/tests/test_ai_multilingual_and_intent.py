import asyncio
from app.services.ai.gemini_provider import MockAIProvider
from app.services.ai.intent import IntentService
from app.services.ai.vision import VisionService


def test_gujarati_intent_and_budget_extraction():
    async def _run():
        provider = MockAIProvider()
        intent_service = IntentService(provider)

        text = "Mare 20 hajar ma gold ring joiye"
        result = await intent_service.detect_intent(text)

        assert result["language"] == "gu"
        assert result["category"] == "Rings"
        assert result["budget_max"] == 20000.0
        assert result["intent"] == "product_search"

    asyncio.run(_run())


def test_hindi_intent_and_purity_extraction():
    async def _run():
        provider = MockAIProvider()
        intent_service = IntentService(provider)

        text = "Kya aapke paas 22k gold necklace hai?"
        result = await intent_service.detect_intent(text)

        assert result["language"] == "hi"
        assert result["category"] == "Necklaces"
        assert result["purity"] == "22K"

    asyncio.run(_run())


def test_english_intent_and_budget():
    async def _run():
        provider = MockAIProvider()
        intent_service = IntentService(provider)

        text = "Do you have gold earrings under ₹15,000?"
        result = await intent_service.detect_intent(text)

        assert result["language"] == "en"
        assert result["category"] == "Earrings"
        assert result["budget_max"] == 15000.0

    asyncio.run(_run())


def test_vision_jewellery_analysis():
    async def _run():
        provider = MockAIProvider()
        vision_service = VisionService(provider)

        result = await vision_service.analyze_jewellery_photo("https://example.com/customer_reference.jpg")
        assert result["category"] == "Rings"
        assert "Yellow Gold" in result["metal"]
        assert len(result["search_keywords"]) > 0

    asyncio.run(_run())
