"""Unit tests for config_loader."""

import os
from pathlib import Path

import pytest

from slidemaker.utils.config_loader import AppConfig, expand_env_vars, load_config


class TestExpandEnvVars:
    """Tests for expand_env_vars function."""

    def test_expand_env_var_braces(self, monkeypatch):
        """Test expanding environment variable with ${VAR} syntax."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = expand_env_vars("${TEST_VAR}")
        assert result == "test_value"

    def test_expand_env_var_dollar(self, monkeypatch):
        """Test expanding environment variable with $VAR syntax."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = expand_env_vars("$TEST_VAR")
        assert result == "test_value"

    def test_expand_env_var_in_dict(self, monkeypatch):
        """Test expanding environment variables in dictionary."""
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")

        data = {"host": "${DB_HOST}", "port": "$DB_PORT", "name": "mydb"}
        result = expand_env_vars(data)

        assert result["host"] == "localhost"
        assert result["port"] == "5432"
        assert result["name"] == "mydb"

    def test_expand_env_var_in_list(self, monkeypatch):
        """Test expanding environment variables in list."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")

        data = ["${VAR1}", "$VAR2", "static"]
        result = expand_env_vars(data)

        assert result == ["value1", "value2", "static"]

    def test_expand_env_var_nested(self, monkeypatch):
        """Test expanding environment variables in nested structures."""
        monkeypatch.setenv("API_KEY", "secret123")

        data = {"config": {"credentials": {"api_key": "${API_KEY}"}}}
        result = expand_env_vars(data)

        assert result["config"]["credentials"]["api_key"] == "secret123"

    def test_expand_env_var_missing_non_strict(self):
        """Test missing environment variable in non-strict mode."""
        # Ensure variable doesn't exist
        if "MISSING_VAR" in os.environ:
            del os.environ["MISSING_VAR"]

        # Should return original value with warning
        result = expand_env_vars("${MISSING_VAR}", strict=False)
        assert result == "${MISSING_VAR}"

    def test_expand_env_var_missing_strict(self):
        """Test missing environment variable in strict mode raises error."""
        # Ensure variable doesn't exist
        if "MISSING_VAR" in os.environ:
            del os.environ["MISSING_VAR"]

        with pytest.raises(ValueError, match="Environment variable 'MISSING_VAR' not found"):
            expand_env_vars("${MISSING_VAR}", strict=True)

    def test_expand_env_var_non_string(self):
        """Test expanding non-string values."""
        result = expand_env_vars(123)
        assert result == 123

        result = expand_env_vars(True)
        assert result is True

        result = expand_env_vars(None)
        assert result is None

    def test_expand_env_var_partial_match(self):
        """Test that partial matches are not expanded."""
        result = expand_env_vars("prefix_${VAR}_suffix")
        # Should not be expanded because it doesn't match the pattern exactly
        assert result == "prefix_${VAR}_suffix"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_default(self):
        """Test loading default config."""
        config = load_config(None)
        assert isinstance(config, AppConfig)

    def test_load_config_from_file(self, tmp_path):
        """Test loading config from YAML file."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
logging:
  level: DEBUG
  format: console

output:
  directory: ./custom_output
  keep_temp: true

slide:
  default_size: "4:3"
  default_font: "Helvetica"
"""
        )

        config = load_config(config_path)

        assert config.logging.level == "DEBUG"
        assert config.logging.format == "console"
        assert config.output.directory == "./custom_output"
        assert config.output.keep_temp is True
        assert config.slide.default_size == "4:3"
        assert config.slide.default_font == "Helvetica"

    def test_load_config_with_env_vars(self, tmp_path, monkeypatch):
        """Test loading config with environment variable expansion."""
        monkeypatch.setenv("API_KEY", "secret123")
        monkeypatch.setenv("OUTPUT_DIR", "/tmp/output")

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
llm:
  openai:
    type: api
    provider: openai
    model: gpt-4
    api_key: ${API_KEY}

output:
  directory: ${OUTPUT_DIR}
"""
        )

        config = load_config(config_path)

        assert config.llm["openai"].api_key == "secret123"
        assert config.output.directory == "/tmp/output"

    def test_load_config_missing_env_var_strict(self, tmp_path):
        """Test loading config with missing env var in strict mode."""
        # Ensure variable doesn't exist
        if "MISSING_API_KEY" in os.environ:
            del os.environ["MISSING_API_KEY"]

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
llm:
  openai:
    type: api
    provider: openai
    model: gpt-4
    api_key: ${MISSING_API_KEY}
"""
        )

        with pytest.raises(ValueError, match="Configuration error"):
            load_config(config_path, strict_env=True)

    def test_load_config_missing_env_var_non_strict(self, tmp_path):
        """Test loading config with missing env var in non-strict mode."""
        # Ensure variable doesn't exist
        if "MISSING_API_KEY" in os.environ:
            del os.environ["MISSING_API_KEY"]

        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            """
llm:
  openai:
    type: api
    provider: openai
    model: gpt-4
    api_key: ${MISSING_API_KEY}
"""
        )

        # Should succeed but keep original value
        config = load_config(config_path, strict_env=False)
        assert config.llm["openai"].api_key == "${MISSING_API_KEY}"

    def test_load_config_nonexistent_file(self):
        """Test loading non-existent config file."""
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            load_config("nonexistent.yaml")

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test loading invalid YAML file."""
        config_path = tmp_path / "invalid.yaml"
        config_path.write_text("{ invalid yaml: ]")

        with pytest.raises(ValueError, match="Invalid YAML format"):
            load_config(config_path)

    def test_load_config_empty_file(self, tmp_path):
        """Test loading empty YAML file returns default config."""
        config_path = tmp_path / "empty.yaml"
        config_path.write_text("")

        config = load_config(config_path)
        assert isinstance(config, AppConfig)

    def test_load_config_invalid_schema(self, tmp_path):
        """Test loading config with invalid schema."""
        config_path = tmp_path / "invalid_schema.yaml"
        config_path.write_text(
            """
logging:
  level: INVALID_LEVEL
  invalid_field: 123
"""
        )

        # Should still load, but may have validation warnings
        # Pydantic will use defaults for invalid fields
        config = load_config(config_path)
        assert isinstance(config, AppConfig)
