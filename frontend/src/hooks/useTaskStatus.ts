/**
 * useTaskStatusフック
 *
 * タスクステータスのポーリング取得を管理するカスタムフック。
 *
 * @module hooks/useTaskStatus
 *
 * @example
 * ```tsx
 * const { taskStatus, isPolling, error, startPolling, stopPolling } = useTaskStatus(2000);
 *
 * // タスク作成後にポーリング開始
 * const handleCreateSlide = async () => {
 *   const response = await apiClient.createSlide({ content: '...' });
 *   startPolling(response.task_id);
 * };
 *
 * // 完了時に自動停止
 * useEffect(() => {
 *   if (taskStatus?.status === 'completed') {
 *     console.log('Task completed!', taskStatus.result);
 *   }
 * }, [taskStatus]);
 * ```
 */

import { useState, useEffect, useRef } from 'react';
import apiClient from '../api/client';
import { TaskStatusResponse } from '../types';

/**
 * useTaskStatusフックの戻り値型
 */
export interface UseTaskStatusReturn {
  /** 現在のタスクステータス */
  taskStatus: TaskStatusResponse | null;

  /** ポーリング実行中かどうか */
  isPolling: boolean;

  /** エラーメッセージ（エラーがない場合はnull） */
  error: string | null;

  /**
   * タスクステータスのポーリングを開始
   *
   * @param taskId - 監視するタスクID（UUID形式）
   */
  startPolling: (taskId: string) => void;

  /**
   * ポーリングを停止
   */
  stopPolling: () => void;
}

/**
 * デフォルトのポーリング間隔（ミリ秒）
 */
const DEFAULT_INTERVAL_MS = 2000;

/**
 * タスクステータスのポーリング取得を管理するカスタムフック
 *
 * 指定されたタスクIDのステータスを定期的に取得し、完了または失敗時に自動停止します。
 * コンポーネントのアンマウント時には自動的にポーリングをクリーンアップします。
 *
 * @param intervalMs - ポーリング間隔（ミリ秒）。デフォルトは2000ms（2秒）
 * @returns {UseTaskStatusReturn} タスクステータス関連のステートと関数
 *
 * @example
 * ```tsx
 * const TaskMonitor = () => {
 *   const { taskStatus, isPolling, error, startPolling, stopPolling } = useTaskStatus(3000);
 *
 *   const createTask = async () => {
 *     const response = await apiClient.createSlide({
 *       content: '# My Presentation\nSlide content...',
 *     });
 *     startPolling(response.task_id);
 *   };
 *
 *   return (
 *     <div>
 *       <button onClick={createTask} disabled={isPolling}>
 *         Create Slide
 *       </button>
 *       {isPolling && <p>Processing...</p>}
 *       {taskStatus && (
 *         <div>
 *           <p>Status: {taskStatus.status}</p>
 *           {taskStatus.progress !== undefined && (
 *             <progress value={taskStatus.progress} max={1} />
 *           )}
 *         </div>
 *       )}
 *       {error && <p>Error: {error}</p>}
 *     </div>
 *   );
 * };
 * ```
 */
export function useTaskStatus(intervalMs: number = DEFAULT_INTERVAL_MS): UseTaskStatusReturn {
  const [taskStatus, setTaskStatus] = useState<TaskStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // インターバルIDを保持するRef（レンダリング間で保持）
  const intervalIdRef = useRef<number | null>(null);
  // 監視中のタスクIDを保持するRef
  const taskIdRef = useRef<string | null>(null);

  /**
   * タスクステータスを取得
   *
   * APIからタスクステータスを取得し、完了または失敗時に自動停止します。
   *
   * @param taskId - タスクID
   */
  const fetchTaskStatus = async (taskId: string): Promise<void> => {
    try {
      const status = await apiClient.getTaskStatus(taskId);
      setTaskStatus(status);

      // 完了または失敗時に自動停止
      if (status.status === 'completed' || status.status === 'failed') {
        stopPolling();
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch task status';
      setError(errorMessage);
      stopPolling();
    }
  };

  /**
   * タスクステータスのポーリングを開始
   *
   * 指定されたタスクIDのステータスを定期的に取得します。
   * 初回は即座に取得し、その後は指定された間隔で取得を続けます。
   *
   * @param taskId - 監視するタスクID
   */
  const startPolling = (taskId: string): void => {
    // 既存のポーリングをクリア
    if (intervalIdRef.current !== null) {
      stopPolling();
    }

    taskIdRef.current = taskId;
    setIsPolling(true);
    setError(null);

    // 初回取得（即座に実行）
    fetchTaskStatus(taskId);

    // 定期取得
    intervalIdRef.current = window.setInterval(() => {
      if (taskIdRef.current) {
        fetchTaskStatus(taskIdRef.current);
      }
    }, intervalMs);
  };

  /**
   * ポーリングを停止
   *
   * 現在実行中のポーリングを停止し、関連するステートをクリアします。
   */
  const stopPolling = (): void => {
    if (intervalIdRef.current !== null) {
      clearInterval(intervalIdRef.current);
      intervalIdRef.current = null;
    }
    setIsPolling(false);
    taskIdRef.current = null;
  };

  /**
   * クリーンアップ処理
   *
   * コンポーネントのアンマウント時にポーリングを自動停止します。
   * メモリリークを防止するための重要な処理です。
   */
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, []); // 空の依存配列 → マウント時とアンマウント時のみ実行

  return {
    taskStatus,
    isPolling,
    error,
    startPolling,
    stopPolling,
  };
}
