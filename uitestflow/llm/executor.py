"""
Claude executor for guided test execution.

This module provides the ClaudeExecutor class which manages Claude conversation
during test execution for step guidance, selector adaptation, and error recovery.
"""

import json
import logging
import time
from typing import Any

from anthropic import Anthropic, APIError
from anthropic import RateLimitError as AnthropicRateLimitError

from uitestflow.src.models import TestStep


logger = logging.getLogger(__name__)


class ClaudeExecutor:
    """
    Manages Claude conversation during test execution.

    Provides intelligent guidance for test steps, adaptive selector resolution,
    and error recovery during test execution.

    Example:
        ```python
        executor = ClaudeExecutor(api_key="sk-...")
        guidance = await executor.get_step_guidance(step, page_state)
        alternatives = await executor.suggest_selector_alternatives(selector, page_state)
        ```
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-20241022",
        temperature: float = 0.3,
        timeout: float = 10.0,
    ):
        """
        Initialize Claude executor.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            temperature: Sampling temperature (0.0-1.0)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.client = Anthropic(api_key=api_key)
        self.conversation_history: list[dict[str, str]] = []
        self.guidance_count = 0

    async def get_step_guidance(
        self,
        step: TestStep,
        page_state: dict[str, Any],
        step_index: int,
    ) -> dict[str, Any]:
        """
        Get guidance from Claude before executing a step.

        Analyzes the step and page state to provide intelligent guidance
        including selector validation, next step suggestions, and warnings.

        Args:
            step: Test step to execute
            page_state: Current page state
            step_index: Index of the step

        Returns:
            Dictionary with guidance information:
            - guidance: Text guidance for the step
            - selector_valid: Whether selector is likely valid
            - warnings: List of potential issues
            - suggestions: List of suggestions

        Raises:
            LLMError: If Claude API call fails
        """
        start_time = time.time()

        try:
            prompt = self._build_step_guidance_prompt(step, page_state, step_index)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=self.temperature,
                system=self._get_system_prompt(),
                messages=self.conversation_history
                + [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract response
            response_text = ""
            if response.content:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    response_text = first_block.text

            # Parse structured response
            guidance_data = self._parse_guidance_response(response_text)

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response_text})

            # Keep conversation history manageable (last 10 exchanges)
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            self.guidance_count += 1
            duration = time.time() - start_time

            logger.info(
                f"Step guidance received in {duration:.2f}s " f"(step {step_index}: {step.name})"
            )

            return guidance_data

        except (APIError, AnthropicRateLimitError) as e:
            logger.error("Claude API error during step guidance: %s", e)
            # Return fallback guidance
            return {
                "guidance": "Unable to get Claude guidance, proceeding with step",
                "selector_valid": True,
                "warnings": [],
                "suggestions": [],
                "error": str(e),
            }

    async def validate_step_result(
        self,
        step: TestStep,
        result: dict[str, Any],
        page_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate step result after execution.

        Analyzes the step result and page state to determine if the step
        completed successfully and if expected outcomes occurred.

        Args:
            step: Test step that was executed
            result: Step execution result
            page_state: Page state after step execution

        Returns:
            Dictionary with validation information:
            - validated: Whether step result is valid
            - unexpected_changes: List of unexpected changes
            - suggestions: Suggestions for next steps

        Raises:
            LLMError: If Claude API call fails
        """
        start_time = time.time()

        try:
            prompt = self._build_validation_prompt(step, result, page_state)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=self.temperature,
                system=self._get_system_prompt(),
                messages=self.conversation_history
                + [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract response
            response_text = ""
            if response.content:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    response_text = first_block.text

            # Parse validation response
            validation_data = self._parse_validation_response(response_text)

            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response_text})

            duration = time.time() - start_time
            logger.info(f"Step validation received in {duration:.2f}s")

            return validation_data

        except (APIError, AnthropicRateLimitError) as e:
            logger.error("Claude API error during validation: %s", e)
            return {
                "validated": result.get("success", False),
                "unexpected_changes": [],
                "suggestions": [],
                "error": str(e),
            }

    async def suggest_selector_alternatives(
        self,
        selector: str,
        page_state: dict[str, Any],
        error: str | None = None,
    ) -> list[str]:
        """
        Suggest alternative selectors if original fails.

        Analyzes the page state and failed selector to suggest alternatives
        that are more likely to work.

        Args:
            selector: Original selector that failed
            page_state: Current page state
            error: Error message from failed selector

        Returns:
            List of alternative selectors to try (in priority order)

        Raises:
            LLMError: If Claude API call fails
        """
        start_time = time.time()

        try:
            prompt = self._build_selector_alternatives_prompt(selector, page_state, error)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=self.temperature,
                system=self._get_system_prompt(),
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract response
            response_text = ""
            if response.content:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    response_text = first_block.text

            # Parse alternatives
            alternatives = self._parse_selector_alternatives(response_text)

            duration = time.time() - start_time
            logger.info(
                f"Selector alternatives received in {duration:.2f}s: "
                f"{len(alternatives)} suggestions"
            )

            return alternatives

        except (APIError, AnthropicRateLimitError) as e:
            logger.error("Claude API error getting selector alternatives: %s", e)
            # Return some fallback alternatives
            return self._generate_fallback_alternatives(selector)

    async def suggest_error_recovery(
        self,
        step: TestStep,
        error: str,
        page_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Suggest recovery action for a failed step.

        Analyzes the error and page state to suggest recovery actions
        that might allow the test to continue.

        Args:
            step: Test step that failed
            error: Error message
            page_state: Current page state

        Returns:
            Dictionary with recovery information:
            - recoverable: Whether error is recoverable
            - recovery_action: Suggested recovery action
            - explanation: Explanation of the recovery

        Raises:
            LLMError: If Claude API call fails
        """
        start_time = time.time()

        try:
            prompt = self._build_error_recovery_prompt(step, error, page_state)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=512,
                temperature=self.temperature,
                system=self._get_system_prompt(),
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            # Extract response
            response_text = ""
            if response.content:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    response_text = first_block.text

            # Parse recovery suggestion
            recovery_data = self._parse_error_recovery(response_text)

            duration = time.time() - start_time
            logger.info(f"Error recovery suggestion received in {duration:.2f}s")

            return recovery_data

        except (APIError, AnthropicRateLimitError) as e:
            logger.error("Claude API error during error recovery: %s", e)
            return {
                "recoverable": False,
                "recovery_action": None,
                "explanation": "Unable to get recovery suggestion",
                "error": str(e),
            }

    def _get_system_prompt(self) -> str:
        """Get the system prompt for Claude executor."""
        return """You are an expert test automation assistant helping to execute web UI tests.
Your role is to:
1. Analyze test steps and page state to provide guidance
2. Suggest alternative selectors when elements are not found
3. Validate step results and detect unexpected changes
4. Suggest recovery actions for failed steps

Provide concise, actionable guidance. When suggesting selectors, prefer:
- data-testid attributes
- semantic selectors (role, aria-label)
- stable id attributes
- CSS classes (with caution)

Format responses as JSON when structure is requested."""

    def _build_step_guidance_prompt(
        self,
        step: TestStep,
        page_state: dict[str, Any],
        step_index: int,
    ) -> str:
        """Build prompt for step guidance."""
        return f"""Analyze this test step and provide guidance:

**Step {step_index}: {step.name}**
- Action: {step.action}
- Selector: {step.selector or 'N/A'}
- Value: {step.value or 'N/A'}

**Current Page State:**
- URL: {page_state.get('url')}
- Title: {page_state.get('title')}
- Console errors: {len(page_state.get('console_errors', []))}
- DOM summary: {page_state.get('dom_summary', {})}

Respond with JSON:
{{
    "guidance": "brief guidance for this step",
    "selector_valid": true/false,
    "warnings": ["warning1", "warning2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

    def _build_validation_prompt(
        self,
        step: TestStep,
        result: dict[str, Any],
        page_state: dict[str, Any],
    ) -> str:
        """Build prompt for step validation."""
        return f"""Validate the result of this test step:

**Step: {step.name}**
- Action: {step.action}
- Success: {result.get('success')}
- Error: {result.get('error_message') or 'None'}

**Page State After:**
- URL: {page_state.get('url')}
- Title: {page_state.get('title')}
- Console errors: {len(page_state.get('console_errors', []))}

Respond with JSON:
{{
    "validated": true/false,
    "unexpected_changes": ["change1"],
    "suggestions": ["next step suggestion"]
}}"""

    def _build_selector_alternatives_prompt(
        self,
        selector: str,
        page_state: dict[str, Any],
        error: str | None,
    ) -> str:
        """Build prompt for selector alternatives."""
        return f"""The selector "{selector}" failed to find an element.

**Error:** {error or 'Element not found'}

**Page State:**
- URL: {page_state.get('url')}
- Title: {page_state.get('title')}
- DOM summary: {page_state.get('dom_summary', {})}

Suggest 3-5 alternative selectors that might work better.
Respond with JSON array:
["selector1", "selector2", "selector3"]"""

    def _build_error_recovery_prompt(
        self,
        step: TestStep,
        error: str,
        page_state: dict[str, Any],
    ) -> str:
        """Build prompt for error recovery."""
        return f"""A test step failed with an error. Suggest a recovery action.

**Failed Step: {step.name}**
- Action: {step.action}
- Selector: {step.selector or 'N/A'}
- Error: {error}

**Page State:**
- URL: {page_state.get('url')}
- Console errors: {len(page_state.get('console_errors', []))}

Respond with JSON:
{{
    "recoverable": true/false,
    "recovery_action": "description of recovery action",
    "explanation": "why this might work"
}}"""

    def _parse_guidance_response(self, response: str) -> dict[str, Any]:
        """Parse guidance response from Claude."""
        try:
            # Try to extract JSON
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                return {
                    "guidance": data.get("guidance", ""),
                    "selector_valid": data.get("selector_valid", True),
                    "warnings": data.get("warnings", []),
                    "suggestions": data.get("suggestions", []),
                }
        except json.JSONDecodeError:
            pass

        # Fallback to text response
        return {
            "guidance": response,
            "selector_valid": True,
            "warnings": [],
            "suggestions": [],
        }

    def _parse_validation_response(self, response: str) -> dict[str, Any]:
        """Parse validation response from Claude."""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                return {
                    "validated": data.get("validated", True),
                    "unexpected_changes": data.get("unexpected_changes", []),
                    "suggestions": data.get("suggestions", []),
                }
        except json.JSONDecodeError:
            pass

        return {
            "validated": True,
            "unexpected_changes": [],
            "suggestions": [],
        }

    def _parse_selector_alternatives(self, response: str) -> list[str]:
        """Parse selector alternatives from Claude."""
        try:
            # Try to find JSON array
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                alternatives = json.loads(response[json_start:json_end])
                if isinstance(alternatives, list):
                    return [str(alt) for alt in alternatives if alt]
        except json.JSONDecodeError:
            pass

        # Fallback: try to extract selectors from text
        lines = response.split("\n")
        selectors = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith(".") or line.startswith("#") or line.startswith("[")):
                selectors.append(line.strip("'\""))

        return selectors[:5]  # Max 5 alternatives

    def _parse_error_recovery(self, response: str) -> dict[str, Any]:
        """Parse error recovery suggestion from Claude."""
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                data = json.loads(response[json_start:json_end])
                return {
                    "recoverable": data.get("recoverable", False),
                    "recovery_action": data.get("recovery_action"),
                    "explanation": data.get("explanation", ""),
                }
        except json.JSONDecodeError:
            pass

        return {
            "recoverable": False,
            "recovery_action": None,
            "explanation": response or "No recovery suggestion",
        }

    def _generate_fallback_alternatives(self, selector: str) -> list[str]:
        """Generate fallback selector alternatives."""
        alternatives = []

        # If it's a class selector, try variations
        if selector.startswith("."):
            class_name = selector[1:]
            alternatives.extend([
                f"[class*='{class_name}']",
                f"[class^='{class_name}']",
                f"[class$='{class_name}']",
            ])

        # If it's an ID selector, try variations
        elif selector.startswith("#"):
            id_name = selector[1:]
            alternatives.extend([
                f"[id='{id_name}']",
                f"[id*='{id_name}']",
            ])

        # Try common alternatives
        alternatives.extend([
            f"{selector}:visible",
            f"{selector}:first",
        ])

        return alternatives[:5]

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []
        self.guidance_count = 0
        logger.info("Conversation history reset")
