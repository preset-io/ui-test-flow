"""AI-powered profile generator using Claude or other LLMs."""

import json
import logging
import os
from typing import Any


logger = logging.getLogger(__name__)


class AIProfileGeneratorError(Exception):
    """Exception raised for AI profile generation errors."""


class AIProfileGenerator:
    """
    Generates UITestFlow profiles from natural language descriptions.

    Supports multiple AI providers (Anthropic Claude, OpenAI, etc.)
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        api_key_env: str = "ANTHROPIC_API_KEY",
    ):
        """
        Initialize AI profile generator.

        Args:
            provider: AI provider (anthropic, openai, etc.)
            model: Model to use (default depends on provider)
            api_key_env: Environment variable name for API key
        """
        self.provider = provider.lower()
        self.api_key_env = api_key_env

        # Set default models per provider
        if model is None:
            if self.provider == "anthropic":
                model = "claude-sonnet-4-5-20250929"
            elif self.provider == "openai":
                model = "gpt-4-turbo-preview"
            else:
                model = "default"

        self.model = model

        # Get API key from environment
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            logger.warning(f"API key not found in environment variable: {api_key_env}")

    async def generate_profiles(self, description: str) -> dict[str, Any]:
        """
        Generate profile configurations from natural language description.

        Args:
            description: Natural language description of the profile(s) to create

        Returns:
            Dictionary with:
            - profiles: List of generated profile configurations
            - reasoning: AI's reasoning about the profiles
            - success: Whether generation succeeded
            - message: Status or error message
        """
        if not self.api_key:
            return {
                "success": False,
                "profiles": [],
                "reasoning": None,
                "message": f"API key not found. Please set {self.api_key_env} environment variable.",
            }

        try:
            if self.provider == "anthropic":
                return await self._generate_with_anthropic(description)
            elif self.provider == "openai":
                return await self._generate_with_openai(description)
            else:
                return {
                    "success": False,
                    "profiles": [],
                    "reasoning": None,
                    "message": f"Unsupported provider: {self.provider}",
                }
        except Exception as e:
            logger.error(f"AI profile generation failed: {e}", exc_info=True)
            return {
                "success": False,
                "profiles": [],
                "reasoning": None,
                "message": f"Generation failed: {e!s}",
            }

    async def _generate_with_anthropic(self, description: str) -> dict[str, Any]:
        """Generate profiles using Anthropic Claude."""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            return {
                "success": False,
                "profiles": [],
                "reasoning": None,
                "message": "anthropic package not installed. Run: pip install anthropic",
            }

        client = AsyncAnthropic(api_key=self.api_key)

        system_prompt = """You are an expert at creating UITestFlow profile configurations.

Given a natural language description, generate one or more profile configurations in JSON format.

Each profile should include:
- id: A unique kebab-case identifier
- name: A clear, descriptive name
- description: What this profile does
- profile_type: "environment", "workflow", or "custom"
- execution_mode: "automated", "manual", or "hybrid"
- base_url: The URL to test
- init_steps: Array of initialization steps (for authentication, navigation, etc.)
- auth_config: Authentication configuration
- browser_config: Browser settings
- tags: Relevant tags for organization

Init step actions can be:
- goto: Navigate to URL (requires: url)
- click: Click an element (requires: selector)
- fill: Fill a form field (requires: selector, value)
- wait_for: Wait for element to appear (requires: selector)
- wait: Pause for duration (requires: timeout in ms)

Each init step can have:
- name: Step description
- action: Action type
- selector: CSS selector (for click, fill, wait_for)
- url: URL (for goto)
- value: Value to enter (for fill)
- timeout: Timeout in milliseconds
- critical: Boolean - if true, failure aborts initialization
- screenshot: Boolean - capture screenshot after step
- wait_after: Wait duration after step in ms

Example profile structure:
{
  "id": "example-local",
  "name": "Example Local Environment",
  "description": "Local development environment",
  "profile_type": "environment",
  "execution_mode": "automated",
  "base_url": "http://localhost:3000",
  "init_steps": [
    {
      "name": "Navigate to login",
      "action": "goto",
      "url": "http://localhost:3000/login",
      "critical": true
    },
    {
      "name": "Enter username",
      "action": "fill",
      "selector": "#username",
      "value": "admin",
      "critical": true
    }
  ],
  "auth_config": {"type": "form"},
  "browser_config": {
    "browser_type": "chromium",
    "framework": "playwright",
    "headless": true,
    "viewport": {"width": 1920, "height": 1080}
  },
  "tags": ["local", "development"]
}

Return ONLY a JSON object with this structure:
{
  "reasoning": "Brief explanation of your choices",
  "profiles": [array of profile objects]
}

Do not include markdown code blocks or any other text outside the JSON."""

        user_prompt = f"""Generate UITestFlow profile configuration(s) for:

{description}

Remember to return ONLY the JSON object with "reasoning" and "profiles" fields."""

        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract text from response
            content = response.content[0].text if response.content else ""

            # Try to parse JSON
            # Remove markdown code blocks if present
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            result = json.loads(content)

            return {
                "success": True,
                "profiles": result.get("profiles", []),
                "reasoning": result.get("reasoning", ""),
                "message": f"Successfully generated {len(result.get('profiles', []))} profile(s)",
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.error(f"Response content: {content}")
            return {
                "success": False,
                "profiles": [],
                "reasoning": None,
                "message": f"Failed to parse AI response: {e!s}",
            }

    async def _generate_with_openai(self, description: str) -> dict[str, Any]:
        """Generate profiles using OpenAI."""
        return {
            "success": False,
            "profiles": [],
            "reasoning": None,
            "message": "OpenAI provider not yet implemented. Use 'anthropic' provider.",
        }
