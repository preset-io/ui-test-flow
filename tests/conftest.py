"""Pytest configuration and fixtures for UITestFlow tests."""

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from playwright.async_api import Browser, BrowserContext, Page, async_playwright


# Set test environment
os.environ["UITESTFLOW_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def sample_yaml_test(test_data_dir: Path) -> str:
    """Return path to sample YAML test file."""
    yaml_path = test_data_dir / "sample_test.yaml"
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = """version: "1.0"
name: "Sample Test"
description: "A sample test for testing"
url: "https://example.com"

steps:
  - name: "Navigate to page"
    action: "goto"
    url: "{{ base_url }}"

  - name: "Check title"
    action: "expect"
    assertion: "title_contains"
    value: "Example"

evaluators:
  - name: "execution_successful"
  - name: "within_time_limit"
    args:
      max_duration_ms: 5000
"""
    yaml_path.write_text(yaml_content)
    return str(yaml_path)


@pytest.fixture
def sample_profile_yaml(test_data_dir: Path) -> str:
    """Return path to sample profile YAML file."""
    yaml_path = test_data_dir / ".uitest_profiles.yaml"
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    yaml_content = """default: local

profiles:
  local:
    name: "Local Development"
    base_url: "http://localhost:8080"
    auth:
      type: "form"
      username: "admin"
      password: "admin"
    browser:
      type: "chromium"
      headless: true
      viewport:
        width: 1920
        height: 1080

  staging:
    name: "Staging"
    base_url: "https://staging.example.com"
    auth:
      type: "bearer"
      token: "${STAGING_TOKEN}"
    browser:
      type: "chromium"
      headless: true
"""
    yaml_path.write_text(yaml_content)
    return str(yaml_path)


@pytest.fixture
async def browser() -> AsyncGenerator[Browser, None]:
    """Create Playwright browser instance."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def context(browser: Browser) -> AsyncGenerator[BrowserContext, None]:
    """Create browser context."""
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    yield context
    await context.close()


@pytest.fixture
async def page(context: BrowserContext) -> AsyncGenerator[Page, None]:
    """Create browser page."""
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture
def mock_test_run():
    """Create mock TestRun for testing."""
    from uuid import uuid4

    from uitestflow.core.models import TestRun, TestStatus

    return TestRun(
        id=uuid4(),
        test_id=uuid4(),
        profile="local",
        status=TestStatus.PENDING,
        started_at=None,
        completed_at=None,
        duration_ms=None,
        result=None,
        screenshots=[],
        video_url=None,
        trace_url=None,
        logs=[],
        context={},
    )


@pytest.fixture
def mock_test_definition():
    """Create mock TestDefinition for testing."""
    from uuid import uuid4

    from uitestflow.core.models import ActionType, EvaluatorConfig, TestDefinition, TestStep

    return TestDefinition(
        id=uuid4(),
        name="Sample Test",
        description="A sample test",
        version="1.0",
        url="https://example.com",
        steps=[
            TestStep(
                name="Navigate to page",
                action=ActionType.GOTO,
                url="https://example.com",
                timeout=30000,
            ),
            TestStep(
                name="Wait for content",
                action=ActionType.WAIT_FOR,
                selector=".content",
                timeout=5000,
            ),
        ],
        evaluators=[
            EvaluatorConfig(name="execution_successful"),
            EvaluatorConfig(name="within_time_limit", args={"max_duration_ms": 5000}),
        ],
        tags=["smoke", "example"],
    )
