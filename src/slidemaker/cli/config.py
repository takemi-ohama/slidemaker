"""
Configuration management for CLI.

This module provides ConfigManager class for loading and validating
CLI-specific configuration. It extends the functionality of
utils/config_loader.py with additional CLI-specific features.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from slidemaker.utils.config_loader import (
    AppConfig,
    expand_env_vars,
    get_default_config_path,
)
from slidemaker.utils.file_manager import FileManager
from slidemaker.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigLoadError(Exception):
    """Configuration loading error."""


class ConfigValidationError(Exception):
    """Configuration validation error."""


class ConfigManager:
    """
    Manages configuration loading and validation for CLI.

    This class handles:
    - Searching for config files in multiple locations
    - Loading and parsing YAML configuration
    - Environment variable expansion
    - Configuration validation
    - Providing default configuration

    Examples:
        >>> manager = ConfigManager()
        >>> config = manager.load_config()
        >>> config = manager.load_config(Path("custom_config.yaml"))
    """

    def __init__(self, strict_env: bool = False) -> None:
        """
        Initialize ConfigManager.

        Args:
            strict_env: If True, raise error when environment variables are not found.
                       Useful for production environments to catch misconfigurations.
        """
        self.strict_env = strict_env
        self._file_manager = FileManager()

    def load_config(self, config_path: Path | None = None) -> dict[str, Any]:
        """
        Load configuration from file.

        Search order:
        1. Specified config_path
        2. ./config.yaml (current directory)
        3. ~/.slidemaker/config.yaml (home directory)
        4. Default configuration

        Args:
            config_path: Path to configuration file. If None, searches default locations.

        Returns:
            Configuration dictionary with expanded environment variables

        Raises:
            ConfigLoadError: If config file not found or invalid YAML format
            ConfigValidationError: If configuration validation fails
        """
        resolved_path = self._resolve_config_path(config_path)

        if resolved_path is None:
            logger.info("No config file found, using default configuration")
            return self.get_default_config()

        logger.info("Loading configuration", config_path=str(resolved_path))
        return self._load_from_file(resolved_path)

    def _resolve_config_path(self, config_path: Path | None) -> Path | None:
        """
        Resolve configuration file path.

        Args:
            config_path: Specified config path or None

        Returns:
            Resolved Path object or None if not found

        Raises:
            ConfigLoadError: If path is invalid or outside allowed directories
        """
        if config_path is not None:
            # Specified path has highest priority
            if not config_path.exists():
                raise ConfigLoadError(f"Specified config file not found: {config_path}")

            # セキュリティ検証強化
            try:
                resolved_path = config_path.resolve(strict=True)

                # 許可されたディレクトリ内かチェック
                allowed_dirs = [
                    Path.cwd().resolve(),
                    Path.home().resolve() / ".slidemaker",
                ]

                is_allowed = False
                for allowed_dir in allowed_dirs:
                    try:
                        resolved_path.relative_to(allowed_dir)
                        is_allowed = True
                        break
                    except ValueError:
                        continue

                if not is_allowed:
                    raise ConfigLoadError(
                        f"Config file outside allowed directories: {config_path}"
                    )

                return resolved_path

            except (ValueError, OSError) as e:
                raise ConfigLoadError(f"Invalid config path: {e}") from e

        # Search default locations
        return get_default_config_path()

    def _load_from_file(self, config_path: Path) -> dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file

        Returns:
            Configuration dictionary

        Raises:
            ConfigLoadError: If file reading or YAML parsing fails
            ConfigValidationError: If configuration validation fails
        """
        try:
            with config_path.open("r", encoding="utf-8") as f:
                raw_data: Any = yaml.safe_load(f)
                data: dict[str, Any] | None = raw_data if isinstance(raw_data, dict) else None
        except yaml.YAMLError as e:
            raise ConfigLoadError(f"Invalid YAML format in {config_path}: {e}") from e
        except OSError as e:
            raise ConfigLoadError(f"Failed to read config file {config_path}: {e}") from e

        if not data:
            logger.warning(
                "Config file is empty, using default configuration",
                config_path=str(config_path),
            )
            return self.get_default_config()

        # Expand environment variables
        try:
            expanded_data: Any = expand_env_vars(data, strict=self.strict_env)
            # expand_env_vars preserves dict structure
            data = expanded_data if isinstance(expanded_data, dict) else data
        except ValueError as e:
            raise ConfigValidationError(f"Configuration error in {config_path}: {e}") from e

        # Validate configuration
        self.validate_config(data)

        logger.info("Configuration loaded successfully", config_path=str(config_path))
        return data

    def validate_config(self, config: dict[str, Any]) -> None:
        """
        Validate configuration.

        Checks:
        - Required fields exist (llm, output)
        - LLM configuration is valid (provider, model, api_key)
        - Output directory paths are valid (no path traversal)
        - Values are within acceptable ranges

        Args:
            config: Configuration dictionary to validate

        Raises:
            ConfigValidationError: If validation fails
        """
        # Check required top-level sections
        if "llm" not in config:
            raise ConfigValidationError("Missing required section: 'llm'")
        if "output" not in config:
            raise ConfigValidationError("Missing required section: 'output'")

        # Validate LLM configuration
        self._validate_llm_config(config["llm"])

        # Validate output configuration
        self._validate_output_config(config["output"])

        # Validate optional sections if present
        if "logging" in config:
            self._validate_logging_config(config["logging"])

    def _validate_llm_config(self, llm_config: dict[str, Any]) -> None:
        """
        Validate LLM configuration.

        Args:
            llm_config: LLM configuration dictionary

        Raises:
            ConfigValidationError: If validation fails
        """
        for section in ["composition", "image_generation"]:
            if section not in llm_config:
                # composition is required, image_generation is optional
                if section == "composition":
                    raise ConfigValidationError(f"Missing required field: 'llm.{section}'")
                continue

            config = llm_config[section]

            # Basic required fields (api_key is conditionally required)
            required_fields = ["type", "provider", "model"]

            # Check if provider uses Bedrock (AWS authentication)
            provider = config.get("provider", "")
            is_bedrock_provider = provider in ["bedrock-claude", "bedrock"]

            # For non-Bedrock providers, api_key is required
            if not is_bedrock_provider:
                required_fields.append("api_key")

            # Validate required fields
            for field in required_fields:
                if field not in config:
                    raise ConfigValidationError(
                        f"Missing required field: 'llm.{section}.{field}'"
                    )

            # Validate type
            if config["type"] not in ["api", "cli"]:
                raise ConfigValidationError(
                    f"Invalid llm.{section}.type: {config['type']}. "
                    "Must be 'api' or 'cli'."
                )

            # Warn if API key is not set (but allow for testing)
            # Skip warning for Bedrock providers
            if not is_bedrock_provider:
                api_key = config.get("api_key", "")
                if not api_key or api_key.startswith("${"):
                    logger.warning(
                        "LLM API key not set or environment variable not expanded",
                        section=section,
                        provider=provider,
                    )

    def _validate_output_config(self, output_config: dict[str, Any]) -> None:
        """
        Validate output configuration.

        Args:
            output_config: Output configuration dictionary

        Raises:
            ConfigValidationError: If validation fails
        """
        if "directory" not in output_config:
            raise ConfigValidationError("Missing required field: 'output.directory'")

        directory = output_config["directory"]

        # Security: Validate output directory path
        try:
            # Resolve to absolute path and check for path traversal
            Path(directory).resolve()
            # Ensure it's not a path traversal attempt
            if ".." in Path(directory).parts:
                raise ConfigValidationError(
                    f"Invalid output directory (contains '..'): {directory}"
                )
        except (ValueError, OSError) as e:
            raise ConfigValidationError(f"Invalid output directory path: {directory}") from e

    def _validate_logging_config(self, logging_config: dict[str, Any]) -> None:
        """
        Validate logging configuration.

        Args:
            logging_config: Logging configuration dictionary

        Raises:
            ConfigValidationError: If validation fails
        """
        if "level" in logging_config:
            valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            level = logging_config["level"]
            if level not in valid_levels:
                raise ConfigValidationError(
                    f"Invalid logging level: {level}. Must be one of {valid_levels}."
                )

        if "format" in logging_config:
            valid_formats = ["json", "text"]
            fmt = logging_config["format"]
            if fmt not in valid_formats:
                raise ConfigValidationError(
                    f"Invalid logging format: {fmt}. Must be one of {valid_formats}."
                )

    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            "llm": {
                "composition": {
                    "type": "api",
                    "provider": "claude",
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                    "timeout": 300,
                },
                "image_generation": {
                    "type": "api",
                    "provider": "dalle",
                    "model": "dall-e-3",
                    "api_key": os.getenv("OPENAI_API_KEY", ""),
                    "timeout": 300,
                },
            },
            "output": {
                "directory": "./output",
                "temp_directory": "./tmp",
                "keep_temp": False,
            },
            "slide": {
                "default_size": "16:9",
                "default_theme": "minimal",
                "default_font": "Arial",
            },
            "logging": {
                "level": "INFO",
                "format": "json",
                "file": None,
            },
        }

    def load_app_config(self, config_path: Path | None = None) -> AppConfig:
        """
        Load configuration as AppConfig model.

        This is a convenience method that loads configuration and
        parses it into AppConfig model from utils/config_loader.py.

        Args:
            config_path: Path to configuration file

        Returns:
            AppConfig instance

        Raises:
            ConfigLoadError: If config loading fails
            ConfigValidationError: If config validation fails
        """
        config_dict = self.load_config(config_path)

        try:
            return AppConfig.model_validate(config_dict)
        except Exception as e:
            raise ConfigValidationError(f"Invalid configuration schema: {e}") from e
