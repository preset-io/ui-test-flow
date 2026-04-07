"""
Profiles screen for UITestFlow TUI.

Manage test profiles and configurations.
"""

import time

import httpx
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from ...core.profiles import ProfileManager


class ProfilesScreen(Screen):
    """Profile management screen."""

    BINDINGS = [
        ("t", "test_profile", "Test Connection"),
        ("r", "refresh", "Refresh"),
        ("q", "app.quit_screen", "Back"),
    ]

    def __init__(self):
        """Initialize the profiles screen."""
        super().__init__()
        self.selected_profile_id: str | None = None
        self.test_results: dict[str, dict] = {}
        self.testing_profile: str | None = None

    DEFAULT_CSS = """
    ProfilesScreen {
        background: $surface;
    }

    #profiles-container {
        width: 100%;
        height: 100%;
        padding: 2;
    }

    .profile-card {
        border: solid $border;
        background: $panel;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .profile-card-selected {
        border: solid $primary;
        background: $panel;
        padding: 1;
        margin: 1;
        height: auto;
    }

    .profile-name {
        text-style: bold;
        color: $primary;
    }

    .profile-detail {
        color: $text-muted;
    }

    .test-result {
        margin-top: 1;
    }

    #controls {
        height: auto;
        padding: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose profiles layout."""
        with VerticalScroll(id="profiles-container"):
            yield Label("Test Profiles", classes="panel-title")
            yield Label("Manage environment configurations and settings", classes="muted")
            yield Label("")

            # Load and display profiles
            yield from self._compose_profiles()

        # Controls
        with Horizontal(id="controls"):
            yield Button("Test Connection", id="btn_test")
            yield Button("Refresh", id="btn_refresh")
            yield Button("Back", id="btn_back")

    def _compose_profiles(self) -> ComposeResult:
        """Compose profile cards."""
        try:
            pm = ProfileManager()

            if not pm.has_profiles():
                yield Static(
                    "[yellow]No profiles configured[/yellow]\n\n"
                    "Create .uitest_profiles.yaml in your project root.",
                    classes="profile-card",
                )
                return

            for profile_id in pm.list_profiles():
                profile = pm.get_profile(profile_id)

                # Auto-select first profile if none selected
                if self.selected_profile_id is None:
                    self.selected_profile_id = profile_id

                is_selected = self.selected_profile_id == profile_id
                card_style = "profile-card-selected" if is_selected else "profile-card"

                with Container(classes=card_style, id=f"profile-{profile_id}"):
                    yield Label(profile.name, classes="profile-name")
                    yield Static(f"ID: {profile_id}", classes="profile-detail")
                    yield Static(f"URL: {profile.base_url}", classes="profile-detail")
                    yield Static(
                        f"Browser: {profile.browser.browser_type.value}",
                        classes="profile-detail",
                    )
                    yield Static(f"Headless: {profile.browser.headless}", classes="profile-detail")

                    if profile.is_default:
                        yield Static("[green]✓ Default Profile[/green]")

                    # Show test result if available
                    if profile_id in self.test_results:
                        result = self.test_results[profile_id]
                        if result.get("success"):
                            latency = result.get("latency_ms", "?")
                            yield Static(
                                f"[green]✓ Connected ({latency}ms)[/green]", classes="test-result"
                            )
                        else:
                            error = result.get("error", "Unknown error")
                            yield Static(f"[red]✗ Failed: {error}[/red]", classes="test-result")
                    elif self.testing_profile == profile_id:
                        yield Static(
                            "[yellow]⟳ Testing connection...[/yellow]", classes="test-result"
                        )

        except Exception as e:
            yield Static(f"[red]Error loading profiles: {e}[/red]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn_test":
            self.action_test_profile()
        elif button_id == "btn_refresh":
            self.action_refresh()
        elif button_id == "btn_back":
            self.app.pop_screen()

    def action_test_profile(self) -> None:
        """Test profile connection."""
        if not self.selected_profile_id:
            self.notify("No profile selected", severity="warning", timeout=2)
            return

        # Start async test
        self.run_worker(
            self._test_profile_async(self.selected_profile_id),
            exclusive=True,
        )

    async def _test_profile_async(self, profile_id: str) -> None:
        """Test profile connectivity asynchronously.

        Args:
            profile_id: Profile ID to test
        """
        try:
            pm = ProfileManager()
            profile = pm.get_profile(profile_id)

            # Update UI to show testing state
            self.testing_profile = profile_id
            self.notify(f"Testing {profile.name}...", timeout=1)
            await self.refresh_bindings()

            # Perform connectivity test
            start_time = time.time()

            try:
                timeout = httpx.Timeout(10.0, connect=5.0)
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.get(profile.base_url)
                    latency_ms = int((time.time() - start_time) * 1000)

                    if response.status_code < 400:
                        self.test_results[profile_id] = {
                            "success": True,
                            "latency_ms": latency_ms,
                            "error": None,
                        }
                        self.notify(
                            f"✓ Connected to {profile.name} ({latency_ms}ms)",
                            severity="information",
                            timeout=3,
                        )
                    else:
                        error_msg = f"HTTP {response.status_code}"
                        self.test_results[profile_id] = {
                            "success": False,
                            "latency_ms": latency_ms,
                            "error": error_msg,
                        }
                        self.notify(
                            f"✗ {profile.name} failed: {error_msg}",
                            severity="error",
                            timeout=5,
                        )

            except httpx.TimeoutException:
                latency_ms = int((time.time() - start_time) * 1000)
                error_msg = "Connection timeout (10s)"
                self.test_results[profile_id] = {
                    "success": False,
                    "latency_ms": latency_ms,
                    "error": error_msg,
                }
                self.notify(
                    f"✗ {profile.name} failed: {error_msg}",
                    severity="error",
                    timeout=5,
                )
            except httpx.ConnectError as e:
                latency_ms = int((time.time() - start_time) * 1000)
                error_msg = f"Connection failed: {e!s}"
                self.test_results[profile_id] = {
                    "success": False,
                    "latency_ms": latency_ms,
                    "error": error_msg,
                }
                self.notify(
                    f"✗ {profile.name} failed: Connection error",
                    severity="error",
                    timeout=5,
                )
            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                error_msg = f"Test failed: {e!s}"
                self.test_results[profile_id] = {
                    "success": False,
                    "latency_ms": latency_ms,
                    "error": error_msg,
                }
                self.notify(
                    f"✗ {profile.name} failed: {e!s}",
                    severity="error",
                    timeout=5,
                )

        except Exception as e:
            self.notify(f"Error: {e!s}", severity="error", timeout=5)
        finally:
            self.testing_profile = None
            self.action_refresh()

    def action_refresh(self) -> None:
        """Refresh profiles."""
        self.refresh()
        self.notify("Refreshed", timeout=1)
