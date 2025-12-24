import React, { useRef, useState } from 'react';

/**
 * FileUploadコンポーネントのProps
 */
interface FileUploadProps {
  /** 受け入れるファイル拡張子（例: ".md,.pdf,.png,.jpg"） */
  accept: string;
  /** 最大ファイルサイズ（バイト単位、デフォルト: 50MB） */
  maxSize: number;
  /** ファイル選択時のコールバック */
  onFileSelect: (file: File) => void;
  /** エラー発生時のコールバック */
  onError: (error: string) => void;
  /** 無効化フラグ */
  disabled?: boolean;
}

/**
 * FileUploadコンポーネント
 *
 * ドラッグ&ドロップまたはクリックでファイルをアップロードするUIコンポーネント。
 * ファイルサイズと種別のバリデーション機能を提供。
 *
 * @param props - FileUploadProps
 * @returns FileUploadコンポーネント
 *
 * @example
 * ```tsx
 * <FileUpload
 *   accept=".md,.pdf,.png,.jpg"
 *   maxSize={50 * 1024 * 1024}
 *   onFileSelect={(file) => console.log(file)}
 *   onError={(error) => console.error(error)}
 * />
 * ```
 */
export const FileUpload: React.FC<FileUploadProps> = ({
  accept,
  maxSize,
  onFileSelect,
  onError,
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  /**
   * ファイルのバリデーション
   *
   * @param file - 検証対象のファイル
   * @returns バリデーション結果（true: 成功、false: 失敗）
   */
  const validateFile = (file: File): boolean => {
    // サイズチェック
    if (file.size > maxSize) {
      onError(`ファイルサイズが上限（${formatFileSize(maxSize)}）を超えています`);
      return false;
    }

    // 種別チェック
    const acceptedExtensions = accept.split(',').map(ext => ext.trim().toLowerCase());
    const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;

    if (!acceptedExtensions.includes(fileExtension)) {
      onError(`無効なファイル形式です。対応形式: ${accept}`);
      return false;
    }

    return true;
  };

  /**
   * ドロップイベントハンドラー
   *
   * @param e - ドラッグイベント
   */
  const handleDrop = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const file = e.dataTransfer.files[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  };

  /**
   * ドラッグオーバーイベントハンドラー
   *
   * @param e - ドラッグイベント
   */
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  /**
   * ドラッグ離脱イベントハンドラー
   */
  const handleDragLeave = (): void => {
    setIsDragging(false);
  };

  /**
   * ファイル選択イベントハンドラー
   *
   * @param e - 入力変更イベント
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  };

  /**
   * ファイル選択をクリア
   */
  const clearFile = (): void => {
    setSelectedFile(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  /**
   * クリックイベントハンドラー
   */
  const handleClick = (): void => {
    if (!disabled) {
      inputRef.current?.click();
    }
  };

  /**
   * キーボードイベントハンドラー（アクセシビリティ対応）
   *
   * @param e - キーボードイベント
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>): void => {
    if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
      e.preventDefault();
      inputRef.current?.click();
    }
  };

  return (
    <div className="w-full">
      {/* ドラッグ&ドロップエリア */}
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="ファイルをアップロード"
        aria-disabled={disabled}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:border-blue-400 hover:bg-gray-50'}
        `}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
      >
        {/* アップロードアイコン */}
        <div className="mb-4">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
            aria-hidden="true"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* テキスト */}
        <div className="text-sm text-gray-600">
          <p className="font-medium">
            ファイルをドラッグ&ドロップ
          </p>
          <p className="mt-1">
            または
            <span className="text-blue-600 hover:text-blue-700 font-medium">
              {' '}クリックして選択
            </span>
          </p>
          <p className="mt-2 text-xs text-gray-500">
            対応形式: {accept.split(',').join(', ')} | 最大サイズ: {formatFileSize(maxSize)}
          </p>
        </div>
      </div>

      {/* 非表示のfile input */}
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        disabled={disabled}
        className="hidden"
        aria-hidden="true"
      />

      {/* 選択済みファイル表示 */}
      {selectedFile && (
        <div
          className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200 flex justify-between items-center"
          role="status"
          aria-live="polite"
        >
          <div className="flex-1 min-w-0">
            <p className="font-medium text-gray-900 truncate">
              {selectedFile.name}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {formatFileSize(selectedFile.size)}
            </p>
          </div>
          <button
            type="button"
            onClick={clearFile}
            disabled={disabled}
            className="ml-4 text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="ファイル選択をクリア"
          >
            <svg
              className="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

/**
 * ファイルサイズをフォーマット
 *
 * @param bytes - バイト数
 * @returns フォーマットされたファイルサイズ文字列
 *
 * @example
 * ```ts
 * formatFileSize(1024) // "1 KB"
 * formatFileSize(1048576) // "1 MB"
 * ```
 */
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};
