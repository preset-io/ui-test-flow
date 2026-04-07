"""
Output formatter for UITestFlow test results.

Provides multiple output formats including JSON, YAML, table, and HTML reports.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class OutputFormatter:
    """Format test results for various output types."""

    def __init__(self, test_results: dict[str, Any]):
        """
        Initialize formatter with test results.

        Args:
            test_results: Dictionary containing:
                - test_name: Name of the test
                - status: Test status (passed/failed)
                - duration_ms: Test duration in milliseconds
                - steps: List of test steps
                - evaluators: List of evaluator results
                - screenshots: List of screenshot paths
                - errors: List of errors
                - timestamp: Test execution timestamp
        """
        self.results = test_results
        self.console = Console()

    def format_json(self, pretty: bool = True) -> str:
        """
        Format results as JSON.

        Args:
            pretty: Whether to pretty-print JSON (default: True)

        Returns:
            JSON string
        """
        if pretty:
            return json.dumps(self.results, indent=2, default=str)
        return json.dumps(self.results, default=str)

    def format_yaml(self) -> str:
        """
        Format results as YAML.

        Returns:
            YAML string
        """
        return yaml.dump(self.results, default_flow_style=False, sort_keys=False)

    def format_table(self, detailed: bool = False) -> None:
        """
        Format results as Rich table and print to console.

        Args:
            detailed: Whether to show detailed information (default: False)
        """
        # Overall status
        status = self.results.get("status", "unknown")
        test_name = self.results.get("test_name", "Unnamed Test")
        duration_ms = self.results.get("duration_ms", 0)
        timestamp = self.results.get("timestamp", datetime.now())

        status_emoji = "✓" if status == "passed" else "✗"
        status_color = "green" if status == "passed" else "red"

        # Header panel
        header = f"[bold]{status_emoji} Test: {test_name}[/bold]\n"
        header += f"Status: [{status_color}]{status.upper()}[/{status_color}]\n"
        header += f"Duration: {duration_ms}ms\n"
        header += f"Time: {timestamp}"

        self.console.print(Panel(header, border_style=status_color))

        # Steps table
        if detailed or status == "failed":
            steps = self.results.get("steps", [])
            if steps:
                steps_table = Table(title="Test Steps", show_header=True)
                steps_table.add_column("Step", style="cyan")
                steps_table.add_column("Status", style="bold")
                steps_table.add_column("Duration", justify="right")

                for step in steps:
                    step_name = step.get("name", "Unknown")
                    step_status = step.get("status", "unknown")
                    step_duration = step.get("duration_ms", 0)

                    status_icon = "✓" if step_status == "passed" else "✗"
                    status_style = "green" if step_status == "passed" else "red"

                    steps_table.add_row(
                        step_name,
                        f"[{status_style}]{status_icon} {step_status}[/{status_style}]",
                        f"{step_duration}ms",
                    )

                self.console.print(steps_table)

        # Evaluators table
        evaluators = self.results.get("evaluators", [])
        if evaluators:
            eval_table = Table(title="Evaluators", show_header=True)
            eval_table.add_column("Evaluator", style="cyan")
            eval_table.add_column("Result", style="bold")
            eval_table.add_column("Score", justify="right")
            eval_table.add_column("Reason")

            for evaluator in evaluators:
                eval_name = evaluator.get("name", "Unknown")
                eval_passed = evaluator.get("passed", False)
                eval_score = evaluator.get("score", 0.0)
                eval_reason = evaluator.get("reason", "")

                result_icon = "✓" if eval_passed else "✗"
                result_style = "green" if eval_passed else "red"

                eval_table.add_row(
                    eval_name,
                    f"[{result_style}]{result_icon} {'PASS' if eval_passed else 'FAIL'}[/{result_style}]",
                    f"{eval_score:.2f}",
                    eval_reason[:50] + "..." if len(eval_reason) > 50 else eval_reason,
                )

            self.console.print(eval_table)

        # Screenshots
        screenshots = self.results.get("screenshots", [])
        if screenshots:
            self.console.print(f"\n[bold cyan]Screenshots:[/bold cyan] {len(screenshots)} captured")
            if detailed:
                for i, screenshot in enumerate(screenshots[:5], 1):
                    self.console.print(f"  {i}. {screenshot}")
                if len(screenshots) > 5:
                    self.console.print(f"  ... and {len(screenshots) - 5} more")

        # Errors
        errors = self.results.get("errors", [])
        if errors:
            self.console.print(f"\n[bold red]Errors:[/bold red] {len(errors)} occurred")
            for i, error in enumerate(errors[:3], 1):
                error_msg = error if isinstance(error, str) else error.get("message", str(error))
                self.console.print(f"  {i}. {error_msg}")
            if len(errors) > 3:
                self.console.print(f"  ... and {len(errors) - 3} more")

    def format_html(self, output_path: Path | str) -> str:
        """
        Generate HTML report.

        Args:
            output_path: Path to save HTML report

        Returns:
            Path to generated HTML file
        """
        output_path = Path(output_path)

        test_name = self.results.get("test_name", "UI Test")
        status = self.results.get("status", "unknown")
        duration_ms = self.results.get("duration_ms", 0)
        timestamp = self.results.get("timestamp", datetime.now())
        steps = self.results.get("steps", [])
        evaluators = self.results.get("evaluators", [])
        screenshots = self.results.get("screenshots", [])
        errors = self.results.get("errors", [])

        status_color = "#22c55e" if status == "passed" else "#ef4444"
        status_icon = "✓" if status == "passed" else "✗"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{test_name} - Test Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: {status_color};
            color: white;
            padding: 30px;
        }}
        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .meta {{
            opacity: 0.95;
            font-size: 14px;
        }}
        .content {{
            padding: 30px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            font-size: 20px;
            margin-bottom: 15px;
            color: #555;
            border-bottom: 2px solid #e5e5e5;
            padding-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e5e5;
        }}
        th {{
            background: #f8f8f8;
            font-weight: 600;
            color: #555;
        }}
        .status-pass {{ color: #22c55e; font-weight: bold; }}
        .status-fail {{ color: #ef4444; font-weight: bold; }}
        .screenshot {{
            max-width: 100%;
            border: 1px solid #e5e5e5;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .error {{
            background: #fef2f2;
            border-left: 4px solid #ef4444;
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-success {{ background: #dcfce7; color: #166534; }}
        .badge-error {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{status_icon} {test_name}</h1>
            <div class="meta">
                Status: {status.upper()} |
                Duration: {duration_ms}ms |
                Time: {timestamp}
            </div>
        </div>
        <div class="content">
"""

        # Steps section
        if steps:
            html += """
            <div class="section">
                <h2>Test Steps</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Step</th>
                            <th>Status</th>
                            <th>Duration</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for step in steps:
                step_name = step.get("name", "Unknown")
                step_status = step.get("status", "unknown")
                step_duration = step.get("duration_ms", 0)
                status_class = "status-pass" if step_status == "passed" else "status-fail"
                status_text = "✓ PASS" if step_status == "passed" else "✗ FAIL"

                html += f"""
                        <tr>
                            <td>{step_name}</td>
                            <td class="{status_class}">{status_text}</td>
                            <td>{step_duration}ms</td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
            </div>
