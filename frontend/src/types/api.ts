/**
 * TypeScript型定義 - API スキーマ
 *
 * Pythonスキーマ (src/slidemaker/api/schemas/) に対応するTypeScript型定義です。
 * すべての型はPythonのPydanticモデルから自動生成されたJSON Schemaに基づいています。
 */

// ==================== リクエスト型 ====================

/**
 * スライド設定スキーマ
 *
 * APIリクエストで使用される簡易スライド設定。
 * 省略されたフィールドにはデフォルト値が適用されます。
 */
export interface SlideConfigSchema {
  /** スライドサイズ形式 (16:9 ワイドスクリーンまたは 4:3 標準) */
  size?: '16:9' | '4:3';

  /** スライド幅（ピクセル、1-10000） */
  width?: number;

  /** スライド高さ（ピクセル、1-10000） */
  height?: number;

  /** 背景色（Hex形式、例: '#FFFFFF'） */
  background_color?: string;

  /** デフォルトフォントファミリー名 */
  default_font_family?: string;

  /** デフォルトフォントサイズ（ポイント、1-100） */
  default_font_size?: number;
}

/**
 * スライド作成リクエスト
 *
 * Markdownコンテンツからスライドを生成するためのリクエスト。
 * LLM構成を使用してPowerPointスライドを生成します。
 */
export interface CreateSlideRequest {
  /** スライド生成用Markdownコンテンツ（1-50000文字） */
  content: string;

  /** オプションのスライド設定。省略時はデフォルト値を使用 */
  config?: SlideConfigSchema;

  /** オプションの出力ファイル名（最大255文字）。省略時は自動生成 */
  output_filename?: string;
}

/**
 * スライド変換リクエスト
 *
 * PDF/画像ファイルをPowerPointスライドに変換するためのリクエスト。
 * LLMを使用してPDFまたは画像を分析し、編集可能なプレゼンテーションとして再構築します。
 */
export interface ConvertSlideRequest {
  /** Base64エンコードされたファイルデータ（PDFまたは画像） */
  file_data: string;

  /** ファイルタイプ: PDFファイルは 'pdf'、画像ファイルは 'image' */
  file_type: 'pdf' | 'image';

  /** オプションのスライド設定。省略時はデフォルト値を使用 */
  config?: SlideConfigSchema;

  /** オプションの出力ファイル名（最大255文字）。省略時は自動生成 */
  output_filename?: string;
}

// ==================== レスポンス型 ====================

/**
 * タスクステータス
 *
 * タスクの現在の処理状態を表します。
 */
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

/**
 * タスク作成レスポンス
 *
 * タスク作成APIエンドポイントからのレスポンス。
 * タスクの基本情報（ID、ステータス、作成日時等）を含みます。
 */
export interface TaskResponse {
  /** タスクID（UUID形式） */
  task_id: string;

  /** タスクステータス */
  status: TaskStatus;

  /** ステータスメッセージ */
  message: string;

  /** タスク作成日時（UTC、ISO 8601形式） */
  created_at: string;

  /** 最終更新日時（UTC、ISO 8601形式） */
  updated_at: string;
}

/**
 * タスク結果
 *
 * タスクが正常に完了した場合の結果情報。
 * 生成されたPowerPointファイルのメタデータを含みます。
 */
export interface TaskResult {
  /** 生成されたPowerPointファイルのS3署名付きURL（有効期限7日間） */
  output_url: string;

  /** 出力ファイル名 */
  output_filename: string;

  /** ファイルサイズ（バイト単位） */
  file_size: number;

  /** スライド枚数 */
  page_count: number;
}

/**
 * エラー詳細
 *
 * タスクが失敗した場合のエラー詳細情報。
 * 標準化されたエラーコードとメッセージを含みます。
 *
 * 標準エラーコード:
 * - VALIDATION_ERROR: 入力データバリデーションエラー
 * - LLM_ERROR: LLM API呼び出しエラー
 * - STORAGE_ERROR: ストレージ（S3等）アクセスエラー
 * - TIMEOUT_ERROR: タイムアウトエラー
 * - INTERNAL_ERROR: 内部エラー
 */
export interface ErrorDetail {
  /** エラーコード */
  error_code: string;

  /** ユーザーフレンドリーなエラーメッセージ */
  error_message: string;

  /** 追加の詳細情報（オプション） */
  details?: Record<string, unknown>;
}

/**
 * タスクステータスレスポンス
 *
 * タスクステータス取得APIエンドポイントからのレスポンス。
 * TaskResponseを継承し、タスクの結果やエラー情報を追加します。
 *
 * ステータス別のフィールド:
 * - pending: result=null, error=null, progress=null
 * - processing: result=null, error=null, progress=0.0-1.0
 * - completed: result=TaskResult, error=null, progress=null
 * - failed: result=null, error=ErrorDetail, progress=null
 */
export interface TaskStatusResponse extends TaskResponse {
  /** タスク結果（status='completed'の場合のみ） */
  result?: TaskResult;

  /** エラー詳細（status='failed'の場合のみ） */
  error?: ErrorDetail;

  /** 進捗率（status='processing'の場合のみ、0.0-1.0） */
  progress?: number;
}

/**
 * ヘルスチェックレスポンス
 *
 * サービスの健全性チェック結果。
 * 全体のステータスと各コンポーネントの状態を含みます。
 *
 * ステータス値:
 * - ok: すべてのコンポーネントが正常
 * - degraded: 一部のコンポーネントに問題あり（サービスは継続）
 * - down: サービス停止中
 */
export interface HealthCheckResponse {
  /** サービス全体のステータス */
  status: 'ok' | 'degraded' | 'down';

  /** アプリケーションバージョン */
  version: string;

  /** ヘルスチェック実行日時（UTC、ISO 8601形式） */
  timestamp: string;

  /** 各種チェック結果 */
  checks: Record<string, boolean>;
}
