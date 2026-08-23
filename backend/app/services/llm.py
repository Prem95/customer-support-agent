import logging
from typing import TypeVar

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self, settings: Settings):
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=settings.llm_temperature,
            timeout=settings.llm_timeout_seconds,
            max_retries=1,
            default_headers={"X-Title": settings.openrouter_app_title},
        )

    async def complete(self, system: str, user: str, output_type: type[T]) -> tuple[T, dict]:
        # OpenRouter structured outputs: response_format json_schema enforced server-side.
        # include_raw keeps the AIMessage so token usage can be reported alongside.
        structured = self._llm.with_structured_output(
            output_type, method="json_schema", include_raw=True
        )
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                result = await structured.ainvoke(messages)
                if result["parsed"] is None:
                    raise result["parsing_error"] or ValueError("no parsed output")
                usage = getattr(result["raw"], "usage_metadata", None) or {}
                return result["parsed"], usage
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.warning("LLM call failed (attempt %d): %s", attempt + 1, exc)
        raise LLMError(str(last_error))