"""

        # Evaluators section
        if evaluators:
            html += """
            <div class="section">
                <h2>Evaluators</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Evaluator</th>
                            <th>Result</th>
                            <th>Score</th>
                            <th>Reason</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for evaluator in evaluators:
                eval_name = evaluator.get("name", "Unknown")
                eval_passed = evaluator.get("passed", False)
                eval_score = evaluator.get("score", 0.0)
                eval_reason = evaluator.get("reason", "")
                status_class = "status-pass" if eval_passed else "status-fail"
                status_text = "✓ PASS" if eval_passed else "✗ FAIL"

                html += f"""
                        <tr>
                            <td>{eval_name}</td>
                            <td class="{status_class}">{status_text}</td>
                            <td>{eval_score:.2f}</td>
                            <td>{eval_reason}</td>
                        </tr>
"""
            html += """
                    </tbody>
                </table>
            </div>
"""

        # Screenshots section
        if screenshots:
            html += f"""
            <div class="section">
                <h2>Screenshots ({len(screenshots)})</h2>
"""
            for screenshot in screenshots:
                html += f'<img src="{screenshot}" class="screenshot" alt="Test screenshot">\n'
            html += """
            </div>
"""

        # Errors section
        if errors:
            html += f"""
            <div class="section">
                <h2>Errors ({len(errors)})</h2>
"""
            for error in errors:
                error_msg = error if isinstance(error, str) else error.get("message", str(error))
                html += f'<div class="error">{error_msg}</div>\n'
            html += """
            </div>
"""

        html += """
        </div>
    </div>
</body>
</html>
"""

        # Write HTML file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")

        return str(output_path)

    def save(self, output_path: Path | str, format: str = "json") -> str:
        """
        Save results to file in specified format.

        Args:
            output_path: Path to save output
            format: Output format (json, yaml, html)

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)

        if format == "json":
            output_path.write_text(self.format_json(), encoding="utf-8")
        elif format == "yaml":
            output_path.write_text(self.format_yaml(), encoding="utf-8")
        elif format == "html":
            return self.format_html(output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return str(output_path)
