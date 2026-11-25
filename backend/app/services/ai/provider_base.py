from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class AIProvider(ABC):
    """Abstract Base Class for AI model providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Generate conversational text response."""
        pass

    @abstractmethod
    async def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON output."""
        pass

    @abstractmethod
    async def analyze_image(
        self,
        image_url: str,
        prompt: str
    ) -> Dict[str, Any]:
        """Analyze an image using a vision-capable model."""
        pass

    @abstractmethod
    async def get_embedding(
        self,
        text: str
    ) -> List[float]:
        """Generate text embedding vector."""
        pass
