import React from 'react';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { HomePage, CreatePage, ConvertPage } from './pages';

/**
 * ルートコンポーネント
 *
 * React Router v6によるルーティング設定。
 * ヘッダーナビゲーションとページコンポーネントをレンダリング。
 */
export const App: React.FC = () => {
  return (
    <BrowserRouter>
      {/* ヘッダーナビゲーション */}
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          {/* ロゴ */}
          <Link to="/" className="text-2xl font-bold text-blue-600 hover:text-blue-700 transition-colors">
            Slidemaker
          </Link>

          {/* ナビゲーションリンク */}
          <div className="flex items-center space-x-6">
            <Link
              to="/create"
              className="text-gray-600 hover:text-blue-600 font-medium transition-colors"
            >
              新規作成
            </Link>
            <Link
              to="/convert"
              className="text-gray-600 hover:text-green-600 font-medium transition-colors"
            >
              変換
            </Link>
            <a
              href="https://github.com/yourusername/slidemaker"
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="GitHub"
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                <path
                  fillRule="evenodd"
                  d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  clipRule="evenodd"
                />
              </svg>
            </a>
          </div>
        </div>
      </nav>

      {/* メインコンテンツ */}
      <main className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/create" element={<CreatePage />} />
          <Route path="/convert" element={<ConvertPage />} />
          {/* 404ページ */}
          <Route
            path="*"
            element={
              <div className="container mx-auto px-4 py-16 text-center">
                <h1 className="text-4xl font-bold text-gray-800 mb-4">404</h1>
                <p className="text-gray-600 mb-8">ページが見つかりませんでした。</p>
                <Link
                  to="/"
                  className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  ホームに戻る
                </Link>
              </div>
            }
          />
        </Routes>
      </main>
    </BrowserRouter>
  );
};

export default App;
