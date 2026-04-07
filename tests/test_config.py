"""Tests for configuration system."""

import os
from pathlib import Path

from uitestflow.core.config import Config, UITestFlowSettings, get_config


class TestUITestFlowSettings:
    """Test settings class."""

    def test_settings_defaults(self):
        """Test default settings values."""
        settings = UITestFlowSettings()
        assert settings.environment == "development"
        assert settings.debug is False
        assert settings.browser_headless is True

    def test_settings_from_env(self):
        """Test loading settings from environment."""
        os.environ["UITESTFLOW_ENV"] = "production"
        os.environ["DEBUG"] = "true"

        settings = UITestFlowSettings()
        assert settings.environment == "production"
        assert settings.debug is True

        # Cleanup
        del os.environ["UITESTFLOW_ENV"]
        del os.environ["DEBUG"]


class TestConfig:
    """Test Config class."""

    def test_config_initialization(self):
        """Test config initialization."""
        config = Config()
        assert config.settings is not None

    def test_config_get_default(self):
        """Test getting config value with default."""
        config = Config()
        value = config.get("nonexistent_key", "default_value")
        assert value == "default_value"

    def test_config_set_and_get(self):
        """Test setting and getting config values."""
        config = Config()
        config.set("test_key", "test_value")
        assert config.get("test_key") == "test_value"

    def test_config_singleton(self):
        """Test config singleton pattern."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_config_with_profile(self, sample_profile_yaml):
        """Test config with profile loaded."""
        # Set profile file location
        profile_dir = Path(sample_profile_yaml).parent
        os.chdir(profile_dir)

        config = Config(profile_name="local")
        assert config.profile is not None
        assert config.profile.name == "Local Development"
        assert config.profile.base_url == "http://localhost:8080"

    def test_config_validation(self):
        """Test config validation."""
        config = Config()
        # Should not raise with valid config
        config.validate()

    def test_config_to_dict(self):
        """Test config serialization to dict."""
        config = Config()
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "settings" in config_dict
