"""
Prompt templates for LLM test generation.

This module contains all the prompt templates used for generating test definitions
from natural language descriptions using Claude or other LLMs.
"""

from typing import Any


# System prompt for test generation
SYSTEM_PROMPT_TEST_GENERATION = """You are an expert UI test engineer specializing in creating automated browser tests using Playwright.

Your task is to convert natural language test descriptions into structured test definitions in JSON format.

## Test Definition Schema

A test definition has the following structure:

```json
{
  "name": "test_name",
  "description": "Brief description of what the test does",
  "version": "1.0",
  "url": "https://example.com",
  "steps": [
    {
      "name": "Step name",
      "action": "goto|click|fill|wait_for|expect|screenshot|execute",
      "selector": "CSS or XPath selector (if needed)",
      "value": "Value for action (if needed)",
      "url": "URL for goto action",
      "timeout": 30000,
      "screenshot": false,
      "wait_before": null,
      "wait_after": null
    }
  ],
  "evaluators": [
    {
      "name": "Evaluator name",
      "evaluator_type": "all_steps_completed|no_console_errors|url_matches|element_visible|etc",
      "params": {},
      "required": true,
      "weight": 1.0
    }
  ],
  "timeout": 30000,
  "screenshot_strategy": "on_error",
  "tags": ["tag1", "tag2"]
}
```

## Available Actions

- **goto**: Navigate to a URL (requires `url` field)
- **click**: Click an element (requires `selector`)
- **fill**: Fill input field (requires `selector` and `value`)
- **wait_for**: Wait for element to appear (requires `selector`)
- **expect**: Assert element state (requires `selector` and `value` for expected text/attribute)
- **screenshot**: Capture screenshot
- **execute**: Execute JavaScript code (requires `value` with code)

## Available Evaluators

- **all_steps_completed**: Verify all steps completed successfully
- **no_console_errors**: Check for console errors
- **no_console_warnings**: Check for console warnings
- **url_matches**: Verify final URL matches pattern (params: {"pattern": "regex"})
- **title_matches**: Verify page title (params: {"pattern": "regex"})
- **element_visible**: Check element is visible (params: {"selector": "css"})
- **element_has_text**: Check element has text (params: {"selector": "css", "text": "expected"})
- **page_load_time**: Check page load performance (params: {"max_ms": 3000})

## Selector Best Practices

1. Prefer data-testid attributes: `[data-testid="submit-button"]`
2. Use semantic selectors: `button[type="submit"]`, `input[name="email"]`
3. Avoid brittle selectors: nth-child, absolute positions
4. Use text selectors when appropriate: `text=Login`, `button:has-text("Submit")`
5. Prefer IDs when available: `#login-button`

## Example Test Definitions

### Example 1: Simple Login Test
```json
{
  "name": "login_test",
  "description": "Test user login with valid credentials",
  "version": "1.0",
  "url": "https://example.com/login",
  "steps": [
    {
      "name": "Navigate to login page",
      "action": "goto",
      "url": "https://example.com/login"
    },
    {
      "name": "Fill username",
      "action": "fill",
      "selector": "input[name='username']",
      "value": "admin"
    },
    {
      "name": "Fill password",
      "action": "fill",
      "selector": "input[name='password']",
      "value": "password123"
    },
    {
      "name": "Click login button",
      "action": "click",
      "selector": "button[type='submit']"
    },
    {
      "name": "Wait for dashboard",
      "action": "wait_for",
      "selector": "[data-testid='dashboard']",
      "timeout": 5000
    }
  ],
  "evaluators": [
    {
      "name": "All steps completed",
      "evaluator_type": "all_steps_completed",
      "params": {},
      "required": true,
      "weight": 1.0
    },
    {
      "name": "No console errors",
      "evaluator_type": "no_console_errors",
      "params": {},
      "required": true,
      "weight": 1.0
    },
    {
      "name": "URL is dashboard",
      "evaluator_type": "url_matches",
      "params": {"pattern": ".*/dashboard"},
      "required": true,
      "weight": 1.0
    }
  ],
  "timeout": 30000,
  "screenshot_strategy": "on_error",
  "tags": ["authentication", "login", "critical"]
}
```

### Example 2: Form Submission Test
```json
{
  "name": "contact_form_test",
  "description": "Test contact form submission",
  "version": "1.0",
  "url": "https://example.com/contact",
  "steps": [
    {
      "name": "Navigate to contact page",
      "action": "goto",
      "url": "https://example.com/contact"
    },
    {
      "name": "Fill name",
      "action": "fill",
      "selector": "#name",
      "value": "John Doe"
    },
    {
      "name": "Fill email",
      "action": "fill",
      "selector": "#email",
      "value": "john@example.com"
    },
    {
      "name": "Fill message",
      "action": "fill",
      "selector": "#message",
      "value": "This is a test message"
    },
    {
      "name": "Submit form",
      "action": "click",
      "selector": "button:has-text('Submit')"
    },
    {
      "name": "Wait for success message",
      "action": "wait_for",
      "selector": ".success-message",
      "timeout": 5000
    }
  ],
  "evaluators": [
    {
      "name": "All steps completed",
      "evaluator_type": "all_steps_completed",
      "params": {},
      "required": true,
      "weight": 1.0
    },
    {
      "name": "Success message visible",
      "evaluator_type": "element_visible",
      "params": {"selector": ".success-message"},
      "required": true,
      "weight": 1.0
    }
  ],
  "timeout": 30000,
  "screenshot_strategy": "on_error",
  "tags": ["forms", "contact"]
}
```

## Important Instructions

1. Always return valid JSON that matches the schema exactly
2. Generate test names using snake_case (e.g., "login_test", "search_products")
3. Include appropriate evaluators for the test scenario
4. Use realistic, descriptive step names
5. Set appropriate timeouts for async operations
6. Add relevant tags for categorization
7. If URL is not specified in description, use "https://example.com" as placeholder
8. Include wait_for steps after actions that trigger navigation or async updates
9. Always include at least the "all_steps_completed" evaluator
10. Return ONLY the JSON, no additional text or explanation
"""


