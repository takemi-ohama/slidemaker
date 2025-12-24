import React, { useState } from 'react';
import { FileUpload, ProgressBar, ResultViewer } from '../components';
import { useFileUpload, useTaskStatus } from '../hooks';
import { apiClient } from '../api';

/**
 * 変換ページコンポーネント
 *
 * PDF/画像ファイルからPowerPointスライドを変換する。
 * LLMが要素（テキスト、画像）を自動識別して再構築。
 */
export const ConvertPage: React.FC = () => {
  const { file, encodedData, handleFileSelect, resetFile } = useFileUpload();
  const [isConverting, setIsConverting] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { taskStatus, startPolling, resetStatus } = useTaskStatus();

  /**
   * スライド変換処理
   */
  const handleConvert = async () => {
    // バリデーション
    if (!encodedData || !file) {
      setError('ファイルを選択してください。');
      return;
    }

    setError(null);
    setIsConverting(true);
    resetStatus();

    try {
      // ファイルタイプ判定
      const file_type = file.name.toLowerCase().endsWith('.pdf') ? 'pdf' : 'image';

      const response = await apiClient.convertSlide({
        file_data: encodedData,
        file_type,
      });

      startPolling(response.task_id);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : 'スライド変換に失敗しました。';
      setError(errorMessage);
      console.error('Convert slide error:', err);
    } finally {
      setIsConverting(false);
    }
  };

  /**
   * ファイルエラーハンドラー
   */
  const handleFileError = (errorMessage: string) => {
    setError(errorMessage);
  };

  /**
   * ファイル削除
   */
  const handleRemoveFile = () => {
    resetFile();
    setError(null);
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-6xl">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">変換</h1>
        <p className="text-gray-600">
          PDF/画像ファイルをアップロードしてください。AIが自動的に要素を識別し、編集可能なPowerPointに変換します。
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
        {/* 左カラム: ファイルアップロード */}
        <div className="space-y-4">
          {/* ファイルアップロード */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ファイルアップロード
            </label>
            <FileUpload
              accept=".pdf,.png,.jpg,.jpeg"
              maxSize={50 * 1024 * 1024} // 50MB
              onFileSelect={handleFileSelect}
              onError={handleFileError}
            />
          </div>

          {/* 選択されたファイル情報 */}
          {file && (
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {/* ファイルアイコン */}
                  <div className="flex-shrink-0">
                    {file.name.toLowerCase().endsWith('.pdf') ? (
                      <svg
                        className="w-10 h-10 text-red-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg
                        className="w-10 h-10 text-blue-500"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                  {/* ファイル情報 */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
                {/* 削除ボタン */}
                <button
                  onClick={handleRemoveFile}
                  className="ml-4 text-gray-400 hover:text-red-500"
                  disabled={isConverting}
                >
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </div>
            </div>
          )}

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
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="preserve-layout"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 rounded"
                  />
                  <label htmlFor="preserve-layout" className="ml-2 text-sm text-gray-700">
                    元のレイアウトを保持
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="extract-images"
                    defaultChecked
                    className="h-4 w-4 text-blue-600 rounded"
                  />
                  <label htmlFor="extract-images" className="ml-2 text-sm text-gray-700">
                    画像を抽出
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* 変換ボタン */}
          <button
            onClick={handleConvert}
            disabled={isConverting || !file}
            className="w-full bg-green-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isConverting ? (
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
                変換中...
              </span>
            ) : (
              'スライドに変換'
            )}
          </button>
        </div>

        {/* 右カラム: 進捗・結果表示 */}
        <div className="space-y-4">
          {/* 進捗表示 */}
          {taskStatus && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                変換状況
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
                変換結果
              </h3>
              <ResultViewer result={taskStatus.result} />
            </div>
          )}

          {/* ヘルプテキスト */}
          {!taskStatus && (
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-900 mb-3">
                サポートされているファイル形式
              </h3>
              <ul className="space-y-2 text-sm text-green-800">
                <li className="flex items-center">
                  <svg
                    className="w-4 h-4 mr-2 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  PDF（.pdf）
                </li>
                <li className="flex items-center">
                  <svg
                    className="w-4 h-4 mr-2 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  PNG（.png）
                </li>
                <li className="flex items-center">
                  <svg
                    className="w-4 h-4 mr-2 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  JPEG（.jpg, .jpeg）
                </li>
              </ul>
              <p className="text-xs text-green-700 mt-4">
                最大ファイルサイズ: 50MB
              </p>
              <p className="text-xs text-green-700 mt-2">
                AIがファイル内のテキスト、画像、レイアウトを自動的に識別し、編集可能なPowerPoint形式に変換します。
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
