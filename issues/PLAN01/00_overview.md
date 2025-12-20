# slidemakerプロジェクト開発計画 - 概要

## プロジェクト概要
slidemakerは、複数の方法でPowerPointスライドを自動生成するツールです。LLMを活用し、構成設計から画像生成、スライド作成までを自動化します。

## 主要機能

### 1. 新規作成モード
- **入力**: Markdownによるスライド構成概要
- **処理フロー**:
  1. LLMでスライド設定とページ定義を生成
  2. LLMで各ページの画像を生成
  3. 構成定義（Markdown形式）を出力
  4. PowerPointドキュメントを作成・保存
- **出力**: PowerPointファイル（.pptx）

### 2. PDF/画像から作成モード
- **入力**: PDFファイル、または画像ファイル群
- **処理フロー**:
  1. LLMでスライド構成を分解（画像・テキスト分離）
  2. LLMでスライド設定とページ定義を生成
  3. LLMで画像をトリミング・テキスト除去
  4. 背景画像の抽出と加工
  5. PowerPointドキュメントを作成・保存
- **出力**: PowerPointファイル（.pptx）

## ページ定義仕様
- **スライド設定**: サイズ（デフォルト16:9）、共通背景、ファイル名等
- **ページ要素**: 画像とテキスト
- **要素属性**: 座標、レイヤー順序、透過率
- **テキスト属性**: フォント、サイズ、色（PowerPoint仕様準拠）

## LLM統合
- **選択可能な利用形態**:
  - API経由: nano banana, Gemini, GPT-5.2, Claude Opus等
  - CLI経由: codex cli, gemini cli, claude code, kiro cli等
- **分離設定**: 構成定義用LLMと画像生成用LLMを個別指定可能

## 提供形態
1. **CLI版**: コマンドラインツール
2. **WebUI版**: Webアプリケーション（React + TypeScript）

## 開発方針
- Python 3.13をコア言語として使用
- CLI版とWebUI版でコードを最大限共有
- モジュール化による保守性確保
- 段階的な開発とテスト

## デプロイ戦略
- **CLI版**: PyPIへの登録、GitHub Actions CI/CD
- **WebUI版**: AWS Lambda + API Gateway、CDK（Python）による構成管理
