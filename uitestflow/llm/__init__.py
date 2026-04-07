"""
LLM integration for UITestFlow.

This module provides integration with Large Language Models (LLMs) like Claude
for natural language test generation and execution guidance.

Key components:
- ClaudeTestGenerator: Generates test definitions from natural language descriptions
- Prompt templates: Structured prompts for test generation
- LLM types: Type definitions for LLM configurations and results
"""

from uitestflow.llm.claude_client import ClaudeTestGenerator
from uitestflow.llm.types import (
    GenerationConfig,
    GenerationResult,
    GenerationTimeoutError,
    LLMError,
)


__all__ = [
    "ClaudeTestGenerator",
    "GenerationConfig",
    "GenerationResult",
    "GenerationTimeoutError",
    "LLMError",
]
