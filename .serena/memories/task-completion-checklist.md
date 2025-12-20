# タスク完了時のチェックリスト

## 必須チェック

### 1. リント（ruff）
```bash
uv run ruff check src/
uv run ruff check tests/
```
- すべてのエラーと警告を修正
- 未使用インポートの削除
- コードスタイル準拠

### 2. 型チェック（mypy）
```bash
uv run mypy src/
```
- 型ヒントの追加
- strict modeでのエラー解消
- 型安全性の保証

### 3. テスト実行
```bash
uv run pytest
```
- すべてのテストがパス
- 新規コードに対するテスト追加
- カバレッジ80%以上維持

### 4. コミット前
```bash
git status
git diff
```
- 意図しない変更がないか確認
- コミットメッセージは日本語で明確に

## セキュリティチェック（Phase 1）
- パストラバーサル脆弱性
- 入力検証（RGB値、JSON）
- エラーハンドリング
- 環境変数strictモード

## ドキュメント更新
- CLAUDE.mdの更新（必要に応じて）
- docstringの追加・更新
- READMEの更新（大きな変更時）
