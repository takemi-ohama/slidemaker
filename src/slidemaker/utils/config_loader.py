"""Configuration loading utilities."""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """LLM configuration."""

    type: str = Field(..., description="'api' or 'cli'")
    provider: str = Field(..., description="LLM provider name")
    model: str = Field(..., description="Model name")
    api_key: str | None = Field(default=None, description="API key (for API type)")
    cli_command: str | None = Field(default=None, description="CLI command (for CLI type)")
    timeout: int = Field(default=300, description="Timeout in seconds")
    extra_params: dict[str, Any] = Field(
        default_factory=dict, description="Additional provider-specific parameters"
    )


class OutputConfig(BaseModel):
    """Output configuration."""

    directory: str = Field(default="./output", description="Output directory")
    temp_directory: str = Field(default="./tmp", description="Temporary directory")
    keep_temp: bool = Field(default=False, description="Keep temporary files")


class SlideDefaultsConfig(BaseModel):
    """Default slide settings."""

    default_size: str = Field(default="16:9", description="Default slide size")
    default_theme: str | None = Field(default=None, description="Default theme")
    default_font: str = Field(default="Arial", description="Default font family")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format")
    file: str | None = Field(default=None, description="Log file path")


class AppConfig(BaseModel):
    """Application configuration."""

    llm: dict[str, LLMConfig] = Field(
        default_factory=dict, description="LLM configurations"
    )
    output: OutputConfig = Field(default_factory=OutputConfig)
    slide: SlideDefaultsConfig = Field(default_factory=SlideDefaultsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def expand_env_vars(value: Any, strict: bool = False) -> Any:
    """
    Recursively expand environment variables in config values.

    Args:
        value: Value to expand (str, dict, list, or other)
        strict: If True, raise ValueError when environment variable is not found

    Returns:
        Value with environment variables expanded

    Raises:
        ValueError: If strict=True and environment variable is not found

    Examples:
        >>> expand_env_vars("${HOME}/config.yaml")
        "/home/user/config.yaml"
        >>> expand_env_vars("${MISSING_VAR}", strict=True)
        ValueError: Environment variable 'MISSING_VAR' not found
    """
    if isinstance(value, str):
        # Replace ${VAR} or $VAR with environment variable value
        if value.startswith("${") and value.endswith("}"):
            var_name = value[2:-1]
            env_value = os.environ.get(var_name)
            if env_value is None:
                if strict:
                    raise ValueError(
                        f"Environment variable '{var_name}' not found. "
                        f"Set it or use non-strict mode."
                    )
                # In non-strict mode, log warning and return original value
                import structlog
                logger = structlog.get_logger()
                logger.warning("Environment variable not found", var_name=var_name)
                return value
            return env_value
        elif value.startswith("$"):
            var_name = value[1:]
            env_value = os.environ.get(var_name)
            if env_value is None:
                if strict:
                    raise ValueError(
                        f"Environment variable '{var_name}' not found. "
                        f"Set it or use non-strict mode."
                    )
                import structlog
                logger = structlog.get_logger()
                logger.warning("Environment variable not found", var_name=var_name)
                return value
            return env_value
        return value
    elif isinstance(value, dict):
        return {k: expand_env_vars(v, strict) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(item, strict) for item in value]
    return value


def load_config(config_path: str | Path | None = None, strict_env: bool = False) -> AppConfig:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, uses default config.
        strict_env: If True, raise error when environment variables are not found.
                   Useful for production environments to catch misconfigurations.

    Returns:
        Loaded configuration

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid or environment variable is missing (strict_env=True)
    """
    if config_path is None:
        # Return default config
        return AppConfig()

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML format in {path}: {e}") from e

    if not data:
        return AppConfig()

    # Expand environment variables
    try:
        data = expand_env_vars(data, strict=strict_env)
    except ValueError as e:
        raise ValueError(f"Configuration error in {path}: {e}") from e

    # Parse into config model
    try:
        return AppConfig.model_validate(data)
    except Exception as e:
        raise ValueError(f"Invalid configuration schema in {path}: {e}") from e


def get_default_config_path() -> Path | None:
    """
    Get default config file path.

    Searches in order:
    1. ./config.yaml
    2. ~/.slidemaker/config.yaml
    3. None (use defaults)

    Returns:
        Path to config file or None
    """
    candidates = [
        Path.cwd() / "config.yaml",
        Path.home() / ".slidemaker" / "config.yaml",
    ]

    for path in candidates:
        if path.exists():
            return path

    return None
