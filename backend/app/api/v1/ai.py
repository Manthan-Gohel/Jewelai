from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import InstagramAccount
from app.schemas.schemas import (
    AITestRequest, AITestResponse,
    ProductResponse, KnowledgeDocResponse
)
from app.api.deps import get_current_instagram_account
from app.services.ai.orchestrator import AIOrchestrator

router = APIRouter()


@router.post("/test", response_model=AITestResponse)
async def test_ai_response(
    data: AITestRequest,
    account: InstagramAccount = Depends(get_current_instagram_account),
    db: Session = Depends(get_db)
):
    """
    AI Testing Playground Endpoint:
    Simulates AI intent detection, vision analysis, knowledge retrieval, response generation,
    and factual anti-hallucination validation without dispatching a live Instagram message.
    """
    orchestrator = AIOrchestrator(db)

    result = await orchestrator.process_message(
        account_id=account.id,
        message_text=data.message,
        image_url=data.image_url,
        conversation_history=data.conversation_history,
        language_override=data.language_override
    )

    retrieved_prods = [
        ProductResponse.model_validate(p) for p in result.get("products", [])
    ]
    retrieved_docs = [
        KnowledgeDocResponse.model_validate(d) for d in result.get("knowledge_docs", [])
    ]

    entities = {
        "category": result.get("category"),
        "budget_max": result.get("budget_max"),
        "purity": result.get("purity"),
        "vision_data": result.get("vision_data")
    }

    return AITestResponse(
        language_detected=result.get("language", "en"),
        intent_detected=result.get("intent", "product_search"),
        extracted_entities=entities,
        retrieved_products=retrieved_prods,
        retrieved_knowledge=retrieved_docs,
        generated_reply=result.get("reply_text", ""),
        fact_validation_passed=result.get("fact_validation_passed", True),
        validation_flags=result.get("validation_flags", []),
        confidence_score=result.get("confidence", 0.9),
        processing_time_ms=result.get("latency_ms", 0)
    )
