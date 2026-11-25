from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.products import router as products_router
from app.api.v1.knowledge import router as knowledge_router
from app.api.v1.ai import router as ai_router
from app.api.v1.settings import router as settings_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.health import router as health_router
from app.api.v1.posts import router as posts_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Authentication & Instagram OAuth"])
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Meta Webhooks"])
api_router.include_router(conversations_router, prefix="/conversations", tags=["Conversations & Inbox"])
api_router.include_router(products_router, prefix="/products", tags=["Jewellery Catalogue"])
api_router.include_router(posts_router, prefix="/posts", tags=["Post & Reel Product Linking"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["Knowledge & FAQs"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Engine & Playground"])
api_router.include_router(settings_router, prefix="/settings", tags=["Business Settings"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics & Logs"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
