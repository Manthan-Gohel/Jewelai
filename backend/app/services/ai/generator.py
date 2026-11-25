from typing import List, Dict, Any, Optional
import logging
from app.models.models import Product, KnowledgeDocument, BusinessSettings
from app.services.ai.provider_base import AIProvider

logger = logging.getLogger(__name__)


def build_system_instruction(
    settings: Optional[BusinessSettings],
    language: str = "en"
) -> str:
    biz_name = settings.business_name if settings and settings.business_name else "this jewellery business"
    tone = settings.tone if settings else "luxurious"
    custom_prompt = settings.system_prompt if settings and settings.system_prompt else ""

    lang_guideline = {
        "gu": "Respond primarily in natural, polite Gujarati (or Gujarati script/transliteration matching the customer).",
        "hi": "Respond in polite, warm Hindi (Hinglish or Devanagari matching the customer).",
        "en": "Respond in elegant, polished English with friendly Instagram tone."
    }.get(language, "Respond in the customer's language.")

    base_prompt = f"""
You are the official AI jewellery sales assistant for {biz_name}.
Tone: {tone.capitalize()}, warm, elegant, concise, and trustworthy.

LANGUAGE REQUIREMENT:
{lang_guideline}

STRICT NON-NEGOTIABLE OPERATIONAL RULES:
1. ONLY recommend products explicitly provided in the 'VERIFIED CATALOGUE' section.
2. ALWAYS use the exact verified prices (in ₹ INR). NEVER invent or approximate a price.
3. NEVER invent or assume gold purity, diamond specs, weight, or availability.
4. If no catalogue products match the customer's budget or request, clearly state that no direct match is currently in stock, and offer to show other options or connect them with our jewellery specialists.
5. Keep responses short, concise, and natural for Instagram DMs (2-4 brief sentences maximum).
6. Use emojis tastefully (e.g. ✨, 💎, 😊, ❤️).
7. If the customer asks for a discount, negotiation, or complaint, politely offer to connect them with a store manager.

{custom_prompt}
"""
    return base_prompt.strip()


class ResponseGenerator:
    def __init__(self, provider: AIProvider):
        self.provider = provider

    async def generate_response(
        self,
        customer_message: str,
        detected_language: str,
        detected_intent: str,
        products: List[Product],
        knowledge_docs: List[KnowledgeDocument],
        settings: Optional[BusinessSettings],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Generate grounded, natural Instagram DM response.
        """
        system_instruction = build_system_instruction(settings, detected_language)

        # Format verified products
        products_context = "No products found in catalogue matching this request."
        if products:
            p_list = []
            for p in products:
                img_url = p.images[0].image_url if p.images else "None"
                p_list.append(
                    f"- Product: {p.name} (SKU: {p.sku})\n"
                    f"  Verified Price: ₹{p.price:,.0f}\n"
                    f"  Gold Purity: {p.gold_purity or 'N/A'}\n"
                    f"  Gross Weight: {p.gross_weight or 'N/A'}g\n"
                    f"  Availability: {'In Stock' if p.stock > 0 else 'Made to Order'}\n"
                    f"  Image URL: {img_url}"
                )
            products_context = "\n".join(p_list)

        # Format knowledge docs
        docs_context = ""
        if knowledge_docs:
            d_list = [f"[{d.category.upper()}] {d.title}: {d.content}" for d in knowledge_docs]
            docs_context = "\n".join(d_list)

        # Format store info
        store_info = ""
        if settings:
            rates = []
            for purity in ("24k", "22k", "18k"):
                rate = getattr(settings, f"gold_rate_{purity}_per_10g", None)
                if rate and rate > 0:
                    rates.append(f"{purity.upper()}: ₹{rate:,.0f}/10g")
            store_info = (
                f"Store Timings: {settings.store_timings or 'Not configured; ask the store'}\n"
                f"Store Address: {settings.store_address or 'Not configured; ask the store'}\n"
                f"Manually saved gold rates (not a live feed): {' | '.join(rates) or 'Not configured; do not quote a rate'}.\n"
                "Confirm saved rates with the store before presenting them as current."
            )

        # Build prompt
        prompt_parts = [
            f"CUSTOMER MESSAGE: \"{customer_message}\"",
            f"DETECTED INTENT: {detected_intent}",
            f"TARGET LANGUAGE: {detected_language}",
            "",
            "VERIFIED CATALOGUE PRODUCTS:",
            products_context,
            "",
            "BUSINESS KNOWLEDGE & POLICIES:",
            docs_context or "Standard business policies apply.",
            "",
            "STORE DETAILS:",
            store_info
        ]

        if conversation_history:
            history_str = "\n".join([f"{m.get('sender', 'user')}: {m.get('content', '')}" for m in conversation_history[-4:]])
            prompt_parts.insert(1, f"RECENT CONVERSATION:\n{history_str}\n")

        full_prompt = "\n".join(prompt_parts)

        return await self.provider.generate_text(
            prompt=full_prompt,
            system_instruction=system_instruction,
            temperature=0.2
        )
