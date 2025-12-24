/**
 * ResultViewer コンポーネントのテスト
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ResultViewer } from './ResultViewer';
import type { TaskResult } from '../types';

describe('ResultViewer', () => {
  const mockResult: TaskResult = {
    output_url: 'https://example.com/test.pptx',
    output_filename: 'test_presentation.pptx',
    file_size: 2048000, // 2MB
    page_count: 10,
  };

  it('正常にレンダリングされる', () => {
    render(<ResultViewer result={mockResult} />);

    // 成功メッセージが表示される
    expect(
      screen.getByText('スライドが正常に生成されました！')
    ).toBeInTheDocument();

    // ファイル情報が表示される
    expect(screen.getByText('test_presentation.pptx')).toBeInTheDocument();
    expect(screen.getByText('2.00 MB')).toBeInTheDocument();
    expect(screen.getByText('10 ページ')).toBeInTheDocument();

    // ダウンロードボタンが表示される
    const downloadLink = screen.getByRole('link', {
      name: /PowerPointファイルをダウンロード/i,
    });
    expect(downloadLink).toHaveAttribute('href', mockResult.output_url);
    expect(downloadLink).toHaveAttribute('target', '_blank');
    expect(downloadLink).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('ファイルサイズが正しくフォーマットされる', () => {
    const testCases = [
      { file_size: 0, expected: '0 Bytes' },
      { file_size: 1024, expected: '1.00 KB' },
      { file_size: 1048576, expected: '1.00 MB' },
      { file_size: 1073741824, expected: '1.00 GB' },
    ];

    testCases.forEach(({ file_size, expected }) => {
      const { unmount } = render(
        <ResultViewer result={{ ...mockResult, file_size }} />
      );
      expect(screen.getByText(expected)).toBeInTheDocument();
      unmount();
    });
  });

  it('onResetが指定されている場合、リセットボタンが表示される', () => {
    const handleReset = vi.fn();
    render(<ResultViewer result={mockResult} onReset={handleReset} />);

    const resetButton = screen.getByRole('button', {
      name: /新しいスライドを作成/i,
    });
    expect(resetButton).toBeInTheDocument();

    // リセットボタンをクリック
    fireEvent.click(resetButton);
    expect(handleReset).toHaveBeenCalledTimes(1);
  });

  it('onResetが指定されていない場合、リセットボタンは表示されない', () => {
    render(<ResultViewer result={mockResult} />);

    const resetButton = screen.queryByRole('button', {
      name: /新しいスライドを作成/i,
    });
    expect(resetButton).not.toBeInTheDocument();
  });

  it('カスタムclassNameが適用される', () => {
    const { container } = render(
      <ResultViewer result={mockResult} className="custom-class" />
    );

    const rootElement = container.firstChild as HTMLElement;
    expect(rootElement).toHaveClass('custom-class');
  });

  it('アクセシビリティ属性が正しく設定されている', () => {
    render(<ResultViewer result={mockResult} />);

    // region role
    const region = screen.getByRole('region', {
      name: 'スライド生成結果',
    });
    expect(region).toBeInTheDocument();

    // alert role
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveAttribute('aria-live', 'polite');
  });

  it('注意事項が表示される', () => {
    render(<ResultViewer result={mockResult} />);

    expect(
      screen.getByText('ダウンロードリンクは7日間有効です')
    ).toBeInTheDocument();
  });

  it('レスポンシブデザイン用のクラスが適用されている', () => {
    const { container } = render(<ResultViewer result={mockResult} />);

    // flex-colとsm:flex-rowが適用されているか確認
    const dlElements = container.querySelectorAll('dl > div');
    dlElements.forEach((element) => {
      expect(element).toHaveClass('flex');
      expect(element.className).toContain('sm:flex-row');
    });
  });
});
