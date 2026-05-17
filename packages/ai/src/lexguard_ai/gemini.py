import json
import logging
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from lexguard_ai.config import AISettings
from lexguard_ai.exceptions import GeminiError, StructuredOutputError
from lexguard_ai.retry import with_retry

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


def _is_retryable(exc: Exception) -> bool:
    message = str(exc).lower()
    retryable_signals = ("429", "500", "502", "503", "504", "rate", "timeout", "unavailable")
    return any(signal in message for signal in retryable_signals)


class GeminiClient:
    """Async Gemini client producing structured JSON validated by Pydantic."""

    def __init__(self, settings: AISettings | None = None) -> None:
        self._settings = settings or AISettings()
        self._client: object | None = None

    def _get_client(self) -> object:
        if self._client is None:
            if not self._settings.gemini_api_key:
                raise GeminiError("GEMINI_API_KEY is not configured")
            try:
                from google import genai

                self._client = genai.Client(api_key=self._settings.gemini_api_key)
            except ImportError as exc:
                raise GeminiError(
                    "google-genai is not installed. Run: uv sync --package lexguard-ai"
                ) from exc
        return self._client

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        *,
        system_instruction: str | None = None,
    ) -> T:
        async def _call() -> T:
            return await self._generate_once(prompt, response_model, system_instruction)

        return await with_retry(
            _call,
            max_retries=self._settings.gemini_max_retries,
            base_delay=self._settings.gemini_retry_base_delay,
            retryable=_is_retryable,
        )

    async def _generate_once(
        self,
        prompt: str,
        response_model: type[T],
        system_instruction: str | None,
    ) -> T:
        import asyncio

        from google.genai import types

        client = self._get_client()

        config = types.GenerateContentConfig(
            temperature=self._settings.gemini_temperature,
            response_mime_type="application/json",
            response_schema=response_model,
            system_instruction=system_instruction,
        )

        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=self._settings.gemini_model,
                contents=prompt,
                config=config,
            )
        except Exception as exc:
            raise GeminiError(f"Gemini API call failed: {exc}") from exc

        raw_text = response.text
        if not raw_text:
            raise GeminiError("Gemini returned empty response")

        try:
            return response_model.model_validate_json(raw_text)
        except ValidationError:
            pass

        try:
            data = json.loads(raw_text)
            return response_model.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            raise StructuredOutputError(
                f"Failed to validate Gemini output as {response_model.__name__}: {exc}"
            ) from exc

    async def health_check(self) -> bool:
        return bool(self._settings.gemini_api_key)
