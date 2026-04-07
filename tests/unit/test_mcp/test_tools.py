"""Unit tests for MCP tools."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from uitestflow.mcp.tools import PlaywrightTools
from uitestflow.mcp.types import (
    BrowserError,
    ConsoleLogLevel,
    JavaScriptError,
    MCPTimeoutError,
    ScreenshotError,
    SelectorError,
)


class TestToolsInitialization:
    """Test tools initialization."""

    def test_tools_creation(self) -> None:
        """Test tools can be instantiated."""
        tools = PlaywrightTools()
        assert tools is not None
        assert tools.page is None
        assert len(tools._console_logs) == 0

    def test_tools_with_page(self) -> None:
        """Test tools with page."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()

        tools = PlaywrightTools(page=mock_page)
        assert tools.page is mock_page

    def test_set_page(self) -> None:
        """Test setting page."""
        tools = PlaywrightTools()
        mock_page = AsyncMock()
        mock_page.on = MagicMock()

        tools.set_page(mock_page)
        assert tools.page is mock_page


class TestNavigateTool:
    """Test navigate tool."""

    @pytest.mark.asyncio
    async def test_navigate_success(self) -> None:
        """Test successful navigation."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()

        mock_response = Mock()
        mock_response.status = 200
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.url = "https://example.com/"

        tools = PlaywrightTools(page=mock_page)
        result = await tools.navigate("https://example.com")

        assert result.success
        assert result.data["url"] == "https://example.com/"
        assert result.data["status_code"] == 200
        assert result.data["redirected"] is True
        mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_navigate_timeout(self) -> None:
        """Test navigation timeout."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.goto = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(MCPTimeoutError) as exc_info:
            await tools.navigate("https://example.com", timeout=5000)

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_navigate_no_page(self) -> None:
        """Test navigate without page."""
        tools = PlaywrightTools()

        with pytest.raises(BrowserError, match="No page available"):
            await tools.navigate("https://example.com")

    @pytest.mark.asyncio
    async def test_navigate_with_redirect(self) -> None:
        """Test navigation with redirect."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()

        mock_response = Mock()
        mock_response.status = 301
        mock_page.goto = AsyncMock(return_value=mock_response)
        mock_page.url = "https://example.com/new-page"

        tools = PlaywrightTools(page=mock_page)
        result = await tools.navigate("https://example.com")

        assert result.success
        assert result.data["redirected"] is True


class TestClickTool:
    """Test click tool."""

    @pytest.mark.asyncio
    async def test_click_success(self) -> None:
        """Test successful click."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.click = AsyncMock()

        tools = PlaywrightTools(page=mock_page)
        result = await tools.click("button.submit")

        assert result.success
        assert result.data["selector"] == "button.submit"
        mock_page.click.assert_called_once_with("button.submit", timeout=5000)

    @pytest.mark.asyncio
    async def test_click_timeout(self) -> None:
        """Test click timeout."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.click = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(MCPTimeoutError) as exc_info:
            await tools.click("button.submit", timeout=3000)

        assert (
            "not found" in str(exc_info.value).lower()
            or "not clickable" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_click_custom_timeout(self) -> None:
        """Test click with custom timeout."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.click = AsyncMock()

        tools = PlaywrightTools(page=mock_page)
        await tools.click("button", timeout=10000)

        mock_page.click.assert_called_once_with("button", timeout=10000)


class TestFillTool:
    """Test fill tool."""

    @pytest.mark.asyncio
    async def test_fill_success(self) -> None:
        """Test successful fill."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.fill = AsyncMock()

        tools = PlaywrightTools(page=mock_page)
        result = await tools.fill("input[name='username']", "admin")

        assert result.success
        assert result.data["selector"] == "input[name='username']"
        assert result.data["value_length"] == 5
        mock_page.fill.assert_called_once_with("input[name='username']", "admin", timeout=5000)

    @pytest.mark.asyncio
    async def test_fill_timeout(self) -> None:
        """Test fill timeout."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.fill = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(MCPTimeoutError):
            await tools.fill("input", "value")

    @pytest.mark.asyncio
    async def test_fill_error(self) -> None:
        """Test fill with non-input element."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.fill = AsyncMock(side_effect=Exception("Not an input"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(SelectorError):
            await tools.fill("div", "value")


class TestWaitForSelectorTool:
    """Test wait_for_selector tool."""

    @pytest.mark.asyncio
    async def test_wait_for_selector_success(self) -> None:
        """Test successful wait."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.wait_for_selector = AsyncMock()

        tools = PlaywrightTools(page=mock_page)
        result = await tools.wait_for_selector("#loading")

        assert result.success
        assert result.data["selector"] == "#loading"
        assert result.data["state"] == "visible"
        mock_page.wait_for_selector.assert_called_once_with(
            "#loading", timeout=5000, state="visible"
        )

    @pytest.mark.asyncio
    async def test_wait_for_selector_hidden(self) -> None:
        """Test wait for hidden state."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.wait_for_selector = AsyncMock()

        tools = PlaywrightTools(page=mock_page)
        result = await tools.wait_for_selector("#loading", state="hidden")

        assert result.success
        assert result.data["state"] == "hidden"

    @pytest.mark.asyncio
    async def test_wait_for_selector_timeout(self) -> None:
        """Test wait timeout."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.wait_for_selector = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(MCPTimeoutError):
            await tools.wait_for_selector("#loading", timeout=3000)