def get_test_generation_prompt(
    description: str,
    base_url: str | None = None,
    page_context: dict[str, Any] | None = None,
) -> str:
    """Generate user prompt for test generation.

    Args:
        description: Natural language test description
        base_url: Optional base URL to use in the test
        page_context: Optional page context from browser extraction

    Returns:
        Formatted user prompt
    """
    prompt = f"""Generate a test definition for the following description:

{description}
"""

    if base_url:
        prompt += f"""
Use this base URL: {base_url}
"""

    # Add page context if available - this is the key enhancement!
    if page_context:
        prompt += f"""
## IMPORTANT: Real Page Context

I have loaded the actual page and extracted the following information.
**You MUST use these exact selectors** - they are verified to exist on the page:

Page Title: {page_context.get('title', 'Unknown')}
Page URL: {page_context.get('url', base_url or 'Unknown')}

### Available Interactive Elements:

"""
        elements = page_context.get("elements", [])

        # Group elements by type for clarity
        buttons = [e for e in elements if e.get("type") == "button"]
        inputs = [e for e in elements if e.get("type") == "input"]
        links = [e for e in elements if e.get("type") == "link"]
        selects = [e for e in elements if e.get("type") == "select"]
        forms = [e for e in elements if e.get("type") == "form"]

        if buttons:
            prompt += "**Buttons:**\n"
            for btn in buttons[:10]:  # Limit to avoid huge prompts
                text = btn.get("text", "").strip()
                prompt += f"- Selector: `{btn['selector']}` | Text: \"{text}\"\n"
            prompt += "\n"

        if inputs:
            prompt += "**Input Fields:**\n"
            for inp in inputs[:10]:
                input_type = inp.get("inputType", "text")
                name = inp.get("name", "")
                placeholder = inp.get("placeholder", "")
                prompt += f"- Selector: `{inp['selector']}` | Type: {input_type} | Name: \"{name}\" | Placeholder: \"{placeholder}\"\n"
            prompt += "\n"

        if selects:
            prompt += "**Dropdowns:**\n"
            for sel in selects[:5]:
                options = ", ".join(sel.get("options", [])[:3])
                prompt += f"- Selector: `{sel['selector']}` | Options: [{options}...]\n"
            prompt += "\n"

        if links:
            prompt += "**Links:**\n"
            for link in links[:10]:
                text = link.get("text", "").strip()
                href = link.get("href", "")
                prompt += f"- Selector: `{link['selector']}` | Text: \"{text}\" | Href: {href}\n"
            prompt += "\n"

        if forms:
            prompt += "**Forms:**\n"
            for form in forms[:3]:
                prompt += f"- Selector: `{form['selector']}` | Action: {form.get('action', '')} | Method: {form.get('method', 'get')}\n"
            prompt += "\n"

        prompt += """
**CRITICAL:** Use ONLY the selectors listed above. Do not make up selectors or guess - they will fail.
If you need a selector that's not listed, use a more generic approach like waiting for text content.

"""

    prompt += """
Return ONLY a valid JSON object that matches the test definition schema. Do not include any markdown formatting, code blocks, or explanatory text - just the raw JSON.
"""

    return prompt


def get_evaluator_selection_prompt(test_definition: dict[str, Any]) -> str:
    """Generate prompt for selecting appropriate evaluators.

    Args:
        test_definition: Generated test definition

    Returns:
        Prompt for evaluator selection
    """
    return f"""Given this test definition:

{test_definition}

Suggest the most appropriate evaluators for this test. Consider:
1. What could go wrong in this test?
2. What should be verified to ensure success?
3. What performance considerations are important?

Return a JSON array of evaluator configurations. Each evaluator should have:
- name: Descriptive name
- evaluator_type: One of the available evaluator types
- params: Parameters for the evaluator
- required: Whether this is required for test to pass
- weight: Importance weight (0.0 to 1.0)

Return ONLY the JSON array, no additional text.
"""


# Prompt for refining/improving existing tests
SYSTEM_PROMPT_TEST_REFINEMENT = """You are an expert UI test engineer specializing in improving automated browser tests.

Your task is to analyze existing test definitions and suggest improvements for:
- Selector robustness
- Missing assertions
- Better error handling
- Performance optimization
- Accessibility considerations

Provide specific, actionable recommendations in a structured format.
"""


def get_test_refinement_prompt(test_definition: dict[str, Any], issues: list[str]) -> str:
    """Generate prompt for refining an existing test.

    Args:
        test_definition: Existing test definition
        issues: List of issues encountered during execution

    Returns:
        Prompt for test refinement
    """
    issues_text = "\n".join(f"- {issue}" for issue in issues)

    return f"""Analyze this test definition and the issues encountered:

Test Definition:
{test_definition}

Issues Encountered:
{issues_text}

Suggest specific improvements to make this test more robust. Return a JSON object with:
{{
  "selector_improvements": [
    {{"step_name": "...", "current_selector": "...", "suggested_selector": "...", "reason": "..."}}
  ],
  "missing_evaluators": [
    {{"name": "...", "evaluator_type": "...", "params": {{}}, "reason": "..."}}
  ],
  "timeout_adjustments": [
    {{"step_name": "...", "current_timeout": ..., "suggested_timeout": ..., "reason": "..."}}
  ],
  "additional_steps": [
    {{"name": "...", "action": "...", "insert_after": "...", "reason": "..."}}
  ]
}}

Return ONLY the JSON object, no additional text.
"""
