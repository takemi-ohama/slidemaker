"""CLI module for Slidemaker.

コマンドラインインターフェースモジュールです。
"""

from slidemaker.cli.commands.convert import convert
from slidemaker.cli.commands.create import create
from slidemaker.cli.config import ConfigManager
from slidemaker.cli.main import app, main, version
from slidemaker.cli.output import OutputFormatter

__all__ = [
    # Main application
    "app",
    "main",
    "version",
    # Commands
    "create",
    "convert",
    # Utilities
    "ConfigManager",
    "OutputFormatter",
]
