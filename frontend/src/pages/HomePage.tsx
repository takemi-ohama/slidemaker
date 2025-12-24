import React from 'react';
import { Link } from 'react-router-dom';

/**
 * ホームページコンポーネント
 *
 * アプリケーションのランディングページ。
 * 2つの主要機能（新規作成、変換）へのナビゲーションを提供。
 */
export const HomePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* タイトルセクション */}
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-800 mb-4">
            Slidemaker
          </h1>
          <p className="text-xl text-gray-600">
            AI-Powered PowerPoint Generator
          </p>
        </div>

        {/* 機能カード */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* 新規作成カード */}
          <Link
            to="/create"
            className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow duration-300 transform hover:-translate-y-1"
          >
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
                <svg
                  className="w-8 h-8 text-blue-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
              </div>
              <h3 className="text-2xl font-semibold text-gray-800 mb-2">
                新規作成
              </h3>
              <p className="text-gray-600 text-center">
                Markdownからスライド生成
              </p>
              <p className="text-sm text-gray-500 mt-4 text-center">
                テキストベースでプレゼンテーションを作成。AIが最適なレイアウトを提案します。
              </p>
            </div>
          </Link>

          {/* 変換カード */}
          <Link
            to="/convert"
            className="bg-white rounded-lg shadow-lg p-8 hover:shadow-xl transition-shadow duration-300 transform hover:-translate-y-1"
          >
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
                  />
                </svg>
              </div>
              <h3 className="text-2xl font-semibold text-gray-800 mb-2">
                変換
              </h3>
              <p className="text-gray-600 text-center">
                PDF/画像からスライド変換
              </p>
              <p className="text-sm text-gray-500 mt-4 text-center">
                既存の資料を編集可能なPowerPointに変換。AIが要素を自動識別します。
              </p>
            </div>
          </Link>
        </div>

        {/* 機能リスト */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-12">
          <h2 className="text-xl font-semibold text-gray-800 mb-4 text-center">
            主な機能
          </h2>
          <ul className="space-y-3 text-gray-600">
            <li className="flex items-start">
              <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>AIによる自動レイアウト最適化</span>
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>画像の自動生成・配置</span>
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>PDF/画像からの自動変換</span>
            </li>
            <li className="flex items-start">
              <svg className="w-5 h-5 text-green-500 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>編集可能なPowerPoint形式で出力</span>
            </li>
          </ul>
        </div>

        {/* フッター */}
        <footer className="text-center text-gray-500 text-sm">
          <p className="mb-2">v0.6.0 | © 2025 Slidemaker Team</p>
          <div className="flex justify-center space-x-4 text-xs">
            <a href="#" className="hover:text-blue-600 transition-colors">
              ドキュメント
            </a>
            <span>|</span>
            <a href="#" className="hover:text-blue-600 transition-colors">
              GitHub
            </a>
            <span>|</span>
            <a href="#" className="hover:text-blue-600 transition-colors">
              お問い合わせ
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
};