class TestScreenshotTool:
    """Test screenshot tool."""

    @pytest.mark.asyncio
    async def test_screenshot_success(self) -> None:
        """Test successful screenshot."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake image data")
        mock_page.viewport_size = {"width": 1920, "height": 1080}

        tools = PlaywrightTools(page=mock_page)
        result = await tools.screenshot()

        assert result.success
        assert "screenshot" in result.data
        assert result.data["screenshot"]["size"] > 0
        assert result.data["screenshot"]["width"] == 1920
        assert result.data["screenshot"]["height"] == 1080

    @pytest.mark.asyncio
    async def test_screenshot_full_page(self) -> None:
        """Test full page screenshot."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.screenshot = AsyncMock(return_value=b"fake image data")
        mock_page.viewport_size = {"width": 1920, "height": 1080}

        tools = PlaywrightTools(page=mock_page)
        result = await tools.screenshot(full_page=True)

        assert result.success
        assert result.data["screenshot"]["full_page"] is True
        mock_page.screenshot.assert_called_once_with(full_page=True, type="png")

    @pytest.mark.asyncio
    async def test_screenshot_error(self) -> None:
        """Test screenshot error."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.screenshot = AsyncMock(side_effect=Exception("Screenshot failed"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(ScreenshotError):
            await tools.screenshot()


class TestGetPageStateTool:
    """Test get_page_state tool."""

    @pytest.mark.asyncio
    async def test_get_page_state_success(self) -> None:
        """Test getting page state."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(return_value="Example Page")
        mock_page.viewport_size = {"width": 1920, "height": 1080}

        tools = PlaywrightTools(page=mock_page)
        result = await tools.get_page_state()

        assert result.success
        assert result.data["page_state"]["url"] == "https://example.com"
        assert result.data["page_state"]["title"] == "Example Page"
        assert result.data["page_state"]["viewport"]["width"] == 1920

    @pytest.mark.asyncio
    async def test_get_page_state_error(self) -> None:
        """Test get page state error."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.url = "https://example.com"
        mock_page.title = AsyncMock(side_effect=Exception("Failed"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(BrowserError):
            await tools.get_page_state()


class TestGetTextTool:
    """Test get_text tool."""

    @pytest.mark.asyncio
    async def test_get_text_success(self) -> None:
        """Test getting text."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()

        mock_element = AsyncMock()
        mock_element.text_content = AsyncMock(return_value="  Hello World  ")
        mock_page.wait_for_selector = AsyncMock(return_value=mock_element)

        tools = PlaywrightTools(page=mock_page)
        result = await tools.get_text("h1")

        assert result.success
        assert result.data["text"] == "Hello World"
        assert result.data["selector"] == "h1"
        assert result.data["length"] == 11

    @pytest.mark.asyncio
    async def test_get_text_not_found(self) -> None:
        """Test get text when element not found."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.wait_for_selector = AsyncMock(return_value=None)

        tools = PlaywrightTools(page=mock_page)
        result = await tools.get_text("h1")

        assert result.success
        assert result.data["text"] == ""

    @pytest.mark.asyncio
    async def test_get_text_timeout(self) -> None:
        """Test get text timeout."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.wait_for_selector = AsyncMock(side_effect=PlaywrightTimeoutError("Timeout"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(MCPTimeoutError):
            await tools.get_text("h1")


