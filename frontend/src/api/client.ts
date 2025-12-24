/**
 * API クライアント
 *
 * SlidemakerバックエンドAPIとの通信を管理するHTTPクライアント。
 * すべてのAPI呼び出しに対する統一されたインターフェースを提供します。
 *
 * @module api/client
 */

import {
  CreateSlideRequest,
  ConvertSlideRequest,
  TaskResponse,
  TaskStatusResponse,
  HealthCheckResponse,
} from '../types';

/**
 * API基底URL
 *
 * 環境変数から取得。デフォルトはローカル開発サーバー。
 */
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * APIエラークラス
 *
 * API呼び出しで発生したエラーを表します。
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public errorCode?: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * API クライアントクラス
 *
 * すべてのバックエンドAPIエンドポイントへのアクセスメソッドを提供します。
 * エラーハンドリング、タイムアウト、リトライロジックを統一的に管理します。
 */
class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * 汎用HTTPリクエストメソッド
   *
   * @param endpoint - APIエンドポイントパス（例: '/slides/create'）
   * @param options - fetchオプション
   * @returns レスポンスデータ
   * @throws {ApiError} HTTPエラーが発生した場合
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        let errorCode: string | undefined;

        try {
          const errorData = await response.json();
          errorMessage = errorData.error_message || errorMessage;
          errorCode = errorData.error_code;
        } catch {
          // JSON解析失敗時はデフォルトメッセージを使用
        }

        throw new ApiError(errorMessage, response.status, errorCode);
      }

      return await response.json();
    } catch (err) {
      if (err instanceof ApiError) {
        throw err;
      }

      // ネットワークエラー等
      throw new ApiError(
        err instanceof Error ? err.message : 'Network error occurred',
        undefined,
        'NETWORK_ERROR',
      );
    }
  }

  /**
   * ヘルスチェック
   *
   * サービスの健全性を確認します。
   *
   * @returns ヘルスチェック結果
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    return this.request<HealthCheckResponse>('/health');
  }

  /**
   * スライド作成タスクを開始
   *
   * Markdownコンテンツから新しいPowerPointスライドを生成します。
   *
   * @param request - スライド作成リクエスト
   * @returns タスクレスポンス
   */
  async createSlide(request: CreateSlideRequest): Promise<TaskResponse> {
    return this.request<TaskResponse>('/slides/create', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * スライド変換タスクを開始
   *
   * PDF/画像ファイルをPowerPointスライドに変換します。
   *
   * @param request - スライド変換リクエスト
   * @returns タスクレスポンス
   */
  async convertSlide(request: ConvertSlideRequest): Promise<TaskResponse> {
    return this.request<TaskResponse>('/slides/convert', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * タスクステータスを取得
   *
   * 指定されたタスクIDのステータスと結果を取得します。
   *
   * @param taskId - タスクID（UUID形式）
   * @returns タスクステータスレスポンス
   */
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    return this.request<TaskStatusResponse>(`/tasks/${taskId}`);
  }
}

/**
 * API クライアントのシングルトンインスタンス
 *
 * アプリケーション全体で共有されるAPIクライアントインスタンスです。
 *
 * @example
 * ```ts
 * import apiClient from './api/client';
 *
 * const response = await apiClient.createSlide({
 *   content: '# My Presentation\n...',
 * });
 * ```
 */
const apiClient = new ApiClient();

export default apiClient;
