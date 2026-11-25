from typing import Dict, Any, List
import logging
from app.services.ai.provider_base import AIProvider

logger = logging.getLogger(__name__)

VISION_PROMPT = """
Analyze this jewellery reference photograph for our luxury jewellery catalogue search.
Identify:
1. Category: One of ["Rings", "Necklaces", "Earrings", "Bangles", "Bracelets", "Pendants", "Mangalsutras", "Coins"]
2. Metal Color & Type: e.g. "Yellow Gold", "Rose Gold", "White Gold", "Platinum"
3. Estimated Purity: e.g. "22K", "18K", "14K"
4. Gemstones: e.g. "Diamonds", "Polki", "Kundan", "Emeralds", "Rubies", "Pearls", "Plain Metal"
5. Style & Craftsmanship: e.g. "Traditional Temple", "Solitaire", "Floral Motif", "Contemporary", "Filigree", "Antique"
6. Search keywords: Top 4 search terms to match similar products in our stock.

Return strictly as JSON:
{
  "category": "Necklaces",
  "metal": "Yellow Gold",
  "purity_estimated": "22K",
  "gemstones": "Polki with emerald beads",
  "style": "Traditional bridal choker",
  "search_keywords": ["choker", "temple necklace", "bridal necklace", "emerald gold"]
}
"""


class VisionService:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def analyze_jewellery_photo(self, image_url: str) -> Dict[str, Any]:
        """
        Analyze customer reference jewellery image and extract visual attributes.
        """
        try:
            return await self.provider.analyze_image(image_url, prompt=VISION_PROMPT)
        except Exception as e:
            logger.error(f"Vision analysis failed for image {image_url}: {e}")
            return {
                "category": None,
                "metal": "Gold",
                "purity_estimated": "22K",
                "gemstones": "None",
                "style": "Fine Jewellery",
                "search_keywords": ["gold jewellery"]
            }
