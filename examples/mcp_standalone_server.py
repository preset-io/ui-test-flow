#!/usr/bin/env python3
"""
Standalone MCP Server Example

This example demonstrates how to run the MCP Playwright server as a standalone
process that can be connected to by Claude or other MCP clients.

Usage:
    python examples/mcp_standalone_server.py

The server will run with stdio transport and wait for MCP requests.
It can be used with Claude Desktop by configuring it in the claude_desktop_config.json:

{
  "mcpServers": {
    "playwright": {
      "command": "python",
      "args": ["path/to/examples/mcp_standalone_server.py"]
    }
  }
}

Available Tools:
- navigate(url, timeout) - Navigate to a URL
- click(selector, timeout) - Click an element
- fill(selector, value, timeout) - Fill an input field
- wait_for_selector(selector, timeout, state) - Wait for an element
- screenshot(full_page) - Capture a screenshot
- get_page_state() - Get current page state
- get_text(selector, timeout) - Extract text from an element
- evaluate_javascript(code) - Execute JavaScript
- get_console_logs(level, clear) - Get console logs
- close_browser() - Close the browser

Example Tool Calls (via MCP):
1. Navigate to a page:
   {"url": "https://example.com", "timeout": 30000}

2. Click a button:
   {"selector": "button.submit", "timeout": 5000}

3. Fill a form field:
   {"selector": "input[name='username']", "value": "admin", "timeout": 5000}

4. Take a screenshot:
   {"full_page": true}

5. Get page state:
   {}

6. Extract text:
   {"selector": "h1", "timeout": 5000}

7. Execute JavaScript:
   {"code": "return document.title"}

8. Get console errors:
   {"level": "error", "clear": false}
"""

import asyncio
import logging
import sys
from pathlib import Path


# Add parent directory to path to import uitestflow
sys.path.insert(0, str(Path(__file__).parent.parent))

from uitestflow.mcp import PlaywrightMCPServer
from uitestflow.src.models import BrowserConfig


async def run_server_with_headless_browser() -> None:
    """
    Run MCP server with headless browser.

    This is the default configuration for production use.
    """
    config = BrowserConfig(
        type="chromium",
        headless=True,
        viewport={"width": 1920, "height": 1080},
    )

    server = PlaywrightMCPServer(
        browser_config=config,
        server_name="playwright-mcp-server",
    )

    logging.info("Starting MCP server (headless mode)...")
    await server.run_server()


async def run_server_with_headed_browser() -> None:
    """
    Run MCP server with visible browser.

    Useful for debugging and development.
    """
    config = BrowserConfig(
        type="chromium",
        headless=False,
        viewport={"width": 1280, "height": 720},
        slow_mo=100,  # Slow down actions by 100ms for visibility
    )

    server = PlaywrightMCPServer(
        browser_config=config,
        server_name="playwright-mcp-server-headed",
    )

    logging.info("Starting MCP server (headed mode)...")
    await server.run_server()


async def run_server_with_firefox() -> None:
    """
    Run MCP server with Firefox browser.

    Example of using a different browser engine.
    """
    config = BrowserConfig(
        type="firefox",
        headless=True,
        viewport={"width": 1920, "height": 1080},
    )

    server = PlaywrightMCPServer(
        browser_config=config,
        server_name="playwright-mcp-server-firefox",
    )

    logging.info("Starting MCP server (Firefox)...")
    await server.run_server()


async def demonstrate_tools() -> None:
    """
    Demonstrate all available tools (for testing purposes).

    Note: This is not the typical usage. Normally, tools are called
    via MCP by Claude or another client.
    """
    # Create server
    config = BrowserConfig(headless=True)
    server = PlaywrightMCPServer(browser_config=config)

    try:
        # Start browser
        await server.start_browser()
        logging.info("Browser started successfully")

        # Tool 1: Navigate
        logging.info("\n=== Tool 1: Navigate ===")
        result = await server.tools.navigate("https://example.com")
        logging.info(f"Navigate result: {result.message}")
        logging.info(f"Final URL: {result.data.get('url')}")

        # Tool 2: Get page state
        logging.info("\n=== Tool 2: Get Page State ===")
        result = await server.tools.get_page_state()
        logging.info(f"Page state: {result.data.get('page_state')}")

        # Tool 3: Get text
        logging.info("\n=== Tool 3: Get Text ===")
        result = await server.tools.get_text("h1")
        logging.info(f"Page title: {result.data.get('text')}")

        # Tool 4: Wait for selector
        logging.info("\n=== Tool 4: Wait for Selector ===")
        result = await server.tools.wait_for_selector("h1", state="visible")
        logging.info(f"Wait result: {result.message}")
        logging.info(f"Element state: {result.data.get('state')}")

        # Tool 5: Screenshot
        logging.info("\n=== Tool 5: Screenshot ===")
        result = await server.tools.screenshot(full_page=False)
        screenshot_size = result.data.get("screenshot", {}).get("size", 0)
        logging.info("Screenshot captured: %s bytes", screenshot_size)

        # Tool 6: Execute JavaScript
        logging.info("\n=== Tool 6: Execute JavaScript ===")
        result = await server.tools.evaluate_javascript("document.title")
        logging.info(f"Document title: {result.data.get('result')}")

        # Tool 7: Get console logs
        logging.info("\n=== Tool 7: Get Console Logs ===")
        result = await server.tools.get_console_logs()
        logging.info(f"Console logs: {result.data.get('count')} entries")

        # Tool 8: Navigate to a form demo page
        logging.info("\n=== Tool 8: Click and Fill Demo ===")
        result = await server.tools.navigate("https://www.w3schools.com/html/html_forms.asp")
        logging.info(f"Navigate to form demo: {result.message}")

        # Tool 9: Click demonstration (click on first input)
        try:
            logging.info("\n=== Tool 9: Click ===")
            result = await server.tools.click("input[type='text']", timeout=5000)
            logging.info(f"Click result: {result.message}")
        except Exception as e:
            logging.info("Click demo (expected to vary): %s", e)

        # Tool 10: Fill demonstration
        try:
            logging.info("\n=== Tool 10: Fill ===")
            result = await server.tools.fill("input[type='text']", "Test Input", timeout=5000)
            logging.info(f"Fill result: {result.message}")
            logging.info(f"Value length: {result.data.get('value_length')}")
        except Exception as e:
            logging.info("Fill demo (expected to vary): %s", e)

        # Tool 11: Close browser
        logging.info("\n=== Tool 11: Close Browser ===")
        result = await server.tools.close_browser()
        logging.info(f"Close browser result: {result.message}")

        logging.info("\n=== All tools demonstrated successfully! ===")

    except Exception as e:
        logging.error("Error demonstrating tools: %s", e, exc_info=True)

    finally:
        # Cleanup
        await server.cleanup()
        logging.info("Browser closed")


def main() -> None:
    """Main entry point."""
    # Configure logging to stderr (stdout is used for MCP communication)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stderr)],
    )

    # Parse command line arguments
    mode = sys.argv[1] if len(sys.argv) > 1 else "headless"

    if mode == "demo":
        # Demonstrate tools (for testing)
        asyncio.run(demonstrate_tools())
    elif mode == "headed":
        # Run server with visible browser
        asyncio.run(run_server_with_headed_browser())
    elif mode == "firefox":
        # Run server with Firefox
        asyncio.run(run_server_with_firefox())
    else:
        # Default: Run server with headless browser
        asyncio.run(run_server_with_headless_browser())


if __name__ == "__main__":
    main()
