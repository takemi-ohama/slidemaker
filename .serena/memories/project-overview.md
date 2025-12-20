# Slidemaker プロジェクト概要

## プロジェクト目的
AI（LLM）を活用してPowerPointスライドを自動生成するツール。

### 主要機能
1. **新規作成モード**: Markdown → LLM → PowerPoint
2. **変換モード**: PDF/画像 → LLM分析 → PowerPoint

## 技術スタック
- **言語**: Python 3.13
- **パッケージ管理**: uv (Rust製、高速)
- **LLM統合**: Claude, GPT, Gemini (API + CLI)
- **バリデーション**: Pydantic v2
- **HTTP**: httpx (非同期)
- **ロギング**: structlog
- **PowerPoint**: python-pptx
- **画像処理**: Pillow, pdf2image
- **CLI**: Typer + Rich
- **API**: FastAPI (Phase 6)

## アーキテクチャ
4層アーキテクチャを採用：
1. インターフェース層（CLI / WebUI）
2. アプリケーション層（ワークフロー制御）
3. ドメイン層（コアロジック）
4. インフラ層（LLM, ファイル, PowerPoint）

## 現在の開発フェーズ
**Phase 1**: コアモデルとLLM統合（80%完了）

実装済み:
- データモデル（Pydantic）
- シリアライザ（JSON, Markdown）
- ユーティリティ（logger, config_loader, file_manager）
- LLM基盤（base, manager, prompts）
- API基底アダプタ
- Claudeアダプタ
- セキュリティ修正

残タスク:
- GPT/Geminiアダプタ
- CLIアダプタ
- 包括的なユニットテスト
