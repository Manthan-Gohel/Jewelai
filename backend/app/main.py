import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.api.v1 import api_router
from app.api.deps import get_current_user, get_current_instagram_account

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("jewelai")
# HTTPX's INFO request URLs can include OAuth credentials in query strings.
logging.getLogger("httpx").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("JewelAI backend starting up. Migrations managed exclusively via Alembic.")
    yield
    logger.info("Shutting down JewelAI backend.")


app = FastAPI(
    title="JewelAI — Official Instagram AI Assistant API",
    description="Production-grade backend powering Meta Instagram DM sales assistant for luxury jewellery brands.",
    version=settings.VERSION,
    lifespan=lifespan
)

# Enable CORS with configured origins (reject wildcard credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def browser_session_security(request, call_next):
    webhook_path = f"{settings.API_V1_STR}/webhooks/instagram"
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.url.path != webhook_path:
        origin = request.headers.get("origin")
        if origin and origin not in settings.CORS_ORIGINS:
            return JSONResponse({"detail": "This origin is not permitted."}, status_code=403)
        if request.cookies.get("jewelai_session") and not request.headers.get("authorization"):
            if request.headers.get("X-JewelAI-Request") != "1" or request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail": "Please refresh this page and try again."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    if request.url.path.startswith(f"{settings.API_V1_STR}/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "meta_api_version": settings.META_API_VERSION
    }
