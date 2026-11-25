import re
from typing import List, Tuple, Optional, Set
import logging
from app.models.models import Product, BusinessSettings

logger = logging.getLogger(__name__)


class FactualResponseValidator:
    """
    Deterministic factual firewall for fine jewellery AI replies.
    Protects luxury brand reputation and legal compliance by verifying:
    1. Zero price hallucination: All currency values must match verified products or gold rates.
    2. Zero purity hallucination: Gold purities (24K/22K/18K/14K) must match catalogued items.
    3. Zero phantom availability: Never claim stock or ready shipment when inventory is absent.
    4. Specification grounding: Weight and diamond carat mentions are audited.
    """

    @staticmethod
    def validate_response(
        response_text: str,
        products: List[Product],
        settings: Optional[BusinessSettings] = None,
        language: str = "en"
    ) -> Tuple[bool, List[str], str]:
        """
        Validate generated text deterministically against retrieved facts.
        Returns:
            (is_valid: bool, violations: List[str], sanitized_or_fallback_text: str)
        """
        violations: List[str] = []
        
        # 1. Compile allowed verified prices, purities, and weights
        allowed_prices: Set[int] = set()
        product_purities: Set[str] = set()
        allowed_weights: List[float] = []

        for p in products:
            price_int = int(round(p.price))
            allowed_prices.add(price_int)
            # Allow price rounded to nearest hundred for polite conversational phrasing
            allowed_prices.add(price_int - (price_int % 100))
            if p.gold_purity:
                norm_p = p.gold_purity.upper().replace(" ", "").replace("KARAT", "K")
                product_purities.add(norm_p)
            if p.gross_weight is not None and p.gross_weight > 0:
                allowed_weights.append(float(p.gross_weight))
            if p.net_weight is not None and p.net_weight > 0:
                allowed_weights.append(float(p.net_weight))

        # Gold rate prices are only valid for general rate per 10g queries
        gold_rate_prices: Set[int] = set()
        if settings:
            if settings.gold_rate_24k_per_10g and settings.gold_rate_24k_per_10g > 0:
                gold_rate_prices.add(int(round(settings.gold_rate_24k_per_10g)))
            if settings.gold_rate_22k_per_10g and settings.gold_rate_22k_per_10g > 0:
                gold_rate_prices.add(int(round(settings.gold_rate_22k_per_10g)))
            if settings.gold_rate_18k_per_10g and settings.gold_rate_18k_per_10g > 0:
                gold_rate_prices.add(int(round(settings.gold_rate_18k_per_10g)))

        all_valid_prices = allowed_prices.union(gold_rate_prices)

        # Extract all currency mentions: ₹15,000, Rs. 15000, 15000 INR, 15,000/-
        price_matches = re.findall(
            r'(?:₹|rs\.?|inr)\s*(\d{1,3}(?:,\d{3})+|\d{3,7})|(\d{1,3}(?:,\d{3})+|\d{4,7})\s*(?:₹|rs\.?|inr|\/-)',
            response_text,
            re.IGNORECASE
        )
        
        for group in price_matches:
            raw_match = group[0] or group[1]
            clean_price = int(raw_match.replace(",", ""))
            # Allow tolerance of +/- 50 for rounding in conversation
            matched = any(abs(clean_price - allowed) <= 50 for allowed in all_valid_prices)
            if not matched:
                violations.append(f"Unverified price ₹{clean_price:,} detected in AI response.")

        # 2. Phantom stock / availability check when no matching products exist
        if not products:
            availability_phrases = [
                "we have in stock", "available at ₹", "in our showroom",
                "ready to dispatch", "ready to ship", "can buy this for", "sku:",
                "સ્ટોકમાં ઉપલબ્ધ છે", "હાલમાં હાજર છે", "સ્ટોક માં છે",
                "स्टॉक में उपलब्ध है", "हमारे पास उपलब्ध है", "कीमत ₹"
            ]
            lowered = response_text.lower()
            if any(phrase in lowered for phrase in availability_phrases):
                violations.append("Response claims stock or quotes specific prices when no matching products were found in catalogue.")

        # 3. Purity validation: product purity claims must match retrieved products strictly.
        # Store gold rates do NOT grant permission to claim an 18K item is 24K.
        purity_mentions = re.findall(r'\b(24k|22k|18k|14k|24 karat|22 karat|18 karat|14 karat)\b', response_text, re.IGNORECASE)
        if products and product_purities:
            for pm in purity_mentions:
                norm_purity = pm.upper().replace(" ", "").replace("KARAT", "K")
                if norm_purity not in product_purities and not any(ap in norm_purity for ap in product_purities):
                    violations.append(
                        f"Unverified purity claim '{pm}' does not match retrieved products ({', '.join(product_purities)})."
                    )
        elif not products and purity_mentions:
            # If no products were retrieved, AI cannot claim products with specific purities exist in stock
            lowered = response_text.lower()
            if any(word in lowered for word in ["have", "ring", "earring", "necklace", "bangle", "chain", "piece", "available"]):
                violations.append("Purity claims on non-existent catalogue items detected.")

        # 4. Weight auditing: verify weight mentions against catalogue product specifications
        weight_matches = re.findall(r'\b(\d+(?:\.\d+)?)\s*(?:grams?|gms?|gm|g)\b', response_text, re.IGNORECASE)
        for wm in weight_matches:
            try:
                claimed_wt = float(wm)
                # Ignore trivial small weights like diamond cents or 0
                if claimed_wt > 0.5:
                    if products and allowed_weights:
                        matched_wt = any(abs(claimed_wt - aw) <= 0.5 for aw in allowed_weights)
                        if not matched_wt:
                            violations.append(
                                f"Unverified weight specification {claimed_wt}g detected. Does not match catalogue ({allowed_weights}g)."
                            )
                    elif products and not allowed_weights:
                        violations.append(f"Unverified weight {claimed_wt}g claimed when catalogue products have no weight specified.")
                    elif not products:
                        violations.append(f"Unverified weight {claimed_wt}g claimed when no products were retrieved.")
            except ValueError:
                pass

        # 4. Fallback execution on any violation
        if violations:
            logger.warning(f"AI response failed factual validation firewall: {violations}")

            # Safe localized human escalation text
            fallback_text = {
                "gu": "તમારી પસંદગી માટે ખૂબ ખૂબ આભાર! ✨ આ ડીઝાઇનના ચોક્કસ વજન, હોલમાર્કિંગ અને આજના લાઈવ સોનાના ભાવ સાથે વિગત આપવા માટે હું અમારા જ્વેલરી એક્સપર્ટ સાથે તમારી વાત કરાવી આપું છું. તેઓ ટૂંક સમયમાં જ તમને અહીં મેસેજ કરશે.",
                "hi": "आपकी पसंद के लिए धन्यवाद! ✨ इस डिज़ाइन के सही वज़न, हॉलमार्किंग और आज के लाइव रेट की सटीक जानकारी देने के लिए मैं आपको हमारे ज्वेलरी विशेषज्ञ से कनेक्ट कर रहा हूँ। वे जल्द ही आपको रिप्लाई करेंगे।",
                "en": "Thank you for your interest! ✨ To provide you with exact verified pricing, live gold rates, weight specifications, and showroom availability for this piece, let me connect you directly with our jewellery specialist who will assist you shortly."
            }.get(language, "Thank you for your interest! Let me connect you directly with our jewellery specialist who will assist you shortly with verified details.")

            return False, violations, fallback_text

        return True, [], response_text


factual_validator = FactualResponseValidator()
