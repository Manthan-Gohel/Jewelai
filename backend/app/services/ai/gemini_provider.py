import json
import logging
import httpx
from typing import Dict, Any, List, Optional
from app.core.config import settings
from app.services.ai.provider_base import AIProvider
from app.services.ai.mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


class AIProviderError(RuntimeError):
    """Raised when the production AI engine cannot fulfill an inference request."""
    pass


class GeminiAIProvider(AIProvider):
    """
    Official Google GenAI SDK implementation (google-genai >= 1.0.0).
    Uses the modern unified Client: `from google import genai`
    Provides:
    - Text reasoning & dialogue synthesis (gemini-2.5-flash / gemini-1.5-flash)
    - Multimodal jewellery image analysis
    - Factual JSON schema generation
    - Vector embeddings for retrieval
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        # In production, mock fallbacks are completely eliminated
        self.mock_fallback = MockAIProvider() if settings.ENVIRONMENT != "production" else None
        self.client = None
        self._types = None

        if self.api_key:
            try:
                from google import genai
                from google.genai import types
                self.client = genai.Client(api_key=self.api_key)
                self._types = types
                logger.info("Initialized official Google GenAI client successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Google GenAI SDK client: {e}")
                self.client = None
                self._types = None

    @property
    def is_live(self) -> bool:
        return bool(self.api_key and self.client and not settings.MOCK_AI_PROVIDER)

    def _get_candidate_models(self) -> List[str]:
        candidates = [
            settings.GEMINI_TEXT_MODEL,
            "gemini-3.8-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash"
        ]
        seen = set()
        return [m for m in candidates if not (m in seen or seen.add(m))]

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        if not self.is_live:
            if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
                raise AIProviderError(
                    "AI generation failed: No live GEMINI_API_KEY configured in production. "
                    "Mock replies are strictly forbidden in production."
                )
            return await self.mock_fallback.generate_text(prompt, system_instruction, temperature)

        models_to_try = self._get_candidate_models()
        last_error = None

        for model_name in models_to_try:
            try:
                # 1. Native async client execution via client.aio
                if hasattr(self.client, "aio") and hasattr(self.client.aio, "models"):
                    config = self._types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=600
                    ) if system_instruction else self._types.GenerateContentConfig(
                        temperature=temperature,
                        max_output_tokens=600
                    )
                    response = await self.client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    return response.text.strip()
                elif hasattr(self.client, "models"):
                    # Fallback to threadpool if aio is not initialized
                    import asyncio
                    config = self._types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        max_output_tokens=600
                    )
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    return response.text.strip()
            except Exception as e:
                err_str = str(e)
                last_error = e
                # If model is deprecated or not found, try next candidate model
                if "404" in err_str or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                    logger.warning(f"Gemini model '{model_name}' unavailable ({err_str[:80]}). Trying next candidate...")
                    continue
                else:
                    logger.error(f"Gemini generate_text API error on {model_name}: {e}")
                    break

        if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
            raise AIProviderError(f"Google GenAI API call failed: {last_error}")
        return await self.mock_fallback.generate_text(prompt, system_instruction, temperature)

    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.is_live:
            if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
                raise AIProviderError(
                    "AI JSON parsing failed: No live GEMINI_API_KEY configured in production."
                )
            return await self.mock_fallback.generate_json(prompt, system_instruction)

        models_to_try = self._get_candidate_models()
        last_error = None

        for model_name in models_to_try:
            try:
                if hasattr(self.client, "aio") and hasattr(self.client.aio, "models"):
                    config = self._types.GenerateContentConfig(
                        system_instruction=system_instruction or "You are an accurate intent & entity parser for a fine jewellery assistant. Return only valid JSON.",
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                    response = await self.client.aio.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    raw = response.text.strip()
                    return json.loads(raw)
                elif hasattr(self.client, "models"):
                    import asyncio
                    config = self._types.GenerateContentConfig(
                        system_instruction=system_instruction or "You are an accurate intent & entity parser for a fine jewellery assistant. Return only valid JSON.",
                        temperature=0.1,
                        response_mime_type="application/json"
                    )
                    response = await asyncio.to_thread(
                        self.client.models.generate_content,
                        model=model_name,
                        contents=prompt,
                        config=config
                    )
                    raw = response.text.strip()
                    return json.loads(raw)
            except Exception as e:
                err_str = str(e)
                last_error = e
                if "404" in err_str or "not found" in err_str.lower() or "no longer available" in err_str.lower():
                    logger.warning(f"Gemini model '{model_name}' unavailable ({err_str[:80]}). Trying next candidate...")
                    continue
                else:
                    logger.error(f"Gemini generate_json API error on {model_name}: {e}")
                    break

        if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
            raise AIProviderError(f"Google GenAI JSON generation failed: {last_error}")
        return await self.mock_fallback.generate_json(prompt, system_instruction)

    async def analyze_image(
        self,
        image_url: str,
        prompt: str
    ) -> Dict[str, Any]:
        if not self.is_live:
            if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
                raise AIProviderError(
                    "AI Vision analysis failed: No live GEMINI_API_KEY configured in production."
                )
            return await self.mock_fallback.analyze_image(image_url, prompt)

        try:
            # Download image bytes asynchronously
            async with httpx.AsyncClient(timeout=15.0) as http_client:
                resp = await http_client.get(image_url)
                resp.raise_for_status()
                image_bytes = resp.content
                content_type = resp.headers.get("content-type", "image/jpeg")

            part = self._types.Part.from_bytes(data=image_bytes, mime_type=content_type)
            config = self._types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )

            if hasattr(self.client, "aio") and hasattr(self.client.aio, "models"):
                response = await self.client.aio.models.generate_content(
                    model=settings.GEMINI_VISION_MODEL,
                    contents=[prompt, part],
                    config=config
                )
            else:
                import asyncio
                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=settings.GEMINI_VISION_MODEL,
                    contents=[prompt, part],
                    config=config
                )
            return json.loads(response.text.strip())
        except Exception as e:
            logger.error(f"Gemini analyze_image API error: {e}")
            if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
                raise AIProviderError(f"Google GenAI vision analysis failed: {e}")
            return await self.mock_fallback.analyze_image(image_url, prompt)

    async def get_embedding(self, text: str) -> List[float]:
        if not self.is_live:
            if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
                raise AIProviderError("No live GEMINI_API_KEY configured for embedding calculation.")
            return await self.mock_fallback.get_embedding(text)

        try:
            if hasattr(self.client, "aio") and hasattr(self.client.aio, "models"):
                result = await self.client.aio.models.embed_content(
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=text
                )
            else:
                import asyncio
                result = await asyncio.to_thread(
                    self.client.models.embed_content,
                    model=settings.GEMINI_EMBEDDING_MODEL,
                    contents=text
                )
            # Modern google-genai returns result.embeddings[0].values
            if hasattr(result, "embeddings") and result.embeddings:
                return result.embeddings[0].values
            return []
        except Exception as e:
            logger.warning(f"Gemini embedding error: {e}")
            if settings.ENVIRONMENT == "production" or not settings.MOCK_AI_PROVIDER:
                raise AIProviderError(f"Google GenAI embedding calculation failed: {e}")
            return await self.mock_fallback.get_embedding(text)


def get_ai_provider() -> AIProvider:
    if settings.ENVIRONMENT == "production":
        if settings.MOCK_AI_PROVIDER:
            raise ValueError("MOCK_AI_PROVIDER cannot be enabled in production environment.")
        return GeminiAIProvider()
    if settings.MOCK_AI_PROVIDER or (settings.ENVIRONMENT == "test" and not settings.GEMINI_API_KEY):
        return MockAIProvider()
    return GeminiAIProvider()
