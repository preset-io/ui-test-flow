"""
Claude client for test generation.

This module provides the ClaudeTestGenerator class which uses the Anthropic API
to generate test definitions from natural language descriptions.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any

from anthropic import Anthropic, APIError
from anthropic import RateLimitError as AnthropicRateLimitError
from pydantic import ValidationError as PydanticValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from uitestflow.llm.prompts import SYSTEM_PROMPT_TEST_GENERATION, get_test_generation_prompt
from uitestflow.llm.types import (
    APIKeyError,
    GenerationConfig,
    GenerationResult,
    LLMError,
    ModelNotFoundError,
    ParseError,
    RateLimitError,
    ValidationError,
)
from uitestflow.src.models import TestDefinition


logger = logging.getLogger(__name__)


class ClaudeTestGenerator:
    """Generate test definitions using Claude AI.

    This class provides methods to generate structured test definitions from
    natural language descriptions using the Anthropic Claude API.

    Example:
        ```python
        generator = ClaudeTestGenerator(api_key="sk-...")
        test_def = await generator.generate_test(
            description="Login with username 'admin' and password 'password123'"
        )
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        config: GenerationConfig | None = None,
    ) -> None:
        """Initialize Claude test generator.

        Args:
            api_key: Anthropic API key. If not provided, will read from
                    ANTHROPIC_API_KEY environment variable.
            config: Generation configuration. If not provided, uses defaults.

        Raises:
            APIKeyError: If API key is not provided and not in environment
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise APIKeyError(
                "Anthropic API key is required. Provide via api_key parameter "
                "or ANTHROPIC_API_KEY environment variable."
            )

        # Validate API key format (basic check)
        if not self.api_key.startswith("sk-ant-"):
            logger.warning("API key may be invalid - doesn't match expected format")

        self.config = config or GenerationConfig()
        self.client = Anthropic(api_key=self.api_key)

    async def generate_test(
        self,
        description: str,
        base_url: str | None = None,
        config_override: GenerationConfig | None = None,
        load_page: bool = True,
    ) -> TestDefinition:
        """Generate a test definition from natural language description.

        Args:
            description: Natural language description of the test
            base_url: Optional base URL to use in the test
            config_override: Optional config to override default settings
            load_page: If True, load the page first to extract real selectors

        Returns:
            Generated TestDefinition

        Raises:
            LLMError: If generation fails
            ParseError: If response cannot be parsed
            ValidationError: If generated test is invalid
        """
        if not description or not description.strip():
            raise ValidationError("Test description cannot be empty")

        config = config_override or self.config
        start_time = time.time()

        # Extract page context if base_url is provided and load_page is True
        page_context = None
        if base_url and load_page:
            try:
                page_context = await self._extract_page_context(base_url)
                logger.info(
                    f"Extracted page context from {base_url}: {len(page_context.get('elements', []))} elements"
                )
            except Exception as e:
                logger.warning(f"Failed to extract page context from {base_url}: {e}")
                # Continue without page context

        try:
            # Generate the test using Claude
            result = await self._call_claude_with_retry(
                description=description,
                base_url=base_url,
                config=config,
                page_context=page_context,
            )

            # Parse response into TestDefinition
            test_def = self._parse_response_to_test_definition(result.test_definition)

            # Add MCP metadata
            test_def = self._add_mcp_metadata(
                test_def=test_def,
                description=description,
                model=result.model_used,
                temperature=config.temperature,
                tokens_used=result.tokens_used,
            )

            duration = time.time() - start_time
            logger.info(
                f"Generated test '{test_def.name}' in {duration:.2f}s "
                f"using {result.tokens_used} tokens"
            )

            return test_def

        except (APIError, AnthropicRateLimitError) as e:
            duration = time.time() - start_time
            logger.error(f"Claude API error after {duration:.2f}s: {e}")
            raise LLMError(f"Claude API error: {e}", {"duration": duration}) from e

    @retry(
        retry=retry_if_exception_type((APIError, AnthropicRateLimitError)),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _call_claude_with_retry(
        self,
        description: str,
        base_url: str | None,
        config: GenerationConfig,
        page_context: dict[str, Any] | None = None,
    ) -> GenerationResult:
        """Call Claude API with automatic retries.

        Args:
            description: Test description
            base_url: Optional base URL
            config: Generation configuration
            page_context: Optional page context from browser extraction

        Returns:
            GenerationResult with test definition and metadata

        Raises:
            APIError: If API call fails
            RateLimitError: If rate limited
            TimeoutError: If request times out
        """
        try:
            # Build the prompt with page context if available
            user_prompt = get_test_generation_prompt(description, base_url, page_context)

            logger.debug(f"Calling Claude API with model: {config.model}")

            # Call Claude API (synchronous - Anthropic SDK doesn't have async yet)
            response = self.client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=SYSTEM_PROMPT_TEST_GENERATION,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt,
                    }
                ],
            )

            # Extract the response text
            response_text = ""
            if response.content:
                first_block = response.content[0]
                # Handle different content block types
                if hasattr(first_block, "text"):
                    response_text = first_block.text  # type: ignore[attr-defined]

            logger.debug(f"Claude response: {response_text[:200]}...")

            # Parse JSON from response
            test_definition_dict = self._extract_json_from_response(response_text)

            # Calculate token usage
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            return GenerationResult(
                test_definition=test_definition_dict,
                model_used=response.model,
                tokens_used=tokens_used,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                duration_seconds=0.0,  # Will be set by caller
                raw_response=response_text,
            )

        except AnthropicRateLimitError as e:
            logger.warning("Rate limit hit: %s", e)
            raise RateLimitError("Claude API rate limit exceeded", {"error": str(e)}) from e

        except APIError as e:
            if "model" in str(e).lower():
                raise ModelNotFoundError(
                    f"Model '{config.model}' not found or not accessible",
                    {"model": config.model},
                ) from e
            raise

    def _extract_json_from_response(self, response_text: str) -> dict[str, Any]:
        """Extract JSON from Claude's response.

        Claude may wrap JSON in markdown code blocks or include extra text.
        This method extracts the JSON reliably.

        Args:
            response_text: Raw response from Claude

        Returns:
            Parsed JSON as dictionary

        Raises:
            ParseError: If JSON cannot be extracted or parsed
        """
        # Remove markdown code blocks if present
        text = response_text.strip()

        # Try to find JSON within code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()

        # Try to find JSON by looking for curly braces
        if not text.startswith("{"):
            start_idx = text.find("{")
            if start_idx != -1:
                text = text[start_idx:]

        if not text.endswith("}"):
            end_idx = text.rfind("}")
            if end_idx != -1:
                text = text[: end_idx + 1]

        # Parse JSON
        try:
            result: dict[str, Any] = json.loads(text)
            return result
        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON: %s", e)
            logger.debug("Response text: %s", response_text)
            raise ParseError(
                "Failed to parse Claude response as JSON",
                {"error": str(e), "response": response_text[:500]},
            ) from e

    def _parse_response_to_test_definition(self, test_dict: dict[str, Any]) -> TestDefinition:
        """Parse dictionary to TestDefinition.

        Args:
            test_dict: Dictionary from Claude response

        Returns:
            Validated TestDefinition

        Raises:
            ValidationError: If test definition is invalid
        """
        try:
            # The test_dict should match the dataclass structure from src.models
            # We need to convert it to match the TestDefinition from src.models
            from uitestflow.src.models import (
                ActionType,
                EvaluatorConfig,
                EvaluatorType,
                RetryConfig,
                TestStep,
            )

            # Parse steps
            steps = []
            for step_dict in test_dict.get("steps", []):
                step = TestStep(
                    name=step_dict["name"],
                    action=ActionType(step_dict["action"])
                    if step_dict["action"] in ActionType.__members__.values()
                    else step_dict["action"],
                    selector=step_dict.get("selector"),
                    value=step_dict.get("value"),
                    url=step_dict.get("url"),
                    timeout=step_dict.get("timeout"),
                    screenshot=step_dict.get("screenshot", False),
                    wait_for_navigation=step_dict.get("wait_for_navigation", False),
                    condition=step_dict.get("condition"),
                    retry=RetryConfig(**step_dict["retry"]) if step_dict.get("retry") else None,
                    metadata=step_dict.get("metadata", {}),
                )
                steps.append(step)

            # Parse evaluators
            evaluators = []
            for eval_dict in test_dict.get("evaluators", []):
                evaluator = EvaluatorConfig(
                    name=eval_dict["name"],
                    type=EvaluatorType(eval_dict["evaluator_type"])
                    if eval_dict["evaluator_type"] in EvaluatorType.__members__.values()
                    else eval_dict["evaluator_type"],
                    selector=eval_dict.get("params", {}).get("selector"),
                    expected_value=eval_dict.get("params", {}).get("pattern")
                    or eval_dict.get("params", {}).get("text"),
                    max_errors=eval_dict.get("params", {}).get("max_errors"),
                    max_warnings=eval_dict.get("params", {}).get("max_warnings"),
                    max_load_time=eval_dict.get("params", {}).get("max_ms"),
                )
                evaluators.append(evaluator)

            # Create TestDefinition
            test_def = TestDefinition(
                name=test_dict["name"],
                version=test_dict.get("version", "1.0"),
                description=test_dict.get("description"),
                url=test_dict.get("url"),
                steps=steps,
                evaluators=evaluators,
                timeout=test_dict.get("timeout", 30000),
                tags=test_dict.get("tags", []),
            )

            return test_def

        except (KeyError, ValueError, PydanticValidationError) as e:
            logger.error("Failed to validate test definition: %s", e)
            raise ValidationError(
                "Generated test definition is invalid",
                {"error": str(e), "test_dict": test_dict},
            ) from e

    def _add_mcp_metadata(
        self,
        test_def: TestDefinition,
        description: str,
        model: str,
        temperature: float,
        tokens_used: int,
    ) -> TestDefinition:
        """Add MCP metadata to test definition.

        Args:
            test_def: Test definition to enhance
            description: Original description
            model: Model used for generation
            temperature: Temperature used
            tokens_used: Tokens consumed

        Returns:
            Test definition with MCP metadata
        """
        # For now, we'll add this as metadata since we haven't modified core/models.py yet
        # This will be stored in the test definition's metadata field
        mcp_metadata = {
            "generated_by": "claude",
            "generation_model": model,
            "generation_timestamp": datetime.utcnow().isoformat(),
            "generation_prompt": description,
            "generation_temperature": temperature,
            "tokens_used": tokens_used,
        }

        # Add to the first step's metadata as a temporary solution
        if test_def.steps:
            test_def.steps[0].metadata["mcp_metadata"] = mcp_metadata

        return test_def

    def validate_api_key(self) -> bool:
        """Validate that the API key works.

        Returns:
            True if API key is valid, False otherwise
        """
        try:
            # Make a minimal API call to validate the key
            response = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return response is not None
        except APIError:
            return False

    async def _extract_page_context(self, url: str) -> dict[str, Any]:
        """Extract page context by loading the URL with Playwright.

        Args:
            url: URL to load and extract context from

        Returns:
            Dictionary containing page title, URL, and interactive elements
        """
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                # Navigate to the page
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for dynamic content

                # Extract page info
                title = await page.title()
                current_url = page.url

                # Extract interactive elements with their selectors
                elements = await page.evaluate(
                    """
                    () => {
                        const elements = [];
                        const maxElements = 50;  // Limit to avoid huge context

                        // Helper to get best selector for an element
                        function getBestSelector(el) {
                            if (el.id) return '#' + el.id;
                            if (el.name) return `[name="${el.name}"]`;
                            if (el.getAttribute('data-testid')) return `[data-testid="${el.getAttribute('data-testid')}"]`;
                            if (el.getAttribute('aria-label')) return `[aria-label="${el.getAttribute('aria-label')}"]`;
                            if (el.className && typeof el.className === 'string') {
                                const classes = el.className.trim().split(/\\s+/).slice(0, 2).join('.');
                                if (classes) return el.tagName.toLowerCase() + '.' + classes;
                            }
                            return el.tagName.toLowerCase();
                        }

                        // Get buttons
                        document.querySelectorAll('button, [role="button"], input[type="submit"], input[type="button"]').forEach(el => {
                            if (elements.length < maxElements) {
                                elements.push({
                                    type: 'button',
                                    selector: getBestSelector(el),
                                    text: (el.textContent || el.value || '').trim().substring(0, 50),
                                    visible: el.offsetParent !== null
                                });
                            }
                        });

                        // Get input fields
                        document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]), textarea').forEach(el => {
                            if (elements.length < maxElements) {
                                elements.push({
                                    type: 'input',
                                    inputType: el.type || 'text',
                                    selector: getBestSelector(el),
                                    placeholder: el.placeholder || '',
                                    name: el.name || '',
                                    visible: el.offsetParent !== null
                                });
                            }
                        });

                        // Get links
                        document.querySelectorAll('a[href]').forEach(el => {
                            if (elements.length < maxElements && el.href && !el.href.startsWith('javascript:')) {
                                elements.push({
                                    type: 'link',
                                    selector: getBestSelector(el),
                                    text: (el.textContent || '').trim().substring(0, 50),
                                    href: el.href,
                                    visible: el.offsetParent !== null
                                });
                            }
                        });

                        // Get select dropdowns
                        document.querySelectorAll('select').forEach(el => {
                            if (elements.length < maxElements) {
                                const options = Array.from(el.options).map(o => o.text).slice(0, 5);
                                elements.push({
                                    type: 'select',
                                    selector: getBestSelector(el),
                                    name: el.name || '',
                                    options: options,
                                    visible: el.offsetParent !== null
                                });
                            }
                        });

                        // Get forms
                        document.querySelectorAll('form').forEach(el => {
                            if (elements.length < maxElements) {
                                elements.push({
                                    type: 'form',
                                    selector: getBestSelector(el),
                                    action: el.action || '',
                                    method: el.method || 'get'
                                });
                            }
                        });

                        return elements.filter(e => e.visible !== false);
                    }
                """
                )

                return {
                    "title": title,
                    "url": current_url,
                    "elements": elements,
                }

            finally:
                await browser.close()

    def list_available_models(self) -> list[str]:
        """List available Claude models.

        Returns:
            List of model IDs that can be used for generation
        """
        # Anthropic doesn't have a models list endpoint yet
        # Return the known models
        return [
            "claude-3-5-haiku-20241022",
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
        ]
