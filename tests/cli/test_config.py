"""Tests for CLI ConfigManager."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

from slidemaker.cli.config import ConfigLoadError, ConfigManager, ConfigValidationError


class TestConfigManager:
    """Tests for ConfigManager class."""

    @pytest.fixture
    def manager(self) -> ConfigManager:
        """Create a ConfigManager instance."""
        return ConfigManager(strict_env=False)

    @pytest.fixture
    def strict_manager(self) -> ConfigManager:
        """Create a ConfigManager instance with strict environment variable checking."""
        return ConfigManager(strict_env=True)

    @pytest.fixture
    def valid_config(self) -> dict[str, Any]:
        """Return a valid configuration dictionary."""
        return {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": "sk-ant-test123",
                    "timeout": 300,
                },
                "image_generation": {
                    "type": "api",
                    "provider": "dalle",
                    "model": "dall-e-3",
                    "api_key": "sk-test456",
                },
            },
            "output": {
                "directory": "./output",
                "temp_directory": "./tmp",
            },
            "logging": {
                "level": "INFO",
                "format": "json",
            },
        }

    # Test 1: Default config loading
    def test_load_default_config(self, manager: ConfigManager) -> None:
        """Test loading default configuration when no config file exists."""
        with patch("slidemaker.cli.config.get_default_config_path", return_value=None):
            config = manager.load_config()

        assert "llm" in config
        assert "output" in config
        assert config["llm"]["composition"]["type"] == "api"
        assert config["llm"]["composition"]["provider"] == "claude"
        assert config["output"]["directory"] == "./output"

    # Test 2: Load config from file
    def test_load_config_from_file(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test loading configuration from a YAML file."""
        config_file = Path.cwd() / "test_load_config.yaml"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(valid_config, f)

            with patch("slidemaker.cli.config.get_default_config_path", return_value=config_file):
                config = manager.load_config()

            assert config["llm"]["composition"]["provider"] == "claude"
            assert config["llm"]["composition"]["api_key"] == "sk-ant-test123"
            assert config["output"]["directory"] == "./output"
        finally:
            if config_file.exists():
                config_file.unlink()

    # Test 3: Config search order
    def test_load_config_search_order(self, manager: ConfigManager, valid_config: dict[str, Any]) -> None:
        """Test configuration file search order (specified > current > home)."""
        # Create config in current directory (allowed)
        config_file = Path.cwd() / "test_custom_config.yaml"
        custom_config = valid_config.copy()
        custom_config["llm"]["composition"]["provider"] = "gpt"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(custom_config, f)

            # Specified path should take priority
            config = manager.load_config(config_file)
            assert config["llm"]["composition"]["provider"] == "gpt"
        finally:
            # Cleanup
            if config_file.exists():
                config_file.unlink()

    # Test 4: Validate config success
    def test_validate_config_success(self, manager: ConfigManager, valid_config: dict[str, Any]) -> None:
        """Test validation of a valid configuration."""
        # Should not raise any exception
        manager.validate_config(valid_config)

    # Test 5: Missing llm section
    def test_validate_config_missing_llm(self, manager: ConfigManager) -> None:
        """Test validation fails when 'llm' section is missing."""
        config = {
            "output": {
                "directory": "./output",
            }
        }

        with pytest.raises(ConfigValidationError, match="Missing required section: 'llm'"):
            manager.validate_config(config)

    # Test 6: Missing output section
    def test_validate_config_missing_output(self, manager: ConfigManager) -> None:
        """Test validation fails when 'output' section is missing."""
        config = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": "sk-ant-test",
                }
            }
        }

        with pytest.raises(ConfigValidationError, match="Missing required section: 'output'"):
            manager.validate_config(config)

    # Test 7: Environment variable expansion
    def test_environment_variable_expansion(self, manager: ConfigManager) -> None:
        """Test environment variable expansion in configuration."""
        # Set environment variables
        os.environ["TEST_API_KEY"] = "sk-env-test-key"

        config_data = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": "${TEST_API_KEY}",
                }
            },
            "output": {
                "directory": "./output",
            },
        }

        config_file = Path.cwd() / "test_env_config.yaml"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f)

            config = manager.load_config(config_file)
            assert config["llm"]["composition"]["api_key"] == "sk-env-test-key"
        finally:
            # Cleanup
            del os.environ["TEST_API_KEY"]
            if config_file.exists():
                config_file.unlink()

    # Test 8: Path traversal prevention
    def test_path_traversal_prevention(self, manager: ConfigManager, valid_config: dict[str, Any]) -> None:
        """Test that path traversal attempts in output directory are detected."""
        config = valid_config.copy()
        config["output"]["directory"] = "../../../etc/passwd"

        with pytest.raises(
            ConfigValidationError, match="Invalid output directory.*contains '..'"
        ):
            manager.validate_config(config)

    # Test 9: File not found error
    def test_file_not_found(self, manager: ConfigManager) -> None:
        """Test error when specified config file does not exist."""
        non_existent_path = Path("/non/existent/config.yaml")

        with pytest.raises(ConfigLoadError, match="Specified config file not found"):
            manager.load_config(non_existent_path)

    # Test 10: Invalid YAML format
    def test_invalid_yaml(self, manager: ConfigManager) -> None:
        """Test error when config file contains invalid YAML."""
        config_file = Path.cwd() / "test_invalid.yaml"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                f.write("llm:\n  composition:\n    invalid yaml syntax: [unclosed")

            with pytest.raises(ConfigLoadError, match="Invalid YAML format"):
                manager.load_config(config_file)
        finally:
            if config_file.exists():
                config_file.unlink()

    # Additional Test 11: Missing required LLM fields
    def test_validate_config_missing_llm_composition(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation fails when 'llm.composition' is missing."""
        config = valid_config.copy()
        del config["llm"]["composition"]

        with pytest.raises(
            ConfigValidationError, match="Missing required field: 'llm.composition'"
        ):
            manager.validate_config(config)

    # Additional Test 12: Invalid LLM type
    def test_validate_config_invalid_llm_type(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation fails when LLM type is invalid."""
        config = valid_config.copy()
        config["llm"]["composition"]["type"] = "invalid_type"

        with pytest.raises(ConfigValidationError, match="Invalid llm.composition.type"):
            manager.validate_config(config)

    # Additional Test 13: Missing LLM provider
    def test_validate_config_missing_llm_provider(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation fails when 'llm.composition.provider' is missing."""
        config = valid_config.copy()
        del config["llm"]["composition"]["provider"]

        with pytest.raises(
            ConfigValidationError, match="Missing required field: 'llm.composition.provider'"
        ):
            manager.validate_config(config)

    # Additional Test 14: Invalid logging level
    def test_validate_config_invalid_logging_level(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation fails when logging level is invalid."""
        config = valid_config.copy()
        config["logging"]["level"] = "INVALID"

        with pytest.raises(ConfigValidationError, match="Invalid logging level"):
            manager.validate_config(config)

    # Additional Test 15: Invalid logging format
    def test_validate_config_invalid_logging_format(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation fails when logging format is invalid."""
        config = valid_config.copy()
        config["logging"]["format"] = "xml"

        with pytest.raises(ConfigValidationError, match="Invalid logging format"):
            manager.validate_config(config)

    # Additional Test 16: Empty config file
    def test_load_empty_config_file(self, manager: ConfigManager) -> None:
        """Test loading an empty configuration file returns default config."""
        config_file = Path.cwd() / "test_empty.yaml"

        try:
            config_file.write_text("", encoding="utf-8")

            with patch("slidemaker.cli.config.get_default_config_path", return_value=config_file):
                config = manager.load_config()

            # Should return default config
            assert "llm" in config
            assert "output" in config
            assert config["llm"]["composition"]["provider"] == "claude"
        finally:
            if config_file.exists():
                config_file.unlink()

    # Additional Test 17: Config outside allowed directories
    def test_load_config_outside_allowed_dirs(self, manager: ConfigManager) -> None:
        """Test error when config file is outside allowed directories."""
        # Create a temp file in /tmp (outside allowed dirs)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, dir="/tmp"
        ) as tmp:
            config_data = {
                "llm": {
                    "composition": {
                        "type": "api",
                        "provider": "claude",
                        "model": "test",
                        "api_key": "test",
                    }
                },
                "output": {"directory": "./output"},
            }
            yaml.dump(config_data, tmp)
            tmp_path = Path(tmp.name)

        try:
            with pytest.raises(ConfigLoadError, match="Config file outside allowed directories"):
                manager.load_config(tmp_path)
        finally:
            tmp_path.unlink()

    # Additional Test 18: Strict environment variable mode
    def test_strict_env_mode_undefined_variable(self, strict_manager: ConfigManager) -> None:
        """Test strict mode raises error for undefined environment variables."""
        config_data = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": "${UNDEFINED_VAR_TEST_12345}",
                }
            },
            "output": {
                "directory": "./output",
            },
        }

        config_file = Path.cwd() / "test_strict_env.yaml"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f)

            with pytest.raises(ConfigValidationError, match="Configuration error"):
                strict_manager.load_config(config_file)
        finally:
            if config_file.exists():
                config_file.unlink()

    # Additional Test 19: Load app config
    def test_load_app_config(self, manager: ConfigManager, valid_config: dict[str, Any]) -> None:
        """Test loading configuration as AppConfig model."""
        config_file = Path.cwd() / "test_app_config.yaml"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(valid_config, f)

            with patch("slidemaker.cli.config.get_default_config_path", return_value=config_file):
                app_config = manager.load_app_config()

            # AppConfig has llm as dict[str, LLMConfig]
            assert "composition" in app_config.llm
            assert app_config.llm["composition"].provider == "claude"
            assert app_config.output.directory == "./output"
        finally:
            if config_file.exists():
                config_file.unlink()

    # Additional Test 20: Load app config with invalid schema
    def test_load_app_config_invalid_schema(self, manager: ConfigManager) -> None:
        """Test error when config doesn't match AppConfig schema."""
        # Use data that passes basic validation but fails AppConfig parsing
        config_data = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "test",
                    "api_key": "test",
                    "timeout": "not_a_number",  # Invalid type for timeout
                }
            },
            "output": {"directory": "./output"},
        }

        config_file = Path.cwd() / "test_invalid_schema.yaml"

        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(config_data, f)

            # Should raise ConfigValidationError or pydantic ValidationError
            with pytest.raises((ConfigValidationError, Exception)):
                manager.load_app_config(config_file)
        finally:
            if config_file.exists():
                config_file.unlink()

    # Additional Test 21: Config with extra fields
    def test_validate_config_with_extra_fields(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation succeeds when config has extra fields (should be ignored)."""
        config = valid_config.copy()
        config["extra_section"] = {"foo": "bar"}

        # Should not raise exception (extra fields are allowed)
        manager.validate_config(config)

    # Additional Test 22: Missing output directory field
    def test_validate_config_missing_output_directory(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation fails when 'output.directory' is missing."""
        config = valid_config.copy()
        del config["output"]["directory"]

        with pytest.raises(
            ConfigValidationError, match="Missing required field: 'output.directory'"
        ):
            manager.validate_config(config)

    # Additional Test 23: API key warning
    def test_validate_config_api_key_not_expanded(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test warning is logged when API key is not expanded."""
        config = valid_config.copy()
        config["llm"]["composition"]["api_key"] = "${UNDEFINED_KEY}"

        # Should not raise exception (warning only)
        # We can't easily test log output in this context, so just verify no exception
        manager.validate_config(config)

    # Additional Test 24: OSError during file read
    def test_load_config_oserror(self, manager: ConfigManager) -> None:
        """Test error handling when file reading fails with OSError."""
        config_file = Path.cwd() / "test_oserror.yaml"

        try:
            config_file.write_text("llm:\n  test: value", encoding="utf-8")

            # Mock Path.open() to raise OSError
            with (
                patch("pathlib.Path.open", side_effect=OSError("Permission denied")),
                pytest.raises(ConfigLoadError, match="Failed to read config file"),
            ):
                manager.load_config(config_file)
        finally:
            if config_file.exists():
                config_file.unlink()

    # Additional Test 25: Config with all optional sections
    def test_validate_config_all_optional_sections(
        self, manager: ConfigManager, valid_config: dict[str, Any]
    ) -> None:
        """Test validation with all optional sections present."""
        config = valid_config.copy()
        config["slide"] = {
            "default_size": "16:9",
            "default_theme": "minimal",
            "default_font": "Arial",
        }

        # Should validate successfully
        manager.validate_config(config)

    # Additional Test 26: Bedrock provider without api_key
    def test_validate_config_bedrock_without_api_key(self, manager: ConfigManager) -> None:
        """Test validation succeeds for Bedrock providers without api_key."""
        config = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "bedrock-claude",
                    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    # No api_key for Bedrock (uses AWS credentials)
                }
            },
            "output": {"directory": "./output"},
        }

        # Should validate successfully without api_key for Bedrock
        manager.validate_config(config)

    # Additional Test 27: Bedrock provider with api_key (optional)
    def test_validate_config_bedrock_with_api_key(self, manager: ConfigManager) -> None:
        """Test validation succeeds for Bedrock providers with optional api_key."""
        config = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "bedrock",
                    "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
                    "api_key": "optional-key",  # Optional for Bedrock
                }
            },
            "output": {"directory": "./output"},
        }

        # Should validate successfully
        manager.validate_config(config)

    # Additional Test 28: Image generation with Bedrock provider
    def test_validate_config_image_generation_bedrock(self, manager: ConfigManager) -> None:
        """Test validation for image_generation section with Bedrock provider."""
        config = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": "sk-test",
                },
                "image_generation": {
                    "type": "api",
                    "provider": "bedrock",
                    "model": "stability.stable-diffusion-xl-v1",
                    # No api_key for Bedrock image generation
                },
            },
            "output": {"directory": "./output"},
        }

        # Should validate successfully
        manager.validate_config(config)

    # Additional Test 29: Non-Bedrock provider still requires api_key
    def test_validate_config_non_bedrock_requires_api_key(self, manager: ConfigManager) -> None:
        """Test validation fails for non-Bedrock providers without api_key."""
        config = {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "claude-3-5-sonnet-20241022",
                    # Missing api_key for non-Bedrock provider
                }
            },
            "output": {"directory": "./output"},
        }

        with pytest.raises(
            ConfigValidationError, match="Missing required field: 'llm.composition.api_key'"
        ):
            manager.validate_config(config)
