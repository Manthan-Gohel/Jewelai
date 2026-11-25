from typing import Dict, Any, Optional
import logging
from app.services.ai.provider_base import AIProvider

logger = logging.getLogger(__name__)

INTENT_EXTRACTION_SYSTEM_PROMPT = """
You are an expert multilingual jewellery customer intent classifier for a luxury jewellery brand.
Supported languages:
- English (en)
- Hindi (hi) - both Devanagari and Romanized Hinglish (e.g., 'kya aapke paas gold necklace hai?', 'kitne ka hai')
- Gujarati (gu) - both Gujarati script and Romanized Gujlish (e.g., 'Mare 20 hajar ma gold ring joiye', 'su bhav che')

Extract the following JSON structure:
{
  "language": "en" | "hi" | "gu",
  "intent": "greeting" | "product_search" | "price_enquiry" | "purity_enquiry" | "availability" | "custom_jewellery" | "store_location" | "store_policy" | "gold_rate_enquiry" | "discount_enquiry" | "complaint" | "human_request",
  "category": "Rings" | "Necklaces" | "Earrings" | "Bangles" | "Bracelets" | "Pendants" | "Mangalsutras" | "Coins" | null,
  "budget_max": number | null,
  "purity": "14K" | "18K" | "22K" | "24K" | null,
  "metal": "Gold" | "Diamond" | "Silver" | "Platinum" | null,
  "style_keywords": [string],
  "confidence": number between 0.0 and 1.0
}
Never fabricate budget or category if not mentioned. Return only the JSON object.
"""


class IntentService:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def detect_intent(self, text: str, has_image: bool = False) -> Dict[str, Any]:
        """
        Detect customer language, primary intent, and search filters.
        """
        if not text and has_image:
            return {
                "language": "en",
                "intent": "image_search",
                "category": None,
                "budget_max": None,
                "purity": None,
                "metal": None,
                "style_keywords": [],
                "confidence": 0.95
            }

        prompt = f"Customer message: \"{text}\"\nHas attached image: {has_image}"
        try:
            result = await self.provider.generate_json(prompt, system_instruction=INTENT_EXTRACTION_SYSTEM_PROMPT)
            if has_image and result.get("intent") in ["product_search", "greeting"]:
                result["intent"] = "image_search"
            return result
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return {
                "language": "en",
                "intent": "product_search",
                "category": None,
                "budget_max": None,
                "purity": None,
                "metal": None,
                "style_keywords": [],
                "confidence": 0.5
            }
