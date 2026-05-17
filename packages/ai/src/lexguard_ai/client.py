from lexguard_ai.config import AISettings
from lexguard_ai.gemini import GeminiClient


class AIClient:
    """Facade over AI providers — currently backed by Gemini."""

    def __init__(self, settings: AISettings | None = None) -> None:
        self._settings = settings or AISettings()
        self.gemini = GeminiClient(self._settings)

    async def health_check(self) -> bool:
        return await self.gemini.health_check()