class TestEvaluateJavaScriptTool:
    """Test evaluate_javascript tool."""

    @pytest.mark.asyncio
    async def test_evaluate_javascript_success(self) -> None:
        """Test JavaScript evaluation."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.evaluate = AsyncMock(return_value="Result")

        tools = PlaywrightTools(page=mock_page)
        result = await tools.evaluate_javascript("document.title")

        assert result.success
        assert result.data["result"] == "Result"

    @pytest.mark.asyncio
    async def test_evaluate_javascript_error(self) -> None:
        """Test JavaScript error."""
        mock_page = AsyncMock()
        mock_page.on = MagicMock()
        mock_page.evaluate = AsyncMock(side_effect=Exception("Syntax error"))

        tools = PlaywrightTools(page=mock_page)

        with pytest.raises(JavaScriptError):
            await tools.evaluate_javascript("invalid js")


class TestGetConsoleLogsTool:
    """Test get_console_logs tool."""

    @pytest.mark.asyncio
    async def test_get_console_logs_all(self) -> None:
        """Test getting all console logs."""
        tools = PlaywrightTools()

        # Add some mock logs
        tools._console_logs = [
            Mock(
                level=ConsoleLogLevel.ERROR,
                message="Error message",
                timestamp=datetime.utcnow(),
                args=[],
                location=None,
                to_dict=lambda: {
                    "level": "error",
                    "message": "Error message",
                    "timestamp": datetime.utcnow().isoformat(),
                    "args": [],
                    "location": None,
                },
            ),
            Mock(
                level=ConsoleLogLevel.LOG,
                message="Log message",
                timestamp=datetime.utcnow(),
                args=[],
                location=None,
                to_dict=lambda: {
                    "level": "log",
                    "message": "Log message",
                    "timestamp": datetime.utcnow().isoformat(),
                    "args": [],
                    "location": None,
                },
            ),
        ]

        result = await tools.get_console_logs()

        assert result.success
        assert result.data["count"] == 2

    @pytest.mark.asyncio
    async def test_get_console_logs_filtered(self) -> None:
        """Test getting filtered console logs."""
        tools = PlaywrightTools()

        # Add some mock logs
        tools._console_logs = [
            Mock(
                level=ConsoleLogLevel.ERROR,
                message="Error",
                to_dict=lambda: {"level": "error", "message": "Error"},
            ),
            Mock(
                level=ConsoleLogLevel.LOG,
                message="Log",
                to_dict=lambda: {"level": "log", "message": "Log"},
            ),
        ]

        result = await tools.get_console_logs(level="error")

        assert result.success
        assert result.data["count"] == 1
        assert result.data["level"] == "error"

    @pytest.mark.asyncio
    async def test_get_console_logs_clear(self) -> None:
        """Test clearing console logs."""
        tools = PlaywrightTools()

        # Add some mock logs
        tools._console_logs = [
            Mock(
                level=ConsoleLogLevel.LOG,
                message="Log",
                to_dict=lambda: {"level": "log", "message": "Log"},
            )
        ]

        result = await tools.get_console_logs(clear=True)

        assert result.success
        assert len(tools._console_logs) == 0


class TestCloseBrowserTool:
    """Test close_browser tool."""

    @pytest.mark.asyncio
    async def test_close_browser(self) -> None:
        """Test close browser."""
        tools = PlaywrightTools()
        result = await tools.close_browser()

        assert result.success
        assert result.data["closed"] is True


class TestToolSchemas:
    """Test tool schemas."""

    def test_all_tools_have_schemas(self) -> None:
        """Test all tools have schemas."""
        from uitestflow.mcp.tools import TOOL_SCHEMAS

        expected_tools = [
            "navigate",
            "click",
            "fill",
            "wait_for_selector",
            "screenshot",
            "get_page_state",
            "get_text",
            "evaluate_javascript",
            "get_console_logs",
            "close_browser",
        ]

        for tool in expected_tools:
            assert tool in TOOL_SCHEMAS
            assert "name" in TOOL_SCHEMAS[tool]
            assert "description" in TOOL_SCHEMAS[tool]
            assert "inputSchema" in TOOL_SCHEMAS[tool]

    def test_navigate_schema(self) -> None:
        """Test navigate schema."""
        from uitestflow.mcp.tools import TOOL_SCHEMAS

        schema = TOOL_SCHEMAS["navigate"]
        assert schema["name"] == "navigate"
        assert "url" in schema["inputSchema"]["properties"]
        assert "url" in schema["inputSchema"]["required"]

    def test_click_schema(self) -> None:
        """Test click schema."""
        from uitestflow.mcp.tools import TOOL_SCHEMAS

        schema = TOOL_SCHEMAS["click"]
        assert schema["name"] == "click"
        assert "selector" in schema["inputSchema"]["properties"]
        assert "selector" in schema["inputSchema"]["required"]
