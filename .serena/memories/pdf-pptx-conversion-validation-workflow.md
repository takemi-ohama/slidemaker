# PDF→PowerPoint変換の検証・改善ワークフロー

## 概要

PDF→PowerPoint変換機能の品質を継続的に改善するための検証ワークフローです。
生成されたPowerPointをキャプチャ画像化し、元PDFと比較して問題点を把握・修正するサイクルを回します。

## 必要なツール

### 1. LibreOffice Impress（PowerPoint→PDF変換）

**インストール**:
```bash
sudo apt-get update
sudo apt-get install -y libreoffice-impress --no-install-recommends
```

**用途**: PowerPointファイルをPDFに変換（画像化の前段階）

**使用例**:
```bash
libreoffice --headless --convert-to pdf --outdir /path/to/output /path/to/presentation.pptx
```

### 2. pdf2image（PDF→画像変換）

**インストール**: プロジェクトの依存関係に含まれている

**前提条件**: poppler-utils
```bash
# Ubuntu/Debian
sudo apt-get install poppler-utils

# macOS
brew install poppler
```

**使用例**:
```python
from pdf2image import convert_from_path

images = convert_from_path('presentation.pdf', dpi=150)
for i, image in enumerate(images, 1):
    image.save(f'slide_{i:03d}.png', 'PNG')
```

### 3. Office-PowerPoint-MCP-Server（PowerPoint検証）

**設定**: `.mcp.json` に設定済み

**主要機能**:
- `open_presentation`: PowerPointを開く
- `get_presentation_info`: プレゼンテーション情報取得
- `get_slide_info`: スライド情報取得（要素の座標・サイズ）
- `extract_slide_text`: テキスト抽出

## 検証・改善ワークフロー

### ステップ1: PowerPoint生成

```bash
uv run slidemaker convert samples/input.pdf -o output/generated.pptx -v
```

### ステップ2: PowerPoint検証（座標チェック）

```python
# PowerPoint MCPで座標を確認
mcp__powerpoint__open_presentation(file_path="/path/to/generated.pptx")
mcp__powerpoint__get_slide_info(presentation_id="...", slide_index=0)
```

**確認ポイント**:
- 要素がスライド境界内に収まっているか（width: 9144000, height: 5143500 EMU）
- テキスト・画像要素の座標が妥当か

### ステップ3: キャプチャ画像生成

```bash
# PowerPointをPDFに変換
cd output/pptx_captures
libreoffice --headless --convert-to pdf --outdir . /path/to/generated.pptx

# PDFを画像に変換
cd /path/to/project
uv run python -c "
from pdf2image import convert_from_path

pdf_path = 'output/pptx_captures/generated.pdf'
images = convert_from_path(pdf_path, dpi=150)

for i, image in enumerate(images, 1):
    output_path = f'output/pptx_captures/slide_{i:03d}.png'
    image.save(output_path, 'PNG')
    print(f'Saved: {output_path}')
"
```

### ステップ4: 画像比較（元PDFと生成PPTX）

```python
# 元PDFの画像（変換時に自動保存）
output/temp/pdf_pages/page_001.png

# 生成PPTXのキャプチャ
output/pptx_captures/slide_001.png

# Readツールで両方を読み込んで目視比較
```

**比較ポイント**:
- 画像要素が完全に表示されているか
- テキストが切れていないか
- レイアウトが元PDFに近いか
- 図表の全要素（ボックス、矢印、ラベル等）が含まれているか

**推奨アクション**:
- LLMに両方の画像を提示し、具体的な差異（「画像の下部が20px切れている」「フォントサイズが1.5倍大きい」等）を指摘させる。
- 定量的な差異（ピクセル単位のズレ）を記録する。

### ステップ5: 問題点の特定

**典型的な問題**:

1. **座標スケールエラー**
   - 症状: 要素がスライド境界外に配置
   - 確認: PowerPoint MCP の `get_slide_info` で座標をチェック

2. **画像要素の部分欠落**
   - 症状: 図表の一部しか表示されない
   - 原因: LLMが画像要素の境界を過小評価

3. **テキスト切れ**
   - 症状: テキストの末尾が切れている
   - 原因: テキストボックスのサイズ不足

### ステップ6: コード修正

**主要修正箇所**:

