import re
import json
from typing import Dict, Any, List, Optional
from app.services.ai.provider_base import AIProvider


class MockAIProvider(AIProvider):
    """
    Deterministic AI Provider for testing, local development, and offline evaluation.
    Provides realistic multilingual intent detection, vision attributes, and replies.
    """

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        lowered = prompt.lower()
        
        # Multilingual greetings
        if any(w in lowered for w in ["kem cho", "namaste", "kemcho", "hello", "hi"]):
            if "kem cho" in lowered or "kemcho" in lowered:
                return "નમસ્તે! 😊 Luxe Aura Jewels માં તમારું સ્વાગત છે. હું તમને કેવી રીતે મદદ કરી શકું?"
            elif "namaste" in lowered or "kaise ho" in lowered:
                return "नमस्ते! 😊 Luxe Aura Jewels में आपका स्वागत है। आज हम आपकी क्या सहायता कर सकते हैं?"
            return "Hello! ✨ Welcome to Luxe Aura Jewels. How may I assist you in finding the perfect jewellery today?"

        # Fallback response
        return "Thank you for reaching out to Luxe Aura Jewels! Our jewellery consultants are here to assist with verified designs, pricing, and certified collections. How can we help you today?"

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        # Extract customer message if wrapped in prompt
        lowered = prompt.lower()
        if 'customer message: "' in lowered:
            start = lowered.find('customer message: "') + len('customer message: "')
            end = lowered.find('"', start)
            if end != -1:
                target_text = lowered[start:end]
            else:
                target_text = lowered[start:]
        else:
            target_text = lowered

        # 1. Detect language
        language = "en"
        if any(w in target_text for w in ["kem cho", "joiye", "che", "hajar", "sudhi", "bhav", "aapo"]):
            language = "gu"
        elif any(w in target_text for w in ["chahiye", "hai", "kitne", "hazar", "bataye", "namaste", "aapke"]):
            language = "hi"

        # 2. Detect category (Check Earrings before Rings so 'earring' is not matched by 'ring')
        category = None
        for cat, synonyms in [
            ("Earrings", ["earring", "jhumka", "tops", "stud", "kadi", "bali", "drop"]),
            ("Rings", [r"\bring\b", "ring", "veenti", "anguthi", "chhap"]),
            ("Necklaces", ["necklace", "haar", "choker", "mala", "set"]),
            ("Bangles", ["bangle", "kada", "bangdi", "kangan", "chudi"]),
            ("Bracelets", ["bracelet", "chain"]),
            ("Pendants", ["pendant", "locket"]),
            ("Mangalsutras", ["mangalsutra", "tanmaniya"]),
            ("Coins", ["coin", "ginni", "sikka", "vedhani"])
        ]:
            if any(syn in target_text for syn in synonyms):
                category = cat
                break

        # 3. Detect budget
        budget_max = None
        # Match ₹15,000, 15000, 50k, 20 hajar, 20 hazar
        k_match = re.search(r'(\d+)\s*k\b', target_text)
        hajar_match = re.search(r'(\d+)\s*(?:hajar|hazar)', target_text)
        number_match = re.search(r'(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{3})+|\d{4,7})', target_text)
        
        if k_match:
            budget_max = float(k_match.group(1)) * 1000
        elif hajar_match:
            budget_max = float(hajar_match.group(1)) * 1000
        elif number_match:
            clean_num = number_match.group(1).replace(",", "")
            budget_max = float(clean_num)

        # 4. Detect purity
        purity = None
        if "22k" in target_text or "22 karat" in target_text or "22kt" in target_text:
            purity = "22K"
        elif "18k" in target_text or "18 karat" in target_text or "18kt" in target_text:
            purity = "18K"
        elif "24k" in target_text or "24 karat" in target_text or "24kt" in target_text:
            purity = "24K"
        elif "14k" in target_text or "14 karat" in target_text:
            purity = "14K"

        # 5. Classify intent
        intent = "product_search"
        words = target_text.split()
        if any(w in target_text for w in ["hi", "hello", "hey", "kem cho", "namaste"]) and len(words) <= 3:
            intent = "greeting"
        elif any(w in target_text for w in ["human", "person", "staff", "manager", "phone", "owner", "vaat"]):
            intent = "human_request"
        elif any(w in target_text for w in ["rate", "bhav", "per gram", "todays gold"]):
            intent = "gold_rate_enquiry"
        elif any(w in target_text for w in ["address", "location", "dukan", "store", "timing", "open"]):
            intent = "store_location"
        elif any(w in target_text for w in ["custom", "design banavvi", "banvana"]):
            intent = "custom_jewellery"
        elif any(w in target_text for w in ["return", "exchange", "refund", "policy"]):
            intent = "store_policy"

        return {
            "intent": intent,
            "language": language,
            "category": category,
            "budget_max": budget_max,
            "purity": purity,
            "metal": "gold" if "gold" in lowered or "sonu" in lowered or "sona" in lowered else "diamond" if "diamond" in lowered or "heera" in lowered else None,
            "confidence": 0.95
        }

    async def analyze_image(
        self,
        image_url: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Simulate vision attribute extraction for testing."""
        return {
            "category": "Rings",
            "metal": "Yellow Gold",
            "purity_estimated": "22K",
            "gemstone": "Diamond solitaire with halo",
            "style": "Contemporary bridal solitaire",
            "search_keywords": ["solitaire", "gold ring", "diamond ring", "22k ring"]
        }

    async def get_embedding(self, text: str) -> List[float]:
        # Return deterministic dummy embedding vector of length 128
        val = (hash(text) % 1000) / 1000.0
        return [val] * 128
