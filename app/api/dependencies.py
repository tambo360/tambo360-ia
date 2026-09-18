"""API dependencies and utilities."""

from app.services.ai_service import AIService, ai_service


def get_ai_service() -> AIService:
    """Provide the singleton Gemini client."""
    return ai_service
