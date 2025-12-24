"""CLI main entry point.

Slidemakerのコマンドラインインターフェースのメインエントリーポイントです。
"""

import typer

from slidemaker.cli.commands.convert import convert
from slidemaker.cli.commands.create import create

# Typerアプリケーション
app = typer.Typer(
    name="slidemaker",
    help="AI-powered PowerPoint generator",
    add_completion=False,
    no_args_is_help=True,
)

# サブコマンドの登録
app.command(name="create")(create)
app.command(name="convert")(convert)


@app.command(name="version")
def version() -> None:
    """Show version information.

    バージョン情報を表示します。

    Example:
        $ slidemaker version
        slidemaker version 0.3.0
    """
    try:
        # pyproject.tomlからバージョンを取得
        import importlib.metadata

        version_str = importlib.metadata.version("slidemaker")
        typer.echo(f"slidemaker version {version_str}")
    except importlib.metadata.PackageNotFoundError:
        # 開発環境でインストールされていない場合
        typer.echo("slidemaker version (development)")


def main() -> None:
    """CLI entry point.

    コマンドラインからの実行時のエントリーポイントです。
    """
    app()


if __name__ == "__main__":
    main()
