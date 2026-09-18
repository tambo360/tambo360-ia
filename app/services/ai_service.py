"""AI service — LangChain + Google Gemini for TamboEngine descriptions."""

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.config.settings import settings
from app.models.schemas import OutlierDescripcionesIA
from app.core.logging import get_logger
from app.core.security import mask_api_key

logger = get_logger(__name__)


class AIService:
    """Gemini client used only to write outlier descriptions."""

    def __init__(self):
        """Initialize the AI service."""
        # self.client = httpx.AsyncClient(
        #     base_url=settings.openrouter_base_url,
        #     headers={
        #         "Authorization": f"Bearer {settings.openrouter_api_key}",
        #         "Content-Type": "application/json",
        #         "HTTP-Referer": "https://github.com/your-username/template-python-fastapi",
        #         "X-Title": settings.app_name,
        #     },
        #     timeout=60.0
        # )
        self.llm = ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.1,
            max_tokens=1500,
        )
        self.structured_llm = self.llm.with_structured_output(
            OutlierDescripcionesIA,
            method="json_schema",
        )
        logger.info(
            f"AI Service initialized with Gemini model={settings.gemini_model}, "
            f"key={mask_api_key(settings.google_api_key)}"
        )

    async def generate_outlier_descriptions(
        self, messages: list[BaseMessage]
    ) -> OutlierDescripcionesIA:
        """Ask Gemini for structured descriptions of already-detected outliers."""
        logger.info(f"Requesting structured descriptions via {settings.gemini_model}")
        result = await self.structured_llm.ainvoke(messages)
        if isinstance(result, dict):
            result = OutlierDescripcionesIA.model_validate(result)
        logger.info(
            f"Structured AI response received: {len(result.descripciones)} descriptions"
        )
        return result

    async def close(self):
        """Release the Gemini client if the SDK exposes aclose."""
        aclose = getattr(self.llm, "aclose", None)
        if aclose is not None:
            await aclose()
        logger.info("AI service client closed")


ai_service = AIService()
