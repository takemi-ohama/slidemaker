"""入力検証ユーティリティ

セキュリティ脆弱性対策として、外部入力の検証機能を提供します。
"""
import re
from pathlib import Path
from typing import Optional


def validate_gcp_project_id(project_id: Optional[str]) -> str:
    """GCPプロジェクトIDの検証

    GCPプロジェクトIDの命名規則に従って検証します：
    - 小文字、数字、ハイフンのみ
    - 先頭は小文字
    - 末尾は小文字または数字
    - 6-30文字

    Args:
        project_id: 検証するプロジェクトID

    Returns:
        str: 検証済みプロジェクトID

    Raises:
        ValueError: プロジェクトIDが未設定または不正な形式の場合

    References:
        CWE-20: Improper Input Validation
        https://cwe.mitre.org/data/definitions/20.html
    """
    if not project_id:
        raise ValueError(
            "GOOGLE_CLOUD_PROJECT environment variable is required"
        )

    # GCP命名規則に従った検証
    if not re.match(r'^[a-z][a-z0-9-]{4,28}[a-z0-9]$', project_id):
        raise ValueError(
            f"Invalid GCP project ID format: {project_id}. "
            f"Project ID must be 6-30 characters, start with lowercase letter, "
            f"and contain only lowercase letters, numbers, and hyphens."
        )

    return project_id


def validate_file_path(
    file_path: str,
    allowed_dir: Optional[Path] = None,
    must_exist: bool = True,
    must_be_file: bool = True,
) -> Path:
    """ファイルパスの検証（パストラバーサル対策）

    ファイルパスを検証し、パストラバーサル攻撃を防止します。

    Args:
        file_path: 検証するファイルパス
        allowed_dir: 許可されたディレクトリ（指定された場合、このディレクトリ配下のみ許可）
        must_exist: ファイルの存在を確認するか
        must_be_file: ファイルであることを確認するか

    Returns:
        Path: 検証済みの絶対パス

    Raises:
        FileNotFoundError: ファイルが存在しない場合
        ValueError: パスが不正な場合

    References:
        CWE-22: Path Traversal
        https://cwe.mitre.org/data/definitions/22.html
    """
    # 絶対パスに解決
    resolved_path = Path(file_path).resolve()

    # ファイルの存在確認
    if must_exist and not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # ファイルタイプの確認
    if must_be_file and resolved_path.exists() and not resolved_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # 許可されたディレクトリ配下かチェック
    if allowed_dir is not None:
        allowed_resolved = allowed_dir.resolve()
        try:
            # relative_to()は、resolved_pathがallowed_resolved配下でない場合に例外を投げる
            resolved_path.relative_to(allowed_resolved)
        except ValueError:
            raise ValueError(
                f"Access denied: file '{file_path}' is outside allowed directory '{allowed_dir}'"
            )

    return resolved_path
