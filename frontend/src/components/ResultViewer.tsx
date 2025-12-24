/**
 * ResultViewer コンポーネント
 *
 * タスク完了後の結果表示コンポーネント。
 * ダウンロードリンク、ファイル情報、リセット機能を提供します。
 */

import React from 'react';
import { TaskResult } from '../types';

/**
 * ResultViewerコンポーネントのProps
 */
export interface ResultViewerProps {
  /** タスク結果データ */
  result: TaskResult;

  /** リセットコールバック（オプション） */
  onReset?: () => void;

  /** 追加のCSSクラス名 */
  className?: string;
}

/**
 * ファイルサイズを人間が読める形式に変換
 *
 * @param bytes - バイト数
 * @returns フォーマットされたファイルサイズ文字列（例: "1.23 MB"）
 *
 * @example
 * ```typescript
 * formatFileSize(0)        // "0 Bytes"
 * formatFileSize(1024)     // "1.00 KB"
 * formatFileSize(1048576)  // "1.00 MB"
 * ```
 */
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};

/**
 * ResultViewer - タスク完了結果表示コンポーネント
 *
 * タスク完了後に以下を表示します:
 * - 成功メッセージ
 * - ファイル情報（ファイル名、サイズ、スライド枚数）
 * - ダウンロードボタン
 * - リセットボタン（オプション）
 *
 * @example
 * ```tsx
 * <ResultViewer
 *   result={{
 *     output_url: "https://example.com/file.pptx",
 *     output_filename: "presentation.pptx",
 *     file_size: 2048000,
 *     page_count: 10
 *   }}
 *   onReset={() => console.log('Reset clicked')}
 * />
 * ```
 */
export const ResultViewer: React.FC<ResultViewerProps> = ({
  result,
  onReset,
  className = '',
}) => {
  // ファイルサイズをメモ化（パフォーマンス最適化）
  const formattedFileSize = React.useMemo(
    () => formatFileSize(result.file_size),
    [result.file_size]
  );

  return (
    <div
      className={`bg-white rounded-lg shadow-md p-6 ${className}`}
      role="region"
      aria-label="スライド生成結果"
    >
      {/* 成功メッセージ */}
      <div
        className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md"
        role="alert"
        aria-live="polite"
      >
        <div className="flex items-center">
          <span
            className="text-green-500 text-2xl mr-2"
            aria-hidden="true"
          >
            ✓
          </span>
          <p className="text-green-800 font-medium">
            スライドが正常に生成されました！
          </p>
        </div>
      </div>

      {/* ファイル情報 */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">
          ファイル情報
        </h3>
        <dl className="space-y-2">
          <div className="flex flex-col sm:flex-row">
            <dt className="w-full sm:w-32 text-gray-600">ファイル名:</dt>
            <dd className="text-gray-900 font-medium break-all">
              {result.output_filename}
            </dd>
          </div>
          <div className="flex flex-col sm:flex-row">
            <dt className="w-full sm:w-32 text-gray-600">ファイルサイズ:</dt>
            <dd className="text-gray-900">{formattedFileSize}</dd>
          </div>
          <div className="flex flex-col sm:flex-row">
            <dt className="w-full sm:w-32 text-gray-600">スライド枚数:</dt>
            <dd className="text-gray-900">{result.page_count} ページ</dd>
          </div>
        </dl>
      </div>

      {/* ダウンロードボタン */}
      <a
        href={result.output_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block w-full bg-blue-500 hover:bg-blue-600 text-white font-bold
                   py-3 px-6 rounded-lg text-center transition-colors duration-200
                   focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        aria-label="PowerPointファイルをダウンロード（新しいタブで開く）"
      >
        PowerPointをダウンロード
      </a>

      {/* リセットボタン */}
      {onReset && (
        <button
          onClick={onReset}
          className="mt-4 w-full bg-gray-200 hover:bg-gray-300 text-gray-700
                     py-2 px-4 rounded-lg text-center transition-colors duration-200
                     focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2"
          aria-label="新しいスライドを作成"
        >
          新しいスライドを作成
        </button>
      )}

      {/* 注意事項 */}
      <p className="mt-4 text-xs text-gray-500 text-center">
        ダウンロードリンクは7日間有効です
      </p>
    </div>
  );
};

// デフォルトエクスポート
export default ResultViewer;
