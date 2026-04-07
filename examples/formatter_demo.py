"""
Demo script showing how to use UITestFlow OutputFormatter.
"""

from datetime import datetime
from pathlib import Path

from uitestflow.formatters import OutputFormatter


def create_sample_results():
    """Create sample test results."""
    return {
        "test_name": "Login and Dashboard Test",
        "status": "passed",
        "duration_ms": 3500,
        "timestamp": datetime.now().isoformat(),
        "steps": [
            {"name": "Navigate to login page", "status": "passed", "duration_ms": 800},
            {"name": "Enter username", "status": "passed", "duration_ms": 200},
            {"name": "Enter password", "status": "passed", "duration_ms": 200},
            {"name": "Click login button", "status": "passed", "duration_ms": 500},
            {"name": "Wait for dashboard", "status": "passed", "duration_ms": 1200},
            {"name": "Verify user menu", "status": "passed", "duration_ms": 600},
        ],
        "evaluators": [
            {
                "name": "execution_successful",
                "passed": True,
                "score": 1.0,
                "reason": "All steps completed successfully",
            },
            {
                "name": "all_steps_completed",
                "passed": True,
                "score": 1.0,
                "reason": "All 6 steps were executed",
            },
            {
                "name": "no_console_errors",
                "passed": True,
                "score": 1.0,
                "reason": "No console errors found (checked 15 log entries)",
            },
            {
                "name": "within_time_limit",
                "passed": True,
                "score": 0.85,
                "reason": "Test completed in 3500ms (limit: 5000ms)",
            },
        ],
        "screenshots": [
            "screenshots/login_page.png",
            "screenshots/credentials_entered.png",
            "screenshots/dashboard_loaded.png",
            "screenshots/user_menu_visible.png",
        ],
        "errors": [],
    }


def demo_json_format():
    """Demo JSON formatting."""
    print("\n=== JSON Format ===")
    results = create_sample_results()
    formatter = OutputFormatter(results)

    json_output = formatter.format_json(pretty=True)
    print(json_output[:500] + "...\n")  # Show first 500 chars


def demo_yaml_format():
    """Demo YAML formatting."""
    print("\n=== YAML Format ===")
    results = create_sample_results()
    formatter = OutputFormatter(results)

    yaml_output = formatter.format_yaml()
    print(yaml_output[:500] + "...\n")  # Show first 500 chars


def demo_table_format():
    """Demo table formatting."""
    print("\n=== Table Format (Rich) ===")
    results = create_sample_results()
    formatter = OutputFormatter(results)

    formatter.format_table(detailed=True)


def demo_html_format():
    """Demo HTML report generation."""
    print("\n=== HTML Format ===")
    results = create_sample_results()
    formatter = OutputFormatter(results)

    output_path = Path("/tmp/uitestflow_demo_report.html")
    html_path = formatter.format_html(output_path)
    print(f"HTML report generated: {html_path}")
    print(f"File size: {output_path.stat().st_size} bytes")


def demo_save_formats():
    """Demo saving in different formats."""
    print("\n=== Saving to Files ===")
    results = create_sample_results()
    formatter = OutputFormatter(results)

    # Save JSON
    json_path = formatter.save("/tmp/test_results.json", format="json")
    print(f"✓ JSON saved: {json_path}")

    # Save YAML
    yaml_path = formatter.save("/tmp/test_results.yaml", format="yaml")
    print(f"✓ YAML saved: {yaml_path}")

    # Save HTML
    html_path = formatter.save("/tmp/test_results.html", format="html")
    print(f"✓ HTML saved: {html_path}")


if __name__ == "__main__":
    print("UITestFlow OutputFormatter Demo")
    print("=" * 70)

    demo_json_format()
    demo_yaml_format()
    demo_table_format()
    demo_html_format()
    demo_save_formats()

    print("\n" + "=" * 70)
    print("Demo completed!")
