#!/usr/bin/env python3
"""
Example script demonstrating the UITestFlow configuration and profile system.

This script shows how to:
1. Load profiles from .uitest_profiles.yaml
2. Create test definitions
3. Access configuration values
"""

import sys
from pathlib import Path


# Add parent directory to path so we can import uitestflow
sys.path.insert(0, str(Path(__file__).parent.parent))

from uitestflow.core import (
    ActionType,
    EvaluatorConfig,
    EvaluatorType,
    ProfileManager,
    TestDefinition,
    TestStep,
    init_config,
    load_profile,
)


def demo_profile_loading():
    """Demonstrate profile loading and management."""
    print("\n" + "=" * 80)
    print("DEMO: Profile Loading and Management")
    print("=" * 80)

    # Initialize profile manager (will find .uitest_profiles.yaml in current dir)
    manager = ProfileManager()

    print(f"\nAvailable profiles: {manager.list_profiles()}")
    print(f"Default profile: {manager.get_default_profile_id()}")

    # Load and display each profile
    for profile_id in manager.list_profiles():
        print(f"\n--- Profile: {profile_id} ---")
        profile = manager.get_profile(profile_id)
        print(f"Name: {profile.name}")
        print(f"Description: {profile.description}")
        print(f"Base URL: {profile.base_url}")
        print(f"Auth Type: {profile.auth.auth_type.value}")
        print(f"Browser: {profile.browser.browser_type.value}")
        print(f"Headless: {profile.browser.headless}")
        print(f"Viewport: {profile.browser.viewport.width}x{profile.browser.viewport.height}")

        # Validate profile
        errors = manager.validate_profile(profile_id)
        if errors:
            print(f"Validation errors: {errors}")
        else:
            print("Validation: OK")


def demo_config_hierarchy():
    """Demonstrate configuration hierarchy and overrides."""
    print("\n" + "=" * 80)
    print("DEMO: Configuration Hierarchy")
    print("=" * 80)

    # Initialize config with a profile (using local which doesn't require env vars)
    config = init_config(profile="local", headless=False)

    print("\nConfiguration sources:")
    for key, (value, source) in config.get_all_with_sources().items():
        # Only show interesting keys
        if key in ["profile", "base_url", "headless", "browser", "auth"]:
            print(f"  {key}: {source}")

    print(f"\nBase URL: {config.base_url}")
    print(f"Profile ID: {config.profile_id}")
    print(f"Headless override: {config.get('headless')}")


def demo_test_definition():
    """Demonstrate creating a test definition."""
    print("\n" + "=" * 80)
    print("DEMO: Test Definition Creation")
    print("=" * 80)

    # Create a simple test definition
    test = TestDefinition(
        name="Login and Navigate Test",
        description="Test login functionality and dashboard navigation",
        url="http://localhost:8080",
        steps=[
            TestStep(
                name="Navigate to login page",
                action=ActionType.GOTO,
                url="http://localhost:8080/login",
                screenshot=True,
            ),
            TestStep(
                name="Enter username",
                action=ActionType.FILL,
                selector='input[name="username"]',
                value="admin",
            ),
            TestStep(
                name="Enter password",
                action=ActionType.FILL,
                selector='input[name="password"]',
                value="admin",
            ),
            TestStep(
                name="Click login button",
                action=ActionType.CLICK,
                selector='button[type="submit"]',
                screenshot=True,
            ),
            TestStep(
                name="Wait for dashboard",
                action=ActionType.WAIT_FOR,
                selector=".dashboard-container",
                timeout=10000,
                screenshot=True,
            ),
        ],
        evaluators=[
            EvaluatorConfig(
                name="all_steps_completed",
                evaluator_type=EvaluatorType.ALL_STEPS_COMPLETED,
            ),
            EvaluatorConfig(
                name="no_console_errors",
                evaluator_type=EvaluatorType.NO_CONSOLE_ERRORS,
            ),
            EvaluatorConfig(
                name="page_load_time",
                evaluator_type=EvaluatorType.PAGE_LOAD_TIME,
                params={"max_ms": 5000},
            ),
        ],
        tags=["login", "smoke-test", "critical"],
    )

    print(f"\nTest created: {test.name}")
    print(f"Test ID: {test.id}")
    print(f"Steps: {len(test.steps)}")
    print(f"Evaluators: {len(test.evaluators)}")
    print(f"Tags: {', '.join(test.tags)}")

    print("\nTest steps:")
    for i, step in enumerate(test.steps, 1):
        print(f"  {i}. {step.name} ({step.action.value})")

    print("\nEvaluators:")
    for evaluator in test.evaluators:
        print(f"  - {evaluator.name} ({evaluator.evaluator_type.value})")

    # Serialize to JSON
    test_json = test.model_dump_json(indent=2)
    print("\nJSON representation (first 500 chars):")
    print(test_json[:500] + "...")


def demo_profile_with_test():
    """Demonstrate using a profile with a test definition."""
    print("\n" + "=" * 80)
    print("DEMO: Profile + Test Definition")
    print("=" * 80)

    # Load a profile
    profile = load_profile("local")
    print(f"\nLoaded profile: {profile.name}")
    print(f"Base URL from profile: {profile.base_url}")

    # Create test that will use profile settings
    test = TestDefinition(
        name="Dashboard Smoke Test",
        description="Quick smoke test of dashboard functionality",
        # URL will be overridden by profile
        steps=[
            TestStep(
                name="Navigate to home",
                action=ActionType.GOTO,
                url=f"{profile.base_url}/",
            ),
            TestStep(
                name="Check for dashboard element",
                action=ActionType.WAIT_FOR,
                selector=".dashboard",
                timeout=profile.timeout,
            ),
        ],
        evaluators=[
            EvaluatorConfig(
                name="all_steps_completed",
                evaluator_type=EvaluatorType.ALL_STEPS_COMPLETED,
            ),
        ],
        browser_config=profile.browser,
        auth_config=profile.auth,
    )

    print(f"\nTest: {test.name}")
    print(f"Using browser: {test.browser_config.browser_type.value}")
    print(f"Headless: {test.browser_config.headless}")
    print(f"Auth type: {test.auth_config.auth_type.value}")
    print(f"Step timeout: {test.steps[1].timeout}ms")


def main():
    """Run all demos."""
    print("\n" + "=" * 80)
    print("UITestFlow Configuration System Demo")
    print("=" * 80)

    try:
        demo_profile_loading()
        demo_config_hierarchy()
        demo_test_definition()
        demo_profile_with_test()

        print("\n" + "=" * 80)
        print("All demos completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
