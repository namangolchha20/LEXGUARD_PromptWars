class AIError(Exception):
    """Base exception for AI provider failures."""


class GeminiError(AIError):
    """Raised when Gemini API calls fail."""


class StructuredOutputError(AIError):
    """Raised when model output fails Pydantic validation."""
