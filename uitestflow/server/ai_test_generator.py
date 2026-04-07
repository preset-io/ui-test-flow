"""
AI-powered test generator for creating tests from initialized environment profiles.

Supports multiple coverage levels:
- Smoke: Critical paths only (5-10 tests) - Quick validation of core functionality
- Canary: Core features (15-25 tests) - Pre-deployment validation
- Medium: Standard coverage (30-50 tests) - Comprehensive feature testing
- Deep: Full coverage (50+ tests) - Edge cases and integration scenarios
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any

from playwright.async_api import Page


logger = logging.getLogger(__name__)


class CoverageLevel(str, Enum):
    """Test coverage levels based on industry best practices."""

    SMOKE = "smoke"  # Critical paths - 5-10 tests
    CANARY = "canary"  # Core features - 15-25 tests
    MEDIUM = "medium"  # Standard coverage - 30-50 tests
    DEEP = "deep"  # Full coverage - 50+ tests


class SiteCrawler:
    """
    Crawls an initialized environment to discover UI elements, pages, and workflows.

    Uses the active browser session from a profile to explore the application
    and gather context for AI-powered test generation.
    """

    def __init__(self, page: Page, max_depth: int = 3):
        """
        Initialize site crawler.

        Args:
            page: Active Playwright page from profile session
            max_depth: Maximum crawl depth for link following
        """
        self.page = page
        self.max_depth = max_depth
        self.visited_urls: set[str] = set()
        self.discovered_pages: list[dict] = []

    async def crawl(self) -> dict[str, Any]:
        """
        Crawl the site starting from current page.

        Returns:
            Dictionary containing discovered pages, elements, and workflows
        """
        logger.info("Starting site crawl from %s", self.page.url)

        # Get current page structure
        current_page = await self._analyze_page()
        self.discovered_pages.append(current_page)
        self.visited_urls.add(self.page.url)

        # Discover navigable links (limited depth)
        if self.max_depth > 0:
            await self._discover_links(depth=1)

        return {
            "base_url": self.page.url,
            "pages_discovered": len(self.discovered_pages),
            "pages": self.discovered_pages,
            "summary": self._generate_summary(),
        }

    async def _analyze_page(self) -> dict[str, Any]:
        """Analyze current page structure and elements."""
        try:
            # Get page metadata
            title = await self.page.title()
            url = self.page.url

            # Discover interactive elements
            elements = await self.page.evaluate(
                """() => {
                return {
                    forms: Array.from(document.forms).map(form => ({
                        id: form.id,
                        name: form.name,
                        action: form.action,
                        method: form.method,
                        inputs: Array.from(form.elements).map(el => ({
                            type: el.type,
                            name: el.name,
                            id: el.id,
                            placeholder: el.placeholder,
                            required: el.required
                        }))
                    })),
                    buttons: Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]')).map(btn => ({
                        text: btn.textContent?.trim() || btn.value,
                        type: btn.type,
                        id: btn.id,
                        name: btn.name,
                        className: btn.className
                    })).slice(0, 50),
                    links: Array.from(document.querySelectorAll('a[href]')).map(link => ({
                        text: link.textContent?.trim(),
                        href: link.href,
                        id: link.id,
                        className: link.className
                    })).slice(0, 100),
                    headings: Array.from(document.querySelectorAll('h1, h2, h3')).map(h => ({
                        level: h.tagName,
                        text: h.textContent?.trim()
                    })),
                    inputs: Array.from(document.querySelectorAll('input:not([type="hidden"]), textarea, select')).map(input => ({
                        type: input.type || input.tagName.toLowerCase(),
                        name: input.name,
                        id: input.id,
                        placeholder: input.placeholder,
                        required: input.required
                    })).slice(0, 50),
                    tables: Array.from(document.querySelectorAll('table')).map(table => ({
                        id: table.id,
                        className: table.className,
                        rowCount: table.rows.length,
                        columnCount: table.rows[0]?.cells.length || 0
                    })),
                    modals: Array.from(document.querySelectorAll('[role="dialog"], .modal, [class*="modal"]')).map(modal => ({
                        id: modal.id,
                        className: modal.className,
                        visible: modal.offsetParent !== null
                    }))
                }
            }"""
            )

            # Get console errors
            console_errors = []
            self.page.on(
                "console",
                lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
            )

            return {
                "url": url,
                "title": title,
                "timestamp": datetime.utcnow().isoformat(),
                "elements": elements,
                "metrics": {
                    "forms": len(elements.get("forms", [])),
                    "buttons": len(elements.get("buttons", [])),
                    "links": len(elements.get("links", [])),
                    "inputs": len(elements.get("inputs", [])),
                    "tables": len(elements.get("tables", [])),
                },
            }

        except Exception as e:
            logger.error("Error analyzing page: %s", e)
            return {"url": self.page.url, "error": str(e)}

    async def _discover_links(self, depth: int):
        """Discover and optionally follow links to build site map."""
        if depth > self.max_depth:
            return

        try:
            # Get all navigation links
            links = await self.page.evaluate(
                """() => {
                const navLinks = Array.from(document.querySelectorAll('nav a[href], [role="navigation"] a[href]'));
                return navLinks.map(link => link.href).filter(href =>
                    href && !href.startsWith('javascript:') && !href.startsWith('#') && !href.startsWith('mailto:')
                ).slice(0, 20);
            }"""
            )

            for link in links:
                if link not in self.visited_urls and len(self.discovered_pages) < 10:
                    # Note: In production, you might want to actually navigate
                    # For now, just record the discovered links
                    self.discovered_pages.append({
                        "url": link,
                        "title": "Discovered link",
                        "depth": depth,
                        "analyzed": False,
                    })
                    self.visited_urls.add(link)

        except Exception as e:
            logger.error("Error discovering links: %s", e)

    def _generate_summary(self) -> dict[str, Any]:
        """Generate summary of crawled site."""
        total_forms = sum(page.get("metrics", {}).get("forms", 0) for page in self.discovered_pages)
        total_buttons = sum(
            page.get("metrics", {}).get("buttons", 0) for page in self.discovered_pages
        )
        total_inputs = sum(
            page.get("metrics", {}).get("inputs", 0) for page in self.discovered_pages
        )

        return {
            "total_pages": len(self.discovered_pages),
            "total_forms": total_forms,
            "total_buttons": total_buttons,
            "total_inputs": total_inputs,
            "crawl_depth": self.max_depth,
        }


class AITestGenerator:
    """
    Generates comprehensive UI tests from environment profiles using AI.

    Uses Anthropic Claude to analyze crawled site data and generate
    test definitions based on coverage level and best practices.
    """

    def __init__(
        self,
        provider: str = "anthropic",
        model: str | None = None,
        api_key_env: str = "ANTHROPIC_API_KEY",
    ):
        """
        Initialize AI test generator.

        Args:
            provider: AI provider (anthropic, openai, etc.)
            model: Model to use
            api_key_env: Environment variable for API key
        """
        self.provider = provider.lower()
        self.api_key_env = api_key_env
        self.model = model or "claude-sonnet-4-5-20250929"
        self.api_key = os.getenv(api_key_env)

    async def generate_tests(
        self,
        site_data: dict[str, Any],
        coverage_level: CoverageLevel,
        profile_info: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate tests based on site crawl data and coverage level.

        Args:
            site_data: Crawled site structure and elements
            coverage_level: Desired test coverage level
            profile_info: Profile metadata for context

        Returns:
            Dictionary with generated tests and metadata
        """
        if not self.api_key:
            return {
                "success": False,
                "tests": [],
                "message": f"API key not found. Set {self.api_key_env} environment variable.",
            }

        try:
            if self.provider == "anthropic":
                return await self._generate_with_anthropic(site_data, coverage_level, profile_info)
            else:
                return {
                    "success": False,
                    "tests": [],
                    "message": f"Provider {self.provider} not yet supported",
                }

        except Exception as e:
            logger.error("Error generating tests: %s", e, exc_info=True)
            return {"success": False, "tests": [], "message": f"Test generation failed: {e}"}

    async def _generate_with_anthropic(
        self, site_data: dict[str, Any], coverage_level: CoverageLevel, profile_info: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate tests using Anthropic Claude."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        # Build coverage-specific prompt
        coverage_guidance = self._get_coverage_guidance(coverage_level)

        prompt = f"""You are an expert QA engineer creating comprehensive UI tests for a web application.

**Environment Profile:**
- Name: {profile_info.get('name', 'Unknown')}
- Base URL: {profile_info.get('base_url', 'Unknown')}
- Type: {profile_info.get('profile_type', 'Unknown')}

**Site Analysis:**
{json.dumps(site_data.get('summary', {}), indent=2)}

**Discovered Pages:**
{self._format_pages_for_prompt(site_data.get('pages', [])[:3])}

**Coverage Level: {coverage_level.value.upper()}**
{coverage_guidance}

Generate a comprehensive test suite as a JSON array. Each test should follow this structure:

```json
{{
  "name": "Test name describing what is being tested",
  "description": "Detailed description of test purpose and expected behavior",
  "tags": ["smoke|canary|regression|integration", "feature-area"],
  "priority": "critical|high|medium|low",
  "steps": [
    {{
      "name": "Step description",
      "action": "goto|click|fill|wait_for|wait|assert",
      "selector": "CSS selector if applicable",
      "value": "Value for fill actions",
      "timeout": 30000,
      "screenshot": true,
      "assertion": "Expected outcome if assert action"
    }}
  ],
  "evaluators": [
    {{
      "name": "No console errors",
      "type": "console_errors",
      "max_errors": 0
    }},
    {{
      "name": "Page load performance",
      "type": "performance",
      "max_load_time": 3000
    }}
  ]
}}
```

**Requirements:**
1. Tests must be realistic and executable on the discovered site structure
2. Include proper selectors based on discovered elements
3. Follow testing best practices for {coverage_level.value} coverage
4. Include appropriate assertions and evaluators
5. Ensure tests are maintainable and well-documented

Generate the tests now as a valid JSON array:"""

        try:
            message = await client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text

            # Extract JSON from response
            json_start = response_text.find("[")
            json_end = response_text.rfind("]") + 1

            if json_start >= 0 and json_end > json_start:
                tests_json = response_text[json_start:json_end]
                tests = json.loads(tests_json)

                return {
                    "success": True,
                    "tests": tests,
                    "count": len(tests),
                    "coverage_level": coverage_level.value,
                    "message": f"Generated {len(tests)} tests for {coverage_level.value} coverage",
                    "reasoning": response_text[:json_start].strip() if json_start > 0 else "",
                }
            else:
                return {
                    "success": False,
                    "tests": [],
                    "message": "Failed to parse test JSON from AI response",
                    "raw_response": response_text,
                }

        except Exception as e:
            logger.error("Anthropic API error: %s", e, exc_info=True)
            return {"success": False, "tests": [], "message": f"API error: {e}"}

    def _get_coverage_guidance(self, level: CoverageLevel) -> str:
        """Get coverage-specific guidance for AI."""
        guidance = {
            CoverageLevel.SMOKE: """
**SMOKE Testing (5-10 tests):**
- Focus ONLY on critical paths that must work for the app to be usable
- Authentication flow (if applicable)
- Primary user journey (most common use case)
- Basic CRUD operations on main entities
- Application launches and loads successfully
- Critical error states don't appear
Goal: Quick validation (< 5 minutes) that nothing is catastrophically broken
""",
            CoverageLevel.CANARY: """
**CANARY Testing (15-25 tests):**
- All smoke tests PLUS:
- Core feature validation across major modules
- Key integration points between features
- Common user workflows and happy paths
- Basic error handling for critical operations
- Main navigation flows work correctly
Goal: Pre-deployment confidence (10-15 minutes) that core functionality is intact
""",
            CoverageLevel.MEDIUM: """
**MEDIUM Coverage (30-50 tests):**
- All canary tests PLUS:
- Comprehensive feature coverage for each major module
- Negative test cases and error handling
- Edge cases for critical workflows
- Data validation and form submission scenarios
- Permission and access control checks
- Cross-browser/device compatibility cases
Goal: Standard regression suite (30-45 minutes) ensuring features work as designed
""",
            CoverageLevel.DEEP: """
**DEEP Coverage (50+ tests):**
- All medium tests PLUS:
- Exhaustive edge cases and boundary conditions
- Complex integration scenarios
- Performance and load scenarios
- Accessibility compliance checks
- Security vulnerability tests
- Data integrity and consistency checks
- Stress tests and error recovery
- Internationalization and localization
Goal: Comprehensive validation (1-2 hours) covering all scenarios including rare edge cases
""",
        }
        return guidance.get(level, "")

    def _format_pages_for_prompt(self, pages: list[dict]) -> str:
        """Format discovered pages for AI prompt."""
        formatted = []
        for i, page in enumerate(pages, 1):
            if page.get("error"):
                continue
            formatted.append(
                f"""
Page {i}: {page.get('title', 'Unknown')}
URL: {page.get('url', 'Unknown')}
Elements:
  - Forms: {page.get('metrics', {}).get('forms', 0)}
  - Buttons: {page.get('metrics', {}).get('buttons', 0)}
  - Inputs: {page.get('metrics', {}).get('inputs', 0)}
  - Links: {page.get('metrics', {}).get('links', 0)}
"""
            )
        return "\n".join(formatted) if formatted else "No pages analyzed yet"
