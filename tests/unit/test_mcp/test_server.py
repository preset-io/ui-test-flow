"""Unit tests for MCP server."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from uitestflow.mcp import PlaywrightMCPServer
from uitestflow.src.models import BrowserConfig


class TestMCPServerInitialization:
    """Test MCP server initialization."""

    def test_server_creation(self) -> None:
        """Test server can be instantiated."""
        server = PlaywrightMCPServer()
        assert server is not None
        assert server.server_name == "playwright-mcp-server"
        assert not server.is_running()
        assert not server.is_browser_running()

    def test_server_with_custom_config(self) -> None:
        """Test server with custom browser config."""
        config = BrowserConfig(type="firefox", headless=False)
        server = PlaywrightMCPServer(browser_config=config, server_name="custom-server")
        assert server.server_name == "custom-server"
        assert server.browser_config.type == "firefox"
        assert server.browser_config.headless is False

    @pytest.mark.asyncio
    async def test_server_start_stop(self) -> None:
        """Test server start and stop."""
        server = PlaywrightMCPServer()
        assert not server.is_running()

        await server.start_server()
        assert server.is_running()

        await server.stop_server()
        assert not server.is_running()

    @pytest.mark.asyncio
    async def test_server_cleanup(self) -> None:
        """Test server cleanup releases resources."""
        server = PlaywrightMCPServer()

        # Mock browser components
        server._page = AsyncMock()
        server._context = AsyncMock()
        server._browser = AsyncMock()
        server._playwright = AsyncMock()

        await server.cleanup()

        # Verify cleanup was called
        server._page.close.assert_called_once()
        server._context.close.assert_called_once()
        server._browser.close.assert_called_once()
        server._playwright.stop.assert_called_once()

        # Verify instances are None
        assert server._page is None
        assert server._context is None
        assert server._browser is None
        assert server._playwright is None


class TestToolRegistration:
    """Test tool registration."""

    def test_list_tools(self) -> None:
        """Test listing all tools."""
        server = PlaywrightMCPServer()
        tools = server.list_tools()

        assert len(tools) == 10
        assert "navigate" in tools
        assert "click" in tools
        assert "fill" in tools
        assert "wait_for_selector" in tools
        assert "screenshot" in tools
        assert "get_page_state" in tools
        assert "get_text" in tools
        assert "evaluate_javascript" in tools
        assert "get_console_logs" in tools
        assert "close_browser" in tools

    @pytest.mark.asyncio
    async def test_setup_tools(self) -> None:
        """Test tools setup."""
        server = PlaywrightMCPServer()
        await server.setup_tools()
        # setup_tools is a no-op, just verify it doesn't raise
        assert True


class TestBrowserLifecycle:
    """Test browser lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_browser(self) -> None:
        """Test browser startup."""
        server = PlaywrightMCPServer()

        with patch("uitestflow.mcp.server.async_playwright") as mock_playwright:
            # Create mock chain
            mock_pw = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

            mock_browser = AsyncMock()
            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)
            mock_pw.chromium = mock_chromium

            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_page = AsyncMock()
            mock_page.on = MagicMock()
            mock_context.new_page = AsyncMock(return_value=mock_page)

            await server.start_browser()

            assert server.is_browser_running()
            assert server._browser is not None
            assert server._page is not None

    @pytest.mark.asyncio
    async def test_start_browser_already_started(self) -> None:
        """Test starting browser when already started."""
        server = PlaywrightMCPServer()

        # Mock page as already started
        server._page = AsyncMock()

        await server.start_browser()

        # Should not create new browser
        assert server._page is not None

    @pytest.mark.asyncio
    async def test_browser_state(self) -> None:
        """Test getting browser state."""
        server = PlaywrightMCPServer()

        # Before browser starts
        state = await server.get_browser_state()
        assert not state.is_running
        assert state.page_state is None
        assert state.active_contexts == 0
        assert state.active_pages == 0

        # After browser starts (mocked)
        server._browser = AsyncMock()
        server._context = AsyncMock()
        server._page = AsyncMock()

        state = await server.get_browser_state()
        assert state.is_running
        assert state.active_contexts == 1
        assert state.active_pages == 1


class TestToolHandling:
    """Test tool call handling."""

    @pytest.mark.asyncio
    async def test_tools_registered(self) -> None:
        """Test that tools are registered with MCP server."""
        server = PlaywrightMCPServer()

        # Check that MCP server exists and has tools registered
        assert server.mcp is not None
        assert server.list_tools() == [
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


class TestErrorHandling:
    """Test error handling."""

    @pytest.mark.asyncio
    async def test_cleanup_error_handling(self) -> None:
        """Test cleanup handles errors gracefully."""
        server = PlaywrightMCPServer()

        # Mock page that raises error on close
        server._page = AsyncMock()
        server._page.close.side_effect = Exception("Close failed")

        # Should not raise
        await server.cleanup()

        # Should still set to None
        assert server._page is None


class TestTypeSafety:
    """Test type safety and validation."""

    def test_browser_config_defaults(self) -> None:
        """Test BrowserConfig has correct defaults."""
        config = BrowserConfig()
        assert config.type == "chromium"
        assert config.headless is True
        assert config.viewport == {"width": 1920, "height": 1080}

    def test_server_accepts_valid_config(self) -> None:
        """Test server accepts valid config."""
        config = BrowserConfig(
            type="firefox",
            headless=False,
            viewport={"width": 1280, "height": 720},
        )
        server = PlaywrightMCPServer(browser_config=config)
        assert server.browser_config.type == "firefox"


class TestIntegration:
    """Integration tests with mocked Playwright."""

    @pytest.mark.asyncio
    async def test_full_workflow(self) -> None:
        """Test full workflow from server start to cleanup."""
        server = PlaywrightMCPServer()

        with patch("uitestflow.mcp.server.async_playwright") as mock_playwright:
            # Setup mocks
            mock_pw = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_pw)

            mock_browser = AsyncMock()
            mock_chromium = AsyncMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)
            mock_pw.chromium = mock_chromium

            mock_context = AsyncMock()
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_page = AsyncMock()
            mock_page.on = MagicMock()
            mock_page.url = "https://example.com"
            mock_page.title = AsyncMock(return_value="Example")
            mock_page.viewport_size = {"width": 1920, "height": 1080}
            mock_context.new_page = AsyncMock(return_value=mock_page)

            # Start server
            await server.start_server()
            assert server.is_running()

            # Start browser
            await server.start_browser()
            assert server.is_browser_running()

            # Get browser state
            state = await server.get_browser_state()
            assert state.is_running
            assert state.active_pages == 1

            # Stop server
            await server.stop_server()
            assert not server.is_running()
