"""Tests for YAML test parser."""

import os

import pytest

from uitestflow.core.exceptions import TestParseError
from uitestflow.src.test_parser import YAMLTestParser


class TestYAMLTestParser:
    """Test YAML test parser."""

    def test_parse_simple_test(self, sample_yaml_test):
        """Test parsing a simple YAML test."""
        parser = YAMLTestParser()
        test_def = parser.parse_file(sample_yaml_test)

        assert test_def.name == "Sample Test"
        assert test_def.version == "1.0"
        assert len(test_def.steps) == 2
        assert len(test_def.evaluators) == 2

    def test_parse_steps(self, sample_yaml_test):
        """Test parsing test steps."""
        parser = YAMLTestParser()
        test_def = parser.parse_file(sample_yaml_test)

        # Check first step
        step1 = test_def.steps[0]
        assert step1.name == "Navigate to page"
        assert step1.action.value == "goto"

        # Check second step
        step2 = test_def.steps[1]
        assert step2.name == "Check title"
        assert step2.action.value == "expect"

    def test_parse_evaluators(self, sample_yaml_test):
        """Test parsing evaluators."""
        parser = YAMLTestParser()
        test_def = parser.parse_file(sample_yaml_test)

        # Check evaluators
        assert test_def.evaluators[0].name == "execution_successful"
        assert test_def.evaluators[1].name == "within_time_limit"
        assert test_def.evaluators[1].args["max_duration_ms"] == 5000

    def test_env_var_substitution(self, tmp_path):
        """Test environment variable substitution."""
        # Set test env var
        os.environ["TEST_URL"] = "https://test.example.com"

        yaml_content = """version: "1.0"
name: "Env Test"
url: "${TEST_URL}"

steps:
  - name: "Navigate"
    action: "goto"
    url: "$TEST_URL"

evaluators:
  - name: "execution_successful"
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)

        parser = YAMLTestParser()
        test_def = parser.parse_file(str(yaml_file))

        assert test_def.url == "https://test.example.com"
        assert test_def.steps[0].url == "https://test.example.com"

        # Cleanup
        del os.environ["TEST_URL"]

    def test_parse_invalid_yaml(self, tmp_path):
        """Test parsing invalid YAML."""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text("invalid: yaml: content:")

        parser = YAMLTestParser()
        with pytest.raises(TestParseError):
            parser.parse_file(str(yaml_file))

    def test_parse_missing_required_fields(self, tmp_path):
        """Test parsing YAML with missing required fields."""
        yaml_content = """version: "1.0"
# Missing name field
steps: []
"""
        yaml_file = tmp_path / "missing_fields.yaml"
        yaml_file.write_text(yaml_content)

        parser = YAMLTestParser()
        with pytest.raises(TestParseError):
            parser.parse_file(str(yaml_file))

    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        parser = YAMLTestParser()
        with pytest.raises(TestParseError, match="not found"):
            parser.parse_file("/nonexistent/file.yaml")

    def test_parse_with_browser_config(self, tmp_path):
        """Test parsing test with browser configuration."""
        yaml_content = """version: "1.0"
name: "Browser Config Test"

browser:
  type: "firefox"
  headless: false
  viewport:
    width: 1280
    height: 720

steps:
  - name: "Navigate"
    action: "goto"
    url: "https://example.com"

evaluators:
  - name: "execution_successful"
"""
        yaml_file = tmp_path / "browser_config.yaml"
        yaml_file.write_text(yaml_content)

        parser = YAMLTestParser()
        test_def = parser.parse_file(str(yaml_file))

        assert test_def.browser_config is not None
        assert test_def.browser_config.type.value == "firefox"
        assert test_def.browser_config.headless is False
        assert test_def.browser_config.viewport.width == 1280

    def test_parse_with_auth_config(self, tmp_path):
        """Test parsing test with auth configuration."""
        yaml_content = """version: "1.0"
name: "Auth Config Test"

auth:
  type: "form"
  username: "testuser"
  password: "testpass"

steps:
  - name: "Navigate"
    action: "goto"
    url: "https://example.com"

evaluators:
  - name: "execution_successful"
"""
        yaml_file = tmp_path / "auth_config.yaml"
        yaml_file.write_text(yaml_content)

        parser = YAMLTestParser()
        test_def = parser.parse_file(str(yaml_file))

        assert test_def.auth_config is not None
        assert test_def.auth_config.type.value == "form"
        assert test_def.auth_config.username == "testuser"
