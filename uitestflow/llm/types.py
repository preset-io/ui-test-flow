"""
LLM-specific type definitions for UITestFlow.

This module contains type definitions for LLM configuration, results, and errors.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class GenerationConfig(BaseModel):
    """Configuration for test generation with LLMs.

    This class defines all the parameters that control how tests are generated
    from natural language descriptions.
    """

    model: str = Field(
        default="claude-3-5-haiku-20241022",
        description="Model to use for generation (e.g., claude-3-5-haiku-20241022, claude-3-5-sonnet-20241022)",
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Sampling temperature (0.0=deterministic, 1.0=creative)",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=200000,
        description="Maximum tokens in response",
    )
    timeout: int = Field(
        default=60,
        ge=1,
        le=300,
        description="Request timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts",
    )
    retry_delay: float = Field(
        default=1.0,
        ge=0.0,
        description="Base delay between retries in seconds",
    )
    include_examples: bool = Field(
        default=True,
        description="Include example test definitions in prompt",
    )
    suggest_evaluators: bool = Field(
        default=True,
        description="Have Claude suggest appropriate evaluators",
    )
    auto_fill_url: bool = Field(
        default=True,
        description="Automatically extract and fill base URL from description",
    )


class GenerationResult(BaseModel):
    """Result of a test generation request.

    Contains the generated test definition along with metadata about
    the generation process.
    """

    test_definition: dict[str, Any] = Field(
        ...,
        description="Generated test definition (to be converted to TestDefinition)",
    )
    model_used: str = Field(
        ...,
        description="Model used for generation",
    )
    tokens_used: int = Field(
        ...,
        description="Total tokens used (prompt + completion)",
    )
    prompt_tokens: int = Field(
        ...,
        description="Tokens in the prompt",
    )
    completion_tokens: int = Field(
        ...,
        description="Tokens in the completion",
    )
    duration_seconds: float = Field(
        ...,
        description="Time taken for generation in seconds",
    )
    retries: int = Field(
        default=0,
        description="Number of retry attempts needed",
    )
    raw_response: str | None = Field(
        default=None,
        description="Raw response from the model (for debugging)",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When generation occurred",
    )


class LLMError(Exception):
    """Base exception for LLM-related errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        """Initialize LLMError.

        Args:
            message: Error message
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}


class APIKeyError(LLMError):
    """Raised when API key is missing or invalid."""


class ModelNotFoundError(LLMError):
    """Raised when specified model doesn't exist."""


class RateLimitError(LLMError):
    """Raised when API rate limit is exceeded."""


class ParseError(LLMError):
    """Raised when response cannot be parsed into TestDefinition."""


class ValidationError(LLMError):
    """Raised when generated test fails validation."""


class GenerationTimeoutError(LLMError):
    """Raised when generation request times out."""
