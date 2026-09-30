"""Shared Gemini chat model for supervisor and subagents."""

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import settings


def get_chat_model() -> ChatGoogleGenerativeAI:
    """Return a low-temperature Gemini client for tool-calling agents."""
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.google_api_key,
        temperature=0.1,
        max_tokens=1500,
    )