1. **座標変換**: `src/slidemaker/image_processing/analyzer.py`
```python
# slide_dimensions: スライドサイズをEMU変換に合わせる
slide_dimensions: tuple[int, int] = (960, 540)  # 9144000 / 9525
```

2. **画像切り出し**: `src/slidemaker/workflows/conversion.py`
```python
# padding_ratio: LLM座標の過小評価を補正
padding_ratio = 0.25  # 25%の余白を追加
padding_x = int(width_px * padding_ratio)
padding_y = int(height_px * padding_ratio)

x_px = max(0, x_px - padding_x)
y_px = max(0, y_px - padding_y)
width_px = min(img_width - x_px, width_px + 2 * padding_x)
height_px = min(img_height - y_px, height_px + 2 * padding_y)
```

3. **プロンプト改善**: `src/slidemaker/llm/prompts/image_processing.py`
```python
# 画像要素の完全検出を明示的に指示
CRITICAL FOR IMAGE ELEMENTS:
- Include the COMPLETE boundaries of all graphic elements
- For complex diagrams, specify coordinates that encompass ALL parts
- When in doubt, make the image boundaries LARGER rather than smaller
```

### ステップ7: 再生成と検証

```bash
# 修正後に再生成
uv run slidemaker convert samples/input.pdf -o output/generated_v2.pptx -v
```

ステップ2〜6を繰り返し、問題がなくなるまで改善を続ける。

### ステップ8: レポート作成

各イテレーションの終了時に、課題と改善案をまとめたレポートを作成します。

**出力先**: `output/reports/report_YYYYMMDD_HHMM.md`

**レポート構成**:
1. **概要**: テスト対象ファイル、バージョン情報
2. **比較結果**:
   - スライドごとの差異（PDF vs PPTX）
   - フォントサイズ、画像クロッピング、レイアウトの評価
3. **特定された課題**:
   - 重大な不具合（見切れ、重なり）
   - デザイン上の乖離
4. **実施した修正**:
   - コード変更点
   - プロンプト変更点
5. **次回の改善案**:
   - 残存する課題への対策

```markdown
# 検証レポート: MDX_v4_gemini3_fixed.pptx

## 1. 概要
- **日時**: 2025-12-27
- **入力**: samples/MDX_Strategic_Engine_2026.pdf
- **出力**: output/MDX_v4_gemini3_fixed.pptx

## 2. 比較結果
- **スライド2**: アイコン画像の高さがPDFより短い（PDF: 265px, PPTX: 162px）。下部が見切れている可能性あり。
- **スライド3**: フォントサイズは適正化されたが、画像とテキストの重なり（16px）が発生。

## 3. 実施した修正
- 画像パディングを非対称に変更（下部50%追加）。
- フォントサイズ係数を0.5に縮小。
```

## ベストプラクティス

### 1. バージョン管理

生成ファイルに `_v2`, `_v3`, `_final` のようなサフィックスをつけて、改善履歴を追跡する。

### 2. 複数ページの検証

最初の3〜5ページだけを画像化して素早く確認し、問題が解消されたら全ページを確認する。

```python
# 最初の3枚のみ
for i, image in enumerate(images[:3], 1):
    image.save(f'slide_{i:03d}.png', 'PNG')
```

### 3. 定量的な評価

PowerPoint MCPで取得した座標情報をログ出力し、数値的に妥当性を検証する。

```python
# スライド境界チェック
slide_width = 9144000
slide_height = 5143500

for shape in shapes:
    if shape['left'] < 0 or shape['left'] + shape['width'] > slide_width:
        print(f"⚠️ Horizontal overflow: {shape}")
    if shape['top'] < 0 or shape['top'] + shape['height'] > slide_height:
        print(f"⚠️ Vertical overflow: {shape}")
```

## トラブルシューティング

### LibreOfficeのフォントエラー

```bash
# フォントキャッシュの再構築
fc-cache -f -v
```

### pdf2imageのエラー

```bash
# poppler-utilsのバージョン確認
pdfinfo -v

# 再インストール
sudo apt-get install --reinstall poppler-utils
```

### PowerPoint MCPの接続エラー

```bash
# Claude Codeを再起動して.mcp.jsonを再読み込み
```

## まとめ

このワークフローにより、PDF→PowerPoint変換の品質を継続的に改善できます。
特に画像要素の検出精度とレイアウト再現性の向上に有効です。
