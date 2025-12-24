# Slidemaker Frontend

Reactベースのフロントエンドアプリケーション

## 技術スタック

- React 19.2+
- TypeScript 5.9+
- Vite 7+
- Tailwind CSS 3.4+
- React Router v7

## セットアップ

```bash
# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev

# ビルド
npm run build

# プレビュー
npm run preview

# リンター
npm run lint

# 型チェック
npm run type-check
```

## 環境変数

`.env.development`または`.env.local`に以下を設定:

```
VITE_API_URL=http://localhost:8000
```

本番環境では`.env.production`:

```
VITE_API_URL=https://api.slidemaker.example.com
```

## ディレクトリ構造

```
src/
├── api/              # APIクライアント
├── components/       # Reactコンポーネント
├── hooks/            # カスタムフック
├── pages/            # ページコンポーネント
├── types/            # TypeScript型定義
├── App.tsx           # ルートコンポーネント
├── main.tsx          # エントリーポイント
└── index.css         # グローバルスタイル
```

## 開発規約

- TypeScript strict mode有効
- 関数コンポーネント + Hooks パターン
- Tailwind CSSでスタイリング
- ESLintルールの遵守
