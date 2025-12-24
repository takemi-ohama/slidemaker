import React from 'react';

/**
 * プログレスバーのプロパティ
 */
export interface ProgressBarProps {
  /** タスクのステータス */
  status: 'pending' | 'processing' | 'completed' | 'failed';
  /** 進捗率（0.0-1.0）processingステータス時のみ有効 */
  progress?: number;
  /** 追加のメッセージ */
  message?: string;
  /** 追加のCSSクラス */
  className?: string;
}

/**
 * ステータス別の設定
 */
interface ProgressConfig {
  /** ステータスラベル */
  label: string;
  /** プログレスバーの色 */
  color: string;
  /** プログレスバーの幅 */
  width: string;
  /** アニメーションを有効にするか */
  animated: boolean;
}

/**
 * ProgressBar - タスク進捗状況の視覚的表示
 *
 * @example
 * ```tsx
 * // 準備中
 * <ProgressBar status="pending" />
 *
 * // 処理中（進捗率45%）
 * <ProgressBar status="processing" progress={0.45} />
 *
 * // 完了
 * <ProgressBar status="completed" message="スライド生成が完了しました" />
 *
 * // 失敗
 * <ProgressBar status="failed" message="エラーが発生しました" />
 * ```
 */
export const ProgressBar: React.FC<ProgressBarProps> = ({
  status,
  progress = 0,
  message,
  className = '',
}) => {
  // progress値の範囲チェック（0.0-1.0）
  const normalizedProgress = Math.max(0, Math.min(1, progress));

  /**
   * ステータス別の設定を取得
   */
  const getConfig = (): ProgressConfig => {
    switch (status) {
      case 'pending':
        return {
          label: '準備中...',
          color: 'bg-gray-500',
          width: '50%',
          animated: true,
        };
      case 'processing':
        return {
          label: `処理中... ${Math.round(normalizedProgress * 100)}%`,
          color: 'bg-blue-500',
          width: `${normalizedProgress * 100}%`,
          animated: false,
        };
      case 'completed':
        return {
          label: '完了 ✓',
          color: 'bg-green-500',
          width: '100%',
          animated: false,
        };
      case 'failed':
        return {
          label: '失敗 ✗',
          color: 'bg-red-500',
          width: '100%',
          animated: false,
        };
    }
  };

  const config = getConfig();

  // アクセシビリティ用の属性
  const ariaProps = {
    role: 'progressbar' as const,
    'aria-valuenow': status === 'processing' ? normalizedProgress * 100 : undefined,
    'aria-valuemin': status === 'processing' ? 0 : undefined,
    'aria-valuemax': status === 'processing' ? 100 : undefined,
    'aria-label': config.label,
  };

  return (
    <div className={`w-full ${className}`}>
      {/* ステータスラベル */}
      <div className="mb-2 text-sm font-medium text-gray-700">
        {config.label}
      </div>

      {/* プログレスバー */}
      <div className="w-full bg-gray-200 rounded-full h-6 overflow-hidden">
        <div
          className={`h-full ${config.color} transition-all duration-500 ease-out rounded-full
            ${config.animated ? 'animate-pulse' : ''}
          `}
          style={{ width: config.width }}
          {...ariaProps}
        />
      </div>

      {/* メッセージ */}
      {message && (
        <div className="mt-2 text-sm text-gray-600 text-center">
          {message}
        </div>
      )}
    </div>
  );
};
