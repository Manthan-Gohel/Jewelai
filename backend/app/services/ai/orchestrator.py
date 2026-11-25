import time
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import logging

from app.models.models import Conversation, Product, KnowledgeDocument, BusinessSettings
from app.services.ai.gemini_provider import get_ai_provider
from app.services.ai.intent import IntentService
from app.services.ai.vision import VisionService
from app.services.ai.retriever import KnowledgeRetriever
from app.services.ai.generator import ResponseGenerator
from app.services.ai.validator import factual_validator

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Main AI Orchestrator:
    1. Understands natural language (En/Hi/Gu) & customer photos
    2. Retrieves verified inventory & business rules
    3. Synthesizes elegant Instagram reply
    4. Enforces strict factual validation before delivery
    """

    def __init__(self, db: Session):
        self.db = db
        self.provider = get_ai_provider()
        self.intent_service = IntentService(self.provider)
        self.vision_service = VisionService(self.provider)
        self.retriever = KnowledgeRetriever(self.db)
        self.generator = ResponseGenerator(self.provider)

    async def process_message(
        self,
        account_id: str,
        message_text: str,
        image_url: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        language_override: Optional[str] = None,
        context_product_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        has_image = bool(image_url)

        # 1. Intent Detection
        intent_data = await self.intent_service.detect_intent(message_text, has_image=has_image)
        language = language_override or intent_data.get("language", "en")
        intent = intent_data.get("intent", "product_search")
        category = intent_data.get("category")
        budget_max = intent_data.get("budget_max")
        purity = intent_data.get("purity")
        keywords = intent_data.get("style_keywords", [])

        # 2. Vision Understanding (if reference image attached)
        vision_data = None
        if has_image:
            vision_data = await self.vision_service.analyze_jewellery_photo(image_url)
            if not category and vision_data.get("category"):
                category = vision_data["category"]
            if vision_data.get("search_keywords"):
                keywords.extend(vision_data["search_keywords"])

        # 3. Retrieve Verified Knowledge & Products
        settings = self.retriever.get_business_settings(account_id)
        
        products: List[Product] = []
        # First priority: explicitly linked products from shared reel/post context
        if context_product_ids:
            context_prods = self.db.query(Product).filter(
                Product.id.in_(context_product_ids),
                Product.instagram_account_id == account_id
            ).all()
            products.extend(context_prods)

        if len(products) < 3 and intent in ["product_search", "image_search", "price_enquiry", "purity_enquiry", "availability", "general_inquiry"]:
            searched = self.retriever.search_products(
                account_id=account_id,
                category=category,
                budget_max=budget_max,
                purity=purity,
                keywords=keywords,
                limit=3 - len(products)
            )
            existing_ids = {p.id for p in products}
            for p in searched:
                if p.id not in existing_ids:
                    products.append(p)

        knowledge_docs = self.retriever.search_knowledge_docs(
            account_id=account_id,
            intent=intent,
            query_text=message_text
        )

        # 4. Response Generation
        raw_reply = await self.generator.generate_response(
            customer_message=message_text,
            detected_language=language,
            detected_intent=intent,
            products=products,
            knowledge_docs=knowledge_docs,
            settings=settings,
            conversation_history=conversation_history
        )

        # 5. Factual & Price Validation
        is_valid, violations, final_reply = factual_validator.validate_response(
            response_text=raw_reply,
            products=products,
            settings=settings,
            language=language
        )

        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "reply_text": final_reply,
            "language": language,
            "intent": intent,
            "category": category,
            "budget_max": budget_max,
            "purity": purity,
            "products": products,
            "knowledge_docs": knowledge_docs,
            "vision_data": vision_data,
            "fact_validation_passed": is_valid,
            "validation_flags": violations,
            "latency_ms": latency_ms,
            "confidence": intent_data.get("confidence", 0.9)
        }
