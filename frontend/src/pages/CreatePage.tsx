import React, { useState } from 'react';
import { ProgressBar, ResultViewer } from '../components';
import { useTaskStatus } from '../hooks';
import { apiClient } from '../api';

/**
 * 新規作成ページコンポーネント
 *
 * Markdown入力からPowerPointスライドを生成する。
 * LLMが最適なレイアウトと構成を自動生成。
 */
export const CreatePage: React.FC = () => {
  const [content, setContent] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { taskStatus, startPolling, resetStatus } = useTaskStatus();

  /**
   * スライド生成処理
   */
  const handleCreate = async () => {
    // バリデーション
    if (!content.trim()) {
      setError('Markdown内容を入力してください。');
      return;
    }

    setError(null);
    setIsCreating(true);
    resetStatus();

    try {
      const response = await apiClient.createSlide({ content });
      startPolling(response.task_id);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'スライド生成に失敗しました。';
      setError(errorMessage);
      console.error('Create slide error:', err);
    } finally {
      setIsCreating(false);
    }
  };

  /**
   * サンプルMarkdownを挿入
   */
  const insertSample = () => {
    const sample = `# 私のプレゼンテーション

## スライド 1: イントロダクション

こんにちは！今日は私たちの新しいプロジェクトについてお話しします。

## スライド 2: 主要な機能

- 機能1: 自動レイアウト最適化
- 機能2: AIによる画像生成
- 機能3: 簡単な編集・カスタマイズ

## スライド 3: まとめ

ご清聴ありがとうございました。
`;
    setContent(sample);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">新規作成</h1>
        <p className="text-gray-600">
          Markdownでプレゼンテーション内容を記述してください。AIが最適なスライドを生成します。
        </p>
      </div>

      {/* エラー表示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-red-600 mr-2 mt-0.5"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <h3 className="text-red-800 font-semibold">エラー</h3>
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* メインコンテンツエリア */}
      <div className="grid lg:grid-cols-2 gap-8">
        {/* 左カラム: 入力エリア */}
        <div className="space-y-4">
          {/* Markdown入力 */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <label
                htmlFor="markdown-input"
                className="block text-sm font-medium text-gray-700"
              >
                Markdown入力
              </label>
              <button
                onClick={insertSample}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                サンプルを挿入
              </button>
            </div>
            <textarea
              id="markdown-input"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="# My Presentation&#10;&#10;## Slide 1&#10;&#10;Introduction to our project...&#10;&#10;## Slide 2&#10;&#10;Key features..."
              className="w-full min-h-[400px] p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-vertical"
              disabled={isCreating}
            />
            <p className="text-xs text-gray-500 mt-1">
              {content.length} 文字
            </p>
          </div>

          {/* 設定（オプション） */}
          <div className="border border-gray-200 rounded-lg">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="w-full px-4 py-3 flex justify-between items-center hover:bg-gray-50"
            >
              <span className="font-medium text-gray-700">
                詳細設定（オプション）
              </span>
              <svg
                className={`w-5 h-5 text-gray-500 transform transition-transform ${
                  showSettings ? 'rotate-180' : ''
                }`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 9l-7 7-7-7"
                />
              </svg>
            </button>
            {showSettings && (
              <div className="px-4 py-3 border-t border-gray-200 space-y-3">
                <div>
                  <label className="block text-sm text-gray-700 mb-1">
                    スライドサイズ
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                    <option value="16:9">16:9（ワイド）</option>
                    <option value="4:3">4:3（標準）</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-700 mb-1">
                    デフォルトフォント
                  </label>
                  <select className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm">
                    <option value="Arial">Arial</option>
                    <option value="Meiryo">Meiryo</option>
                    <option value="MS Gothic">MS Gothic</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm text-gray-700 mb-1">
                    フォントサイズ
                  </label>
                  <input
                    type="number"
                    defaultValue={18}
                    min={10}
                    max={72}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                  />
                </div>
              </div>
            )}
          </div>

          {/* 生成ボタン */}
          <button
            onClick={handleCreate}
            disabled={isCreating || !content.trim()}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isCreating ? (
              <span className="flex items-center justify-center">
                <svg
                  className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                生成中...
              </span>
            ) : (
              'スライドを生成'
            )}
          </button>
        </div>

        {/* 右カラム: 進捗・結果表示 */}
        <div className="space-y-4">
          {/* 進捗表示 */}
          {taskStatus && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                生成状況
              </h3>
              <ProgressBar
                status={taskStatus.status}
                progress={taskStatus.progress}
              />
            </div>
          )}

          {/* 結果表示 */}
          {taskStatus?.result && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                生成結果
              </h3>
              <ResultViewer result={taskStatus.result} />
            </div>
          )}

          {/* ヘルプテキスト */}
          {!taskStatus && (
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">
                Markdownの書き方
              </h3>
              <ul className="space-y-2 text-sm text-blue-800">
                <li>
                  <code className="bg-blue-100 px-1 py-0.5 rounded">#</code>{' '}
                  プレゼンテーションのタイトル
                </li>
                <li>
                  <code className="bg-blue-100 px-1 py-0.5 rounded">##</code>{' '}
                  各スライドのタイトル
                </li>
                <li>
                  <code className="bg-blue-100 px-1 py-0.5 rounded">-</code> リスト項目
                </li>
                <li>
                  <code className="bg-blue-100 px-1 py-0.5 rounded">**太字**</code>{' '}
                  強調テキスト
                </li>
              </ul>
              <p className="text-xs text-blue-700 mt-4">
                AIが自動的に最適なレイアウトを選択し、必要に応じて画像を生成します。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
