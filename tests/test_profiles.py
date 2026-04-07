"""Tests for profile management."""

import os
from pathlib import Path

import pytest

from uitestflow.core.exceptions import ProfileNotFoundError
from uitestflow.core.profiles import Profile, ProfileManager


class TestProfile:
    """Test Profile model."""

    def test_profile_creation(self):
        """Test creating a profile."""
        profile = Profile(id="local", name="Local Development", base_url="http://localhost:8080")
        assert profile.id == "local"
        assert profile.name == "Local Development"

    def test_profile_with_auth(self):
        """Test profile with authentication config."""
        from uitestflow.core.models import AuthConfig, AuthType

        profile = Profile(
            id="staging",
            name="Staging",
            base_url="https://staging.example.com",
            auth=AuthConfig(type=AuthType.BEARER, token="test-token"),
        )
        assert profile.auth is not None
        assert profile.auth.type == AuthType.BEARER


class TestProfileManager:
    """Test ProfileManager class."""

    def test_load_profiles(self, sample_profile_yaml):
        """Test loading profiles from YAML."""
        profile_dir = Path(sample_profile_yaml).parent
        manager = ProfileManager(config_path=sample_profile_yaml)

        assert len(manager.profiles) == 2
        assert "local" in manager.profiles
        assert "staging" in manager.profiles

    def test_get_profile(self, sample_profile_yaml):
        """Test getting a profile by ID."""
        manager = ProfileManager(config_path=sample_profile_yaml)

        profile = manager.get_profile("local")
        assert profile.id == "local"
        assert profile.name == "Local Development"

    def test_get_nonexistent_profile(self, sample_profile_yaml):
        """Test getting a profile that doesn't exist."""
        manager = ProfileManager(config_path=sample_profile_yaml)

        with pytest.raises(ProfileNotFoundError):
            manager.get_profile("nonexistent")

    def test_get_default_profile(self, sample_profile_yaml):
        """Test getting the default profile."""
        manager = ProfileManager(config_path=sample_profile_yaml)

        profile = manager.get_default_profile()
        assert profile.id == "local"

    def test_list_profiles(self, sample_profile_yaml):
        """Test listing all profiles."""
        manager = ProfileManager(config_path=sample_profile_yaml)

        profiles = manager.list_profiles()
        assert len(profiles) == 2
        assert all(isinstance(p, Profile) for p in profiles)

    def test_validate_profile(self, sample_profile_yaml):
        """Test profile validation."""
        manager = ProfileManager(config_path=sample_profile_yaml)

        profile = manager.get_profile("local")
        # Should not raise
        manager.validate_profile(profile)

    def test_env_var_substitution(self, tmp_path):
        """Test environment variable substitution in profiles."""
        os.environ["TEST_TOKEN"] = "secret-token-123"

        yaml_content = """default: test

profiles:
  test:
    name: "Test Profile"
    base_url: "https://test.example.com"
    auth:
      type: "bearer"
      token: "${TEST_TOKEN}"
"""
        yaml_file = tmp_path / ".uitest_profiles.yaml"
        yaml_file.write_text(yaml_content)

        manager = ProfileManager(config_path=str(yaml_file))
        profile = manager.get_profile("test")

        assert profile.auth.token == "secret-token-123"

        # Cleanup
        del os.environ["TEST_TOKEN"]
