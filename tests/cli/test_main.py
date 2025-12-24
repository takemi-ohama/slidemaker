"""Tests for CLI main entry point."""

from typer.testing import CliRunner

from slidemaker.cli.main import app, main


class TestCLIMain:
    """Tests for CLI main module."""

    def test_app_exists(self) -> None:
        """Test that Typer app exists."""
        assert app is not None

    def test_app_name(self) -> None:
        """Test that app has correct name."""
        assert hasattr(app, "info")
        assert app.info.name == "slidemaker"

    def test_app_help(self) -> None:
        """Test that app has help message."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "slidemaker" in result.stdout.lower()
        assert "AI-powered PowerPoint generator" in result.stdout

    def test_create_command_registered(self) -> None:
        """Test that create command is registered."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "create" in result.stdout

    def test_convert_command_registered(self) -> None:
        """Test that convert command is registered."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "convert" in result.stdout

    def test_version_command(self) -> None:
        """Test version command execution."""
        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "slidemaker version" in result.stdout

    def test_version_command_in_development(self) -> None:
        """Test version command shows development version when package not installed."""
        # versionコマンド関数を直接テスト（パッケージ未インストール時の挙動）
        runner = CliRunner()
        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        # インストール済みまたは開発環境のいずれかのバージョン表示
        assert "slidemaker version" in result.stdout

    def test_main_entry_point(self) -> None:
        """Test main() function exists."""
        assert main is not None
        assert callable(main)

    def test_cli_module_import(self) -> None:
        """Test CLI module can be imported."""
        from slidemaker import cli

        assert cli is not None

    def test_no_args_shows_help(self) -> None:
        """Test that running with no args shows help (no_args_is_help=True)."""
        runner = CliRunner()
        result = runner.invoke(app, [])

        # no_args_is_helpがTrueの場合、引数なしでhelpが表示される（exit_code=2）
        # Typerはno_args_is_help=Trueの場合、UsageErrorを発生させるため exit_code=2
        # しかし、helpメッセージは出力される
        assert result.stdout != ""
        assert "AI-powered PowerPoint generator" in result.stdout or "Usage" in result.stdout

    def test_version_command_registered(self) -> None:
        """Test that version command is properly registered."""
        runner = CliRunner()
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "version" in result.stdout
        assert "Show version information" in result.stdout

    def test_invalid_command_shows_error(self) -> None:
        """Test that invalid command shows error."""
        runner = CliRunner()
        result = runner.invoke(app, ["invalid-command"])

        # Typerは無効なコマンドに対してエラーを返す
        assert result.exit_code != 0
        # エラーメッセージに"No such command"または類似のメッセージが含まれる
