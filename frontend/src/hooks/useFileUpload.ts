/**
 * useFileUploadフック
 *
 * ファイルアップロードとBase64エンコードの処理を行うカスタムフック。
 *
 * @module hooks/useFileUpload
 *
 * @example
 * ```tsx
 * const { file, encodedData, isEncoding, error, handleFileSelect, clearFile } = useFileUpload();
 *
 * const onFileChange = (event: ChangeEvent<HTMLInputElement>) => {
 *   const selectedFile = event.target.files?.[0];
 *   if (selectedFile) {
 *     await handleFileSelect(selectedFile);
 *   }
 * };
 * ```
 */

import { useState } from 'react';

/**
 * useFileUploadフックの戻り値型
 */
export interface UseFileUploadReturn {
  /** 選択されたファイルオブジェクト */
  file: File | null;

  /** Base64エンコードされたファイルデータ（data:...の部分を除外した純粋なBase64文字列） */
  encodedData: string | null;

  /** エンコード処理中かどうか */
  isEncoding: boolean;

  /** エラーメッセージ（エラーがない場合はnull） */
  error: string | null;

  /**
   * ファイルを選択してBase64エンコードを実行
   *
   * @param file - エンコードするファイル
   * @returns エンコード完了を待つPromise
   */
  handleFileSelect: (file: File) => Promise<void>;

  /**
   * ファイルとステートをクリア
   */
  clearFile: () => void;
}

/**
 * ファイルアップロードとBase64エンコードを管理するカスタムフック
 *
 * FileReaderを使用してファイルをBase64エンコードし、結果を状態管理します。
 * エンコード中のローディング状態、エラーハンドリング、クリア機能を提供します。
 *
 * @returns {UseFileUploadReturn} ファイルアップロード関連のステートと関数
 *
 * @example
 * ```tsx
 * const FileUploadComponent = () => {
 *   const { file, encodedData, isEncoding, error, handleFileSelect, clearFile } = useFileUpload();
 *
 *   const handleChange = async (e: ChangeEvent<HTMLInputElement>) => {
 *     const selectedFile = e.target.files?.[0];
 *     if (selectedFile) {
 *       await handleFileSelect(selectedFile);
 *     }
 *   };
 *
 *   return (
 *     <div>
 *       <input type="file" onChange={handleChange} disabled={isEncoding} />
 *       {isEncoding && <p>エンコード中...</p>}
 *       {error && <p>エラー: {error}</p>}
 *       {file && <p>選択ファイル: {file.name}</p>}
 *       {encodedData && <button onClick={clearFile}>クリア</button>}
 *     </div>
 *   );
 * };
 * ```
 */
export function useFileUpload(): UseFileUploadReturn {
  const [file, setFile] = useState<File | null>(null);
  const [encodedData, setEncodedData] = useState<string | null>(null);
  const [isEncoding, setIsEncoding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * ファイルを選択してBase64エンコードを実行
   *
   * FileReaderを使用して非同期的にファイルを読み込み、Base64エンコードします。
   * エンコード結果から "data:..." プレフィックスを除去し、純粋なBase64文字列のみを保存します。
   *
   * @param selectedFile - エンコードするファイル
   * @throws {Error} ファイル読み込みに失敗した場合
   */
  const handleFileSelect = async (selectedFile: File): Promise<void> => {
    setIsEncoding(true);
    setError(null);

    try {
      const reader = new FileReader();

      // FileReaderの非同期処理をPromiseでラップ
      const result = await new Promise<string>((resolve, reject) => {
        reader.onload = () => {
          const base64 = reader.result as string;
          // "data:image/png;base64,..." → "..."の部分を抽出
          const encoded = base64.split(',')[1];
          resolve(encoded);
        };

        reader.onerror = () => {
          reject(new Error('Failed to read file'));
        };

        reader.readAsDataURL(selectedFile);
      });

      setFile(selectedFile);
      setEncodedData(result);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      setError(errorMessage);
      // エラー時はファイル情報もクリア
      setFile(null);
      setEncodedData(null);
    } finally {
      setIsEncoding(false);
    }
  };

  /**
   * すべてのステートをリセット
   *
   * ファイル、エンコードデータ、エラーメッセージをクリアします。
   */
  const clearFile = () => {
    setFile(null);
    setEncodedData(null);
    setError(null);
  };

  return {
    file,
    encodedData,
    isEncoding,
    error,
    handleFileSelect,
    clearFile,
  };
}
