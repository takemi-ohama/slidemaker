# PDF→PPTX変換 縮尺問題修正計画（96 DPI基準対応版）

**作成日**: 2025-12-26
**更新日**: 2025-12-26（96 DPI基準を反映）
**対象**: PDF→PowerPoint変換機能の座標系不整合修正
**重要な発見**: PDFの実サイズは**1376 x 768 pts**であり、**96 DPI基準で1835 x 1024 px**に変換すべき

---

## 📊 重要な発見：PDFの実サイズ

### PDFメタデータから判明した事実

```
Page size: 1376 x 768 pts (PDF points)
Aspect Ratio: 1.791667
```

**これまでの誤解**:
- ❌ PDFサイズ = 3823 x 2134 px（pdf2imageの150 DPI変換後のサイズ）
- ✅ PDFサイズ = 1376 x 768 pts（PDFの実際の定義サイズ）

### PowerPoint 96 DPI基準での正確な変換

**PDF定義**: 1 pt = 1/72 inch

```
1376 pts / 72 = 19.1111 inches
768 pts / 72 = 10.6667 inches
```

**PowerPoint内部基準**: 1 inch = 96 px @ 96 DPI

```
19.1111 in × 96 = 1834.67 px → 1835 px
10.6667 in × 96 = 1024.00 px → 1024 px
```

**結論**: PDFを96 DPI基準でPowerPointに変換すると、**1835 x 1024 px**が正確なサイズ。

---

## 方針の再決定

### 変更前の方針（誤り）
- PowerPoint標準16:9（1280×720 px）に統一
- または、推測された3823×2134の比率（1280×715 px）を維持
- 縦横比: 1.7778（16:9）または 1.7915（3823:2134）

### 変更後の方針（96 DPI基準、推奨）
- **PDFの実サイズ（1376×768 pts）を96 DPI基準で変換**
- **実装サイズ: 1835 x 1024 px**
- **縦横比: 1.791016**（PDF実サイズの1.791667とほぼ一致、誤差0.036%）
- **PowerPoint内部表現と完全一致**
- **歪みゼロ、座標変換不要**

### サンプルPDFの正確な値

- **ファイル**: samples/MDX_Strategic_Engine_2026.pdf
- **ページサイズ（PDF定義）**: 1376 x 768 pts
- **ページサイズ（96 DPI）**: 1835 x 1024 px
- **ページサイズ（150 DPI）**: 2867 x 1600 px（pdf2imageでの変換結果）
- **縦横比**: 1.791667
- **ページ数**: 15ページ
- **16:9との差異**: +0.78%（僅かに横長）

### 選択した理由（96 DPI基準）

1. **PowerPoint内部表現と完全一致**: 96 DPIはPowerPointの内部基準
2. **座標変換不要**: パーセンテージ→ピクセル→EMUの単純変換のみ
3. **EMU変換が正確**: 1 px = 9,525 EMU（python-pptxの実装）
4. **縦横比の精度**: PDF実サイズとの誤差0.036%（無視できるレベル）
5. **歪みゼロ**: PowerPointの内部基準に基づくため、レンダリング歪みなし

---

## 0. PowerPoint 96 DPI基準の理解（必読）

### 0.1 PowerPointの内部表現

PowerPointは**内部的に96 DPI（ppi）基準**でレイアウトされています（[issues/REPORT01.md](issues/REPORT01.md)より）。

**基本換算式**:
```
1 inch = 96 px @ 96 DPI (PowerPoint内部基準)
1 inch = 914,400 EMU (PowerPoint内部単位: English Metric Unit)
1 px = 914,400 / 96 = 9,525 EMU
1 cm ≈ 37.795 px @ 96 DPI
```

### 0.2 PDF points → PowerPoint pixels

**PDF定義**: 1 pt (point) = 1/72 inch

**変換式**:
```
1 pt = 1/72 inch
1 inch = 96 px @ 96 DPI
∴ 1 pt = (1/72) × 96 = 1.333... px
```

**サンプルPDFの変換例**:
```
PDF: 1376 pts × 768 pts

Step 1: pts → inches
  1376 pts ÷ 72 = 19.1111 inches
  768 pts ÷ 72 = 10.6667 inches

Step 2: inches → pixels (96 DPI)
  19.1111 in × 96 = 1834.67 px → 1835 px
  10.6667 in × 96 = 1024.00 px → 1024 px

結果: 1835 px × 1024 px @ 96 DPI
```

### 0.3 EMU単位（PowerPoint内部）

**EMU (English Metric Unit)** はPowerPointが内部的に使用する単位です。

**変換式**:
```
1 inch = 914,400 EMU
1 px @ 96 DPI = 914,400 / 96 = 9,525 EMU
```

**1835×1024 px のEMU値**:
```
1835 px × 9,525 = 17,478,375 EMU
1024 px × 9,525 = 9,753,600 EMU
```

python-pptxは`Inches()`関数で自動的にEMUに変換します:
```python
from pptx.util import Inches

width_inches = 1835 / 96.0  # 19.11458...
height_inches = 1024 / 96.0  # 10.66666...

prs.slide_width = Inches(width_inches)  # → 17,478,375 EMU
prs.slide_height = Inches(height_inches)  # → 9,753,600 EMU
```

### 0.4 フォントサイズ（pt）とピクセルの関係

**96 DPI基準では**:
```
1 pt = 96/72 px = 1.333... px
```

**例（1024px高さのスライド）**:
```
5% of 1024px = 51.2 px = 51.2 / 1.333 = 38.4 pt ≈ 38pt font
3% of 1024px = 30.72 px = 30.72 / 1.333 = 23.04 pt ≈ 23pt font
2% of 1024px = 20.48 px = 20.48 / 1.333 = 15.36 pt ≈ 15pt font
```

### 0.5 重要な結論

**このPDFの正確な変換サイズ（96 DPI基準）**:
- **1835 px × 1024 px**
- 縦横比: 1.791016（PDF定義の1.791667とほぼ一致、誤差0.036%）
- PowerPoint内部表現（96 DPI、EMU単位）と完全一致
- 座標変換が最小限（パーセンテージ→ピクセル→EMUのみ）

**これまでの実装の誤り**:
- ❌ 1280×720（PowerPoint標準16:9を推測）
- ❌ 1280×715（pdf2imageの150 DPI出力3823×2134から推測した比率）
- ❌ 960×540（謎の基準値）

**正解**:
- ✅ **1835×1024**（PDFの実サイズ1376×768 ptsを96 DPI基準で変換）

---

## 1. 問題の診断

### 1.1 ユーザー報告の問題

> 「PDF→PPTX変換の縮尺把握が世代を進めるごとに悪化している」
> 「正しいスケールでのフォントサイズ把握とトリミングができていない」

### 1.2 調査で特定された根本原因

**致命的な座標系の不整合**が複数のモジュール間で発生しています。

#### 問題①：PDF→画像変換サイズとLLMへの指示サイズの不一致

| モジュール | 設定値 | 問題点 |
|---|---|---|
| **ImageLoader** | 1280×720 px | PDF→画像変換時のサイズ |
| **LLMプロンプト** | 1920×1080 px | LLMに伝えるスライドサイズ（デフォルト） |
| **ImageAnalyzer** | 960×540 px | 座標正規化の基準サイズ |
| **ConversionWorkflow** | 960×540 px | 画像切り出しの基準サイズ |
| **実際のPDF** | 3823×2134 px | 元のPDFサイズ（縦横比1.7915） |

**結果**: LLMは1920×1080の画像を分析していると思い込み、座標を返すが、実際の画像は1280×720。さらに座標正規化では960×540を基準としているため、**複数の縮尺変換が重なり、世代を進めるごとに誤差が累積**。また、元のPDFサイズ（3823×2134）とも一致していないため、縦横比の歪みも発生。

#### 問題②：座標変換の複雑さ

現在のフロー:
```
PDF (3823×2134) → 1280×720 画像 (ImageLoader) ← 縦横比変化！
  ↓
LLMに「1920×1080の画像」と指示 (プロンプト)
  ↓
LLMがパーセンテージ座標を返す
  ↓
960×540ピクセル座標に変換 (ImageAnalyzer)
  ↓
1280×720画像ピクセル座標に再変換 (ConversionWorkflow)
  ↓
PowerPointに配置 (EMU単位)
```

**問題点**:
- **縦横比の変化**: 3823:2134 → 16:9への変換で0.77%の歪み
- 座標変換が4回以上発生
- 各ステップで異なる基準サイズを使用
- 丸め誤差が累積
- フォントサイズ計算も不正確に

#### 問題③：PowerPointサイズの認識不足

PowerPoint 16:9スライドの実サイズ（REPORT01.mdより）:
- **物理サイズ**: 25.4 cm × 14.288 cm (10 inch × 5.625 inch)
- **EMU単位**: 9,144,000 EMU × 5,143,500 EMU
- **96 DPI換算**: **1280 px × 720 px**
- **縦横比**: 1.7778

一方、実際のサンプルPDF:
- **ページサイズ**: 3823 × 2134 ピクセル
- **縦横比**: 1.7915
- **16:9との差異**: +0.77%

**現在の実装では960×540を基準としているが、これは誤り。さらに元のPDFサイズ（3823×2134）も考慮されていない。**

---

## 2. 修正方針

### 2.1 設計思想：PDFの元の縦横比を維持する1:1マッピング

**ユーザー方針決定を反映**:

> PDFの元の縦横比（3823:2134）を維持し、完全な忠実度を実現する。

**新しいフロー**:
```
PDF (3823×2134) → 1280×715 画像 (3823:2134の比率を保つ) ← 縦横比維持！
  ↓
LLMに「1280×715の画像」と指示
  ↓
LLMがパーセンテージ座標を返す
  ↓
1280×715ピクセル座標に変換（1:1マッピング）
  ↓
PowerPointに配置（カスタムスライドサイズ: 1280×715、EMU単位に変換）
```

**メリット**:
- **完全な忠実度**: 元のPDFの縦横比を100%維持
- **歪みゼロ**: 縦横比の変換による歪みが一切発生しない
- 座標変換が最小限（パーセンテージ→ピクセル→EMUのみ）
- 世代間での誤差累積がない
- フォントサイズ計算が正確
- コードがシンプルで保守しやすい

### 2.2 PowerPointカスタムサイズの採用

**PowerPoint カスタムサイズ（3823:2134の比率を保つ）**:
- **実装サイズ（推奨）**: 1280 px × 715 px
  - 理由: メモリ効率、LLM処理速度、PowerPoint互換性
  - 縦横比: 1280 / 715 ≈ 1.7902（3823 / 2134 ≈ 1.7915とほぼ一致）
  - 誤差: 0.07%（無視できる範囲）
- **代替案**: 3823 px × 2134 px（元のサイズをそのまま使用、より高解像度）
  - 利点: 完全に一致
  - 欠点: メモリ使用量大、LLM処理遅延、PowerPointファイルサイズ増加

**推奨**: **1280×715 px**を採用（実用性と忠実度のバランス）

**すべてのモジュールでこの値に統一します。**

### 2.3 LLMプロンプトの改善

現在:
```python
SLIDE DIMENSIONS: {width}px × {height}px
```

改善後:
```python
SLIDE DIMENSIONS: 1280px × 715px

CRITICAL: This slide image is EXACTLY 1280×715 pixels, which corresponds to the original PDF aspect ratio (3823:2134).
- When you specify coordinates as percentages (0-100), they will be directly mapped to this pixel size.
- Example: x=50% → 640px, y=50% → 357.5px
- All measurements should be based on this exact pixel dimension.
- This custom aspect ratio is preserved to avoid distortion from the original PDF.
```

LLMに**実際の画像サイズと縦横比の意図を正確に伝える**ことで、座標の精度を向上。

### 2.4 座標変換ロジックの簡素化

**削除する変換**:
- 960×540基準の座標正規化（ImageAnalyzer）
- 画像ピクセル座標への再変換（ConversionWorkflow）
- 1280×720への縦横比変換（ImageLoader）

**残す変換（必要最小限）**:
1. パーセンテージ（0-100）→ 1280×715ピクセル座標（ImageAnalyzer）
2. ピクセル座標 → EMU単位（TextRenderer / ImageRenderer）

---

## 3. 技術仕様（96 DPI基準）

### 3.0 PowerPoint 96 DPI基準の理解

**CRITICAL**: PowerPointは内部的に**96 DPI（ppi）基準**でレイアウトされています（REPORT01.mdより）。

**単位換算の基礎**:
```
1 inch = 96 px @ 96 DPI
1 inch = 914,400 EMU (PowerPoint内部単位)
1 px = 914,400 / 96 = 9,525 EMU
1 cm ≈ 37.795 px @ 96 DPI
```

**PDF points → PowerPoint pixels**:
```
1 pt = 1/72 inch (PDF定義)
1 inch = 96 px @ 96 DPI (PowerPoint基準)
∴ 1 pt = 96/72 px = 1.333... px
```

**サンプルPDFの変換**:
```
1376 pts → 1376 × (96/72) = 1834.67 px → 1835 px
768 pts → 768 × (96/72) = 1024.00 px → 1024 px
```

### 3.1 PowerPointカスタムスライドサイズの設定（1835×1024 px）

**既存実装**（`src/slidemaker/pptx/generator.py`）:

```python
def _set_slide_size(self, size: SlideSize) -> None:
    """
    スライドサイズを設定します（private）.

    カスタムサイズの場合はconfigのwidth/heightを使用（96 DPI想定で変換）
    """
    if size not in size_mapping:
        # カスタムサイズの場合
        logger.warning(
            "Custom or unsupported slide size, using config dimensions",
            size=size.value,
            width=self.config.width,
            height=self.config.height,
        )
        # ピクセルからインチへの変換（96 DPI想定）
        width_inches = self.config.width / 96.0
        height_inches = self.config.height / 96.0
        self.presentation.slide_width = Inches(width_inches)
        self.presentation.slide_height = Inches(height_inches)
        return
```

**新しいカスタムサイズ設定（1835×1024 px、96 DPI基準）**:

```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
# PDFの実サイズ（1376×768 pts）を96 DPI基準で変換
# 1835 px / 96 = 19.1146 inches
# 1024 px / 96 = 10.6667 inches
prs.slide_width = Inches(19.1146)
prs.slide_height = Inches(10.6667)
```

**EMU単位での設定（正確）**:

```python
from pptx.util import Inches

# 1 inch = 914,400 EMU
# 1 px @ 96 DPI = 9,525 EMU
# 1835 px = 1835 × 9,525 = 17,478,375 EMU
# 1024 px = 1024 × 9,525 = 9,753,600 EMU
prs.slide_width = 17478375  # EMU
prs.slide_height = 9753600   # EMU
```

**または、python-pptxのInches関数を使用（推奨）**:

```python
from pptx.util import Inches

# 96 DPI基準でピクセルからインチへ変換
width_px = 1835
height_px = 1024
width_inches = width_px / 96.0  # 19.11458...
height_inches = height_px / 96.0  # 10.66666...

prs.slide_width = Inches(width_inches)
prs.slide_height = Inches(height_inches)
# 内部的にEMU単位（17,478,375 × 9,753,600）に変換される
```

### 3.2 PDF→画像変換のDPI設定（96 DPI基準）

**ImageLoader（loader.py）の修正**:

```python
# 修正前
DEFAULT_DPI = 150
TARGET_WIDTH = 1280  # AI分析用の画像幅（1280x720で十分）
TARGET_HEIGHT = 720  # AI分析用の画像高さ

# 修正後
# カスタムスライドサイズ（PDFの実サイズ1376×768 ptsを96 DPI基準で変換）
# PowerPoint 96 DPI基準: 1376 pts × (96/72) = 1835 px, 768 pts × (96/72) = 1024 px
DEFAULT_DPI = 150  # PDF→画像変換のDPI（品質維持）
CUSTOM_WIDTH_PX = 1835  # PDFの実サイズ（96 DPI基準）
CUSTOM_HEIGHT_PX = 1024  # PDFの実サイズ（96 DPI基準）
TARGET_WIDTH = CUSTOM_WIDTH_PX
TARGET_HEIGHT = CUSTOM_HEIGHT_PX

# 元のPDF比率（PDF points基準）
# 1376 / 768 = 1.791667
ORIGINAL_PDF_ASPECT_RATIO = 1376 / 768  # ≈ 1.791667

# 実装サイズの比率検証（96 DPI基準）
# 1835 / 1024 = 1.791016
IMPLEMENTED_ASPECT_RATIO = CUSTOM_WIDTH_PX / CUSTOM_HEIGHT_PX  # ≈ 1.791016
# 誤差: 0.036%（無視できる範囲）

# EMU変換定数（PowerPoint内部単位）
# 1 inch = 914,400 EMU, 1 inch = 96 px @ 96 DPI
# 1 px = 914,400 / 96 = 9,525 EMU（python-pptxの実装）
EMU_PER_PIXEL = 9525

# サイズのEMU値（参考）
# 1835 px × 9525 = 17,478,375 EMU
# 1024 px × 9525 = 9,753,600 EMU
SLIDE_WIDTH_EMU = CUSTOM_WIDTH_PX * EMU_PER_PIXEL  # 17,478,375
SLIDE_HEIGHT_EMU = CUSTOM_HEIGHT_PX * EMU_PER_PIXEL  # 9,753,600
```

### 3.3 座標変換式（修正後、96 DPI基準）

#### ステップ1: LLM出力（パーセンテージ）→ ピクセル座標（96 DPI基準）

```python
# ImageAnalyzer._normalize_position / _normalize_size
# 96 DPI基準のカスタムスライドサイズ
slide_width, slide_height = 1835, 1024

x_px = int(percentage_x * slide_width / 100)
y_px = int(percentage_y * slide_height / 100)
width_px = int(percentage_width * slide_width / 100)
height_px = int(percentage_height * slide_height / 100)
```

**例**:
- x=50% → 917.5 px → 917 px（整数化）
- y=10% → 102.4 px → 102 px（整数化）
- width=80% → 1468 px
- height=60% → 614.4 px → 614 px（整数化）

#### ステップ2: ピクセル座標 → EMU単位（PowerPoint内部単位）

```python
# TextRenderer / ImageRenderer
EMU_PER_PIXEL = 9525  # python-pptxの変換レート（96 DPI基準）

left_emu = x_px * EMU_PER_PIXEL
top_emu = y_px * EMU_PER_PIXEL
width_emu = width_px * EMU_PER_PIXEL
height_emu = height_px * EMU_PER_PIXEL
```

**例**:
- x=917px → 8,734,425 EMU
- width=1468px → 13,982,700 EMU

**検証**:
```python
# スライド全体のEMU値
slide_width_emu = 1835 * 9525 = 17,478,375 EMU
slide_height_emu = 1024 * 9525 = 9,753,600 EMU

# 要素が境界内に収まるか確認
assert left_emu + width_emu <= slide_width_emu
assert top_emu + height_emu <= slide_height_emu
```

#### ステップ3: 画像切り出し（1:1マッピング、96 DPI基準）

```python
# ConversionWorkflow._process_images
# 画像サイズ = カスタムスライドサイズ（96 DPI基準）なので、座標変換不要
img_width, img_height = image.size  # 1835×1024
slide_width, slide_height = 1835, 1024

# 1:1マッピング（スケール変換なし）
x_crop = element.position.x  # ピクセル単位
y_crop = element.position.y
width_crop = element.size.width
height_crop = element.size.height

# paddingの追加
padding_ratio = 0.20
padding_x = int(width_crop * padding_ratio)
padding_y = int(height_crop * padding_ratio)

x_crop = max(0, x_crop - padding_x)
y_crop = max(0, y_crop - padding_y)
width_crop = min(img_width - x_crop, width_crop + 2 * padding_x)
height_crop = min(img_height - y_crop, height_crop + 2 * padding_y)

bbox = (x_crop, y_crop, x_crop + width_crop, y_crop + height_crop)
cropped_image = image.crop(bbox)
```

**重要な注意点**:
- 画像サイズ（1835×1024）とカスタムスライドサイズ（1835×1024）が一致
- 座標変換やスケール補正が不要
- PowerPoint 96 DPI基準と完全一致するため、レンダリング歪みなし

### 3.4 フォントサイズ計算（修正後、96 DPI基準）

**LLMが推定したフォントサイズ（pt）を信頼する方針**。

現在の問題:
- LLMは1920×1080基準でフォントサイズを推定
- 実際は異なるサイズなので、フォントサイズ推定が不正確

修正後:
- LLMに1835×1024（96 DPI基準の正確なサイズ）を伝えることで、正確なフォントサイズ推定が可能

**検証式（96 DPI基準、1024px高さ）**:
```python
# 1024px高さのスライドで、テキストが5%を占める場合
text_height_px = 1024 * 0.05 = 51.2 px

# フォント高さ（px）からポイント（pt）への変換（96 DPI基準）
# 1 pt = 1/72 inch, 1 inch = 96 px @ 96 DPI
# よって 1 pt = 96/72 px = 1.333... px
font_size_pt = text_height_px / (96/72) = 51.2 / 1.333 ≈ 38.4 pt ≈ 38 pt
```

**プロンプトに追加する式（96 DPI基準、1024px高さ）**:
```
- 5% of 1024px = 51.2px height ≈ 38pt font
- 3% of 1024px = 30.72px height ≈ 23pt font
- 2% of 1024px = 20.48px height ≈ 15pt font
- 1% of 1024px = 10.24px height ≈ 8pt font
```

**重要**: PowerPoint 96 DPI基準では、1 pt = 96/72 px = 1.333... px という関係が成り立ちます。

---

## 4. 修正計画（実装ステップ）

### Step 1: 定数の統一（最優先、96 DPI基準）

**ファイル**: `src/slidemaker/image_processing/loader.py`

**修正内容**:
```python
# 修正前
DEFAULT_DPI = 150
TARGET_WIDTH = 1280  # AI分析用の画像幅（1280x720で十分）
TARGET_HEIGHT = 720  # AI分析用の画像高さ

# 修正後
# カスタムスライドサイズ（PowerPoint 96 DPI基準）
# サンプルPDF: samples/MDX_Strategic_Engine_2026.pdf
# - ページサイズ（PDF定義）: 1376 × 768 pts
# - 縦横比: 1.791667
# - 96 DPI換算: 1376 pts × (96/72) = 1835 px, 768 pts × (96/72) = 1024 px
DEFAULT_DPI = 150  # PDF→画像変換のDPI（品質維持）
CUSTOM_WIDTH_PX = 1835  # PDFの実サイズ（96 DPI基準）
CUSTOM_HEIGHT_PX = 1024  # PDFの実サイズ（96 DPI基準）
TARGET_WIDTH = CUSTOM_WIDTH_PX
TARGET_HEIGHT = CUSTOM_HEIGHT_PX

# 元のPDF比率（PDF points基準）
# 1376 / 768 = 1.791667
ORIGINAL_PDF_ASPECT_RATIO = 1376 / 768

# 実装サイズの比率検証（96 DPI基準）
# 1835 / 1024 = 1.791016
IMPLEMENTED_ASPECT_RATIO = CUSTOM_WIDTH_PX / CUSTOM_HEIGHT_PX
# 誤差: 0.036%（無視できる範囲）

# PowerPoint内部単位との関係（96 DPI基準）
# 1 inch = 96 px @ 96 DPI
# 1 inch = 914,400 EMU (PowerPoint内部単位)
# 1 px = 914,400 / 96 = 9,525 EMU（python-pptxの実装）
EMU_PER_PIXEL = 9525

# サイズのEMU値（参考）
# 1835 px × 9525 = 17,478,375 EMU
# 1024 px × 9525 = 9,753,600 EMU
SLIDE_WIDTH_EMU = CUSTOM_WIDTH_PX * EMU_PER_PIXEL
SLIDE_HEIGHT_EMU = CUSTOM_HEIGHT_PX * EMU_PER_PIXEL

# PDFサイズのインチ表記（参考）
# 1835 px / 96 = 19.1146 inches
# 1024 px / 96 = 10.6667 inches
SLIDE_WIDTH_INCHES = CUSTOM_WIDTH_PX / 96.0
SLIDE_HEIGHT_INCHES = CUSTOM_HEIGHT_PX / 96.0
```

**理由**:
1. PowerPoint 96 DPI基準に完全一致させる
2. PDFの実サイズ（1376×768 pts）を正確に変換
3. 座標変換を最小限にする（パーセンテージ→ピクセル→EMUのみ）
4. すべてのモジュールで参照する定数を統一

---

### Step 2: ImageAnalyzerの修正（96 DPI基準）

**ファイル**: `src/slidemaker/image_processing/analyzer.py`

**修正箇所①**: `__init__()`のデフォルト引数

```python
# 修正前
def __init__(
    self,
    llm_manager: LLMManager,
    max_retries: int = 3,
    slide_dimensions: tuple[int, int] = (960, 540),  # 古い値（誤り）
) -> None:

# 修正後
def __init__(
    self,
    llm_manager: LLMManager,
    max_retries: int = 3,
    slide_dimensions: tuple[int, int] = (1835, 1024),  # 96 DPI基準（PDFの実サイズ）
) -> None:
```

**修正箇所②**: `analyze_slide_image()`のLLMプロンプト生成

```python
# 修正前
system, user = create_image_analysis_prompt(
    width=1920, height=1080  # デフォルト値（誤り）
)

# 修正後
system, user = create_image_analysis_prompt(
    width=self.slide_dimensions[0],  # 1835
    height=self.slide_dimensions[1]  # 1024
)
```

**理由**:
1. LLMに実際の画像サイズ（1835×1024、96 DPI基準）を正確に伝える
2. PowerPoint内部表現と完全一致させる
3. 座標変換の精度を最大化する

---

### Step 3: ConversionWorkflowの修正（96 DPI基準）

**ファイル**: `src/slidemaker/workflows/conversion.py`

**修正箇所①**: `_process_images()`のslide_width, slide_height

```python
# 修正前
img_width, img_height = image.size
slide_width, slide_height = 960, 540  # デフォルトスライドサイズ（誤り）

# 修正後
img_width, img_height = image.size
# カスタムスライドサイズ（1835×1024、96 DPI基準、PDFの実サイズ）
# 画像も同じサイズで変換されているため、1:1マッピング
slide_width, slide_height = 1835, 1024

# 画像サイズが1835×1024でない場合の警告ログ追加
if img_width != slide_width or img_height != slide_height:
    self.logger.warning(
        "Image size does not match custom slide size (96 DPI basis)",
        image_size=(img_width, img_height),
        expected_size=(slide_width, slide_height),
        expected_aspect_ratio=slide_width / slide_height,
        actual_aspect_ratio=img_width / img_height if img_height > 0 else 0,
    )
```

**修正箇所②**: padding比率の見直し

```python
# 修正前
padding_ratio = 0.15  # 15%の余白を追加（プロンプト改善により削減）

# 修正後
# 座標系が統一されたため、padding比率を再調整
# 過去の経験値: 15%→25%で改善（メモリー参照）
padding_ratio = 0.20  # 20%の余白（座標精度向上により削減）
```

**理由**:
- 画像サイズとカスタムスライドサイズが一致するため、座標変換が不要に
- padding比率は座標精度に応じて調整

**修正箇所③**: `__init__()`でImageAnalyzerに正しいslide_dimensionsを渡す

```python
# 修正前
self.image_analyzer = ImageAnalyzer(
    llm_manager=llm_manager,
    max_retries=max_retries,
    slide_dimensions=(960, 540),  # 古い値（誤り）
)

# 修正後
self.image_analyzer = ImageAnalyzer(
    llm_manager=llm_manager,
    max_retries=max_retries,
    slide_dimensions=(1835, 1024),  # 96 DPI基準（PDFの実サイズ）
)
```

**理由**:
1. ImageAnalyzerのデフォルト値を変更するだけでなく、明示的に渡すことで意図を明確化
2. PowerPoint 96 DPI基準に完全一致
3. PDFの実サイズ（1376×768 pts）を正確に反映

---

### Step 4: LLMプロンプトの改善（96 DPI基準）

**ファイル**: `src/slidemaker/llm/prompts/image_processing.py`

**修正箇所①**: `IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE`

```python
# 修正前
IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze the presentation slide image below and extract all elements following the instructions in the system prompt.

SLIDE DIMENSIONS: {width}px × {height}px

Remember:
- Use percentages (0-100) for all positions and sizes
- Output ONLY valid JSON with no additional text
- Follow the JSON formatting rules exactly
- Include all text and image elements you can identify

Now analyze this slide and output the JSON:"""

# 修正後
IMAGE_ANALYSIS_USER_PROMPT_TEMPLATE = """Analyze the presentation slide image below and extract all elements following the instructions in the system prompt.

SLIDE DIMENSIONS: {width}px × {height}px (PowerPoint 96 DPI Basis)

CRITICAL COORDINATE SYSTEM INFORMATION (PowerPoint 96 DPI Standard):
- This slide image is EXACTLY {width}×{height} pixels, based on PowerPoint's internal 96 DPI standard.
- The original PDF size (1376×768 pts) is converted to {width}×{height} px @ 96 DPI (1 pt = 96/72 px).
- This ensures perfect alignment with PowerPoint's internal coordinate system and avoids any distortion.
- When you specify coordinates as percentages (0-100), they will be directly mapped to this pixel size.
- Example for 1835×1024: x=50% → 917.5px, y=50% → 512px
- All measurements should be based on this exact pixel dimension.

FONT SIZE ESTIMATION (PowerPoint 96 DPI Standard):
- At 96 DPI, 1 pt = 96/72 px = 1.333... px
- Font sizes should be estimated based on the actual pixel height (1024px):
  - 5% of 1024px = 51.2px height ≈ 38pt font
  - 3% of 1024px = 30.72px height ≈ 23pt font
  - 2% of 1024px = 20.48px height ≈ 15pt font
  - 1% of 1024px = 10.24px height ≈ 8pt font

Remember:
- Use percentages (0-100) for all positions and sizes
- Output ONLY valid JSON with no additional text
- Follow the JSON formatting rules exactly
- Include all text and image elements you can identify

Now analyze this slide and output the JSON:"""
```

**理由**:
1. LLMに96 DPI基準とPowerPoint内部表現を明示
2. PDF points → PowerPoint pixels の変換関係を説明
3. フォントサイズ推定式を96 DPI基準（1024px高さ）に更新
4. 座標精度とレンダリング品質の向上

---

### Step 5: SlideConfig/PowerPointGeneratorの対応

**ファイル**: `src/slidemaker/core/models/slide_config.py`

**確認事項**:
- `SlideConfig`が`width=1280, height=715`のカスタムサイズをサポートしているか確認
- 必要に応じて`create_custom()`メソッドを追加

**想定コード**:
```python
@classmethod
def create_custom(cls, width: int, height: int) -> SlideConfig:
    """
    カスタムサイズのスライド設定を作成します.

    Args:
        width: スライド幅（ピクセル）
        height: スライド高さ（ピクセル）

    Returns:
        SlideConfig: カスタムサイズのスライド設定
    """
    return cls(
        size=SlideSize.CUSTOM,  # 新しいEnum値が必要
        width=width,
        height=height,
    )
```

**ファイル**: `src/slidemaker/pptx/generator.py`

**確認事項**:
- `_set_slide_size()`がカスタムサイズを正しく処理しているか確認（既に実装済み）
- `SlideSize.CUSTOM`などのEnum値が必要な場合は追加

---

## 5. テスト方法

### 5.1 単体テスト

**目的**: 各モジュールの座標変換が正しいことを検証

#### テスト1: ImageAnalyzerの座標正規化（1280×715）

```python
def test_normalize_position_1280x715():
    analyzer = ImageAnalyzer(llm_manager, slide_dimensions=(1280, 715))

    # x=50%, y=10% → 640px, 71.5px → 71px（整数化）
    position = analyzer._normalize_position(
        {"x": 50, "y": 10},
        original_image_size=(1280, 715),
        slide_dimensions=(1280, 715)
    )

    assert position.x == 640
    assert position.y == 71

def test_normalize_size_1280x715():
    analyzer = ImageAnalyzer(llm_manager, slide_dimensions=(1280, 715))

    # width=80%, height=60% → 1024px, 429px
    size = analyzer._normalize_size(
        {"width": 80, "height": 60},
        original_image_size=(1280, 715),
        slide_dimensions=(1280, 715)
    )

    assert size.width == 1024
    assert size.height == 429
```

#### テスト2: ConversionWorkflowの画像切り出し

```python
def test_image_cropping_1to1_mapping_custom_size():
    # 1280×715の画像を作成
    image = Image.new("RGB", (1280, 715), color="white")

    # 要素定義（ピクセル座標）
    element = ImageElement(
        source="",
        position=Position(x=640, y=357),  # 中央
        size=Size(width=320, height=179)  # 25%×25%
    )

    # 切り出し（1:1マッピング）
    x_crop = element.position.x
    y_crop = element.position.y
    width_crop = element.size.width
    height_crop = element.size.height

    bbox = (x_crop, y_crop, x_crop + width_crop, y_crop + height_crop)
    cropped = image.crop(bbox)

    assert cropped.size == (320, 179)
```

#### テスト3: 縦横比の検証

```python
def test_aspect_ratio_preservation():
    # 元のPDF比率
    original_aspect_ratio = 3823 / 2134  # ≈ 1.7915

    # 実装サイズの比率
    implemented_aspect_ratio = 1280 / 715  # ≈ 1.7902

    # 誤差が0.1%以内であることを確認
    error = abs(original_aspect_ratio - implemented_aspect_ratio) / original_aspect_ratio
    assert error < 0.001, f"Aspect ratio error {error:.4%} exceeds 0.1%"
```

### 5.2 統合テスト

**目的**: PDF→PowerPoint変換の全体フローを検証

```bash
# テスト用PDFを変換（サンプルPDF使用）
uv run slidemaker convert samples/MDX_Strategic_Engine_2026.pdf -o output/test_output.pptx -v

# 座標が正しいか確認（PowerPoint MCP使用）
mcp__powerpoint__open_presentation(file_path="output/test_output.pptx")
mcp__powerpoint__get_presentation_info()
mcp__powerpoint__get_slide_info(slide_index=0)

# 期待値：
# - slide_width = 12,192,000 EMU (1280px × 9525 EMU/px)
# - slide_height = 6,809,472 EMU (715px × 9525 EMU/px)
# - 縦横比 = 1.7902（誤差0.07%）
# - left < 12,192,000 EMU (スライド幅以内)
# - top < 6,809,472 EMU (スライド高さ以内)
# - テキスト要素のフォントサイズが妥当（10-44pt範囲）
```

### 5.3 世代間検証（再帰的変換）

**目的**: 世代を進めても縮尺・縦横比が維持されることを検証

```bash
# 1世代目: PDF → PPTX1
uv run slidemaker convert samples/MDX_Strategic_Engine_2026.pdf -o output/gen1.pptx

# PPTX1 → PDF1（PowerPointでエクスポート）
libreoffice --headless --convert-to pdf --outdir output output/gen1.pptx

# 2世代目: PDF1 → PPTX2
uv run slidemaker convert output/gen1.pdf -o output/gen2.pptx

# PPTX2 → PDF2
libreoffice --headless --convert-to pdf --outdir output output/gen2.pptx

# 3世代目: PDF2 → PPTX3
uv run slidemaker convert output/gen2.pdf -o output/gen3.pptx

# 座標、フォントサイズ、縦横比を比較
# 期待値: gen1, gen2, gen3で座標・サイズ・縦横比が一定（誤差5%以内）
```

### 5.4 縦横比検証

```python
# 各世代のPDFから縦横比を抽出して比較
from pdf2image import convert_from_path

for gen in ['samples/MDX_Strategic_Engine_2026.pdf', 'output/gen1.pdf', 'output/gen2.pdf']:
    images = convert_from_path(gen, dpi=150, size=(1280, 715))
    for i, img in enumerate(images[:1], 1):  # 最初のページのみ
        width, height = img.size
        aspect_ratio = width / height
        print(f"{gen} - Slide {i}: {width}×{height}, AR={aspect_ratio:.4f}")

# 期待値: すべての世代でAR≈1.7902（誤差0.1%以内）
```

### 5.5 視覚的検証

```bash
# PowerPointをPDFに変換
libreoffice --headless --convert-to pdf --outdir output/captures output/gen1.pptx

# PDFを画像に変換
python -c "
from pdf2image import convert_from_path
images = convert_from_path('output/captures/gen1.pdf', dpi=150)
for i, img in enumerate(images, 1):
    img.save(f'output/captures/gen1_slide_{i:03d}.png', 'PNG')
"

# 元PDFの画像と比較（目視）
# - テキストが切れていないか
# - 画像要素が完全に表示されているか
# - フォントサイズが妥当か
# - **縦横比が維持されているか（歪みがないか）**
```

---

## 6. 優先順位

| 優先度 | ステップ | 理由 |
|---|---|---|
| **1（最優先）** | Step 1: 定数の統一 | すべてのモジュールの基礎となる |
| **2（高）** | Step 2: ImageAnalyzerの修正 | LLMへの指示が最も重要 |
| **3（高）** | Step 3: ConversionWorkflowの修正 | 画像切り出しの精度に直結 |
| **4（中）** | Step 4: LLMプロンプトの改善 | LLMの理解を助ける補助的改善 |
| **5（中）** | Step 5: SlideConfig/PowerPointGenerator対応 | カスタムサイズのサポート確認 |
| **6（低）** | テストの追加 | 修正後の検証 |

**推奨作業順序**:
1. Step 1 → Step 2 → Step 3を一度に実施（密接に関連）
2. 単体テスト（縦横比検証含む）で検証
3. Step 4 → Step 5を実施
4. 統合テスト・世代間検証で最終確認

---

## 7. リスク評価と対策

### リスク1: 既存のPDFで座標がずれる

**リスク**: 過去にキャリブレーションされたPDFが新しい座標系でずれる可能性

**対策**:
- 修正前後でサンプルPDFを変換し、座標を比較
- 既存のメモリー（pdf-pptx-conversion-technical-learnings.md）に記載されたpadding比率を再調整

### リスク2: フォントサイズが小さくなる

**リスク**: LLMが1920×1080基準で推定していた場合、1280×715に変更するとフォントサイズが小さくなる

**対策**:
- プロンプトにフォントサイズ推定式を明記（715px基準）
- 統合テストでフォントサイズを検証
- 必要に応じてフォントサイズにスケール係数を適用

### リスク3: 画像切り出しの精度低下

**リスク**: padding比率の変更により、画像要素が欠ける可能性

**対策**:
- padding比率を0.20から開始し、視覚的検証で調整
- 過去の経験値（15%→25%で改善）を参考に、0.20-0.25の範囲で最適化

### リスク4: カスタムサイズの互換性問題

**リスク**: 1280×715のカスタムサイズがPowerPoint/LibreOfficeで正しく表示されない可能性

**対策**:
- PowerPointおよびLibreOfficeでのレンダリング検証
- 必要に応じて代替案（3823×2134の元サイズ）に切り替え
- 縦横比が正しく維持されているかを視覚的に確認

---

## 8. 成功基準

修正が成功したと判断する基準:

1. **縦横比の一貫性**: すべてのモジュールで3823:2134の比率（1280×715として実装）を維持
2. **座標系の一貫性**: すべてのモジュールで1280×715を基準とする
3. **世代間の安定性**: 3世代変換しても座標・サイズ・縦横比の誤差が5%以内
4. **歪みゼロ**: 元のPDFの縦横比が完全に維持されている（目視確認）
5. **フォントサイズの妥当性**: テキスト要素のフォントサイズが10-44pt範囲内
6. **画像要素の完全性**: 画像要素が切れずに完全に表示される
7. **テストカバレッジ**: 単体テスト・統合テストでカバレッジ90%以上

---

## 9. 実装後のメンテナンス

### 9.1 ドキュメント更新

- `docs/phase4_summary.md`: 座標系の変更とカスタム縦横比の採用を記載
- `.serena/memories/pdf-pptx-conversion-technical-learnings.md`: 修正内容を追記
- `CLAUDE.md`: 技術スタックに座標系の仕様とカスタムサイズを追加

### 9.2 モニタリング

- ConversionWorkflowに座標範囲の警告ログを追加
- 画像サイズが1280×715でない場合の警告
- 縦横比が1.7902から大きくずれる場合の警告（±1%）
- フォントサイズが異常値（<8pt, >60pt）の場合の警告

### 9.3 今後の拡張

**他のPDF縦横比への対応**:
- PDFページサイズを動的に検出
- 各PDFの元の縦横比を自動的に維持
- `slide_dimensions`を動的に計算して切り替え可能にする

**カスタムスライドサイズ対応の強化**:
- ユーザーがスライドサイズを指定できるオプション追加
- `target_size`パラメータをCLI引数として公開
- 縦横比の自動検出と最適サイズ提案機能

---

## 10. まとめ（96 DPI基準対応版）

### 問題の本質（更新）

PDF→PowerPoint変換において、**PowerPointの96 DPI内部基準を理解せずに、複数のモジュール間で異なる座標系を使用していたこと**が根本原因。

**これまでの誤解**:
1. PDFサイズ = 3823×2134 px（実際はpdf2imageの150 DPI変換後のサイズ）
2. PowerPoint標準16:9（1280×720）に統一しようとした
3. LLMには1920×1080と伝え、座標正規化では960×540を使用
4. 座標変換が複数回発生し、丸め誤差が累積

**実際の真実**:
1. PDFサイズ = **1376×768 pts**（PDF定義）
2. PowerPoint 96 DPI基準では **1835×1024 px**（1 pt = 96/72 px）
3. PowerPoint内部表現（96 DPI、EMU単位）と完全一致させるべき
4. 座標変換は **パーセンテージ→ピクセル→EMUのみ**で十分

### 解決策（96 DPI基準）

**PowerPoint 96 DPI基準に基づく正確なサイズ（1835×1024 px）に完全統一**し、座標変換を最小限に削減。

**実装方針**:
- すべてのモジュールで **1835×1024 px**（96 DPI基準）を使用
- LLMにも1835×1024と**96 DPI基準の意図**を明示
- 1:1マッピングで画像を切り出す（座標変換不要）
- **PowerPoint内部表現と完全一致**
- EMU変換のみpython-pptxに任せる（1 px = 9,525 EMU）

### 期待効果（96 DPI基準）

- **PowerPoint内部表現と完全一致**: レンダリング歪みゼロ
- **座標精度の最大化**: パーセンテージ→ピクセル→EMUの単純変換
- **縦横比の完全維持**: PDF実サイズ（1.791667）との誤差0.036%
- 世代間での縮尺維持
- フォントサイズの正確な推定（96 DPI基準）
- 画像要素の完全な表示
- コードの簡素化と保守性向上

### 重要な学び

**PowerPointの96 DPI基準**（REPORT01.mdより）:
```
1 inch = 96 px @ 96 DPI (PowerPoint内部基準)
1 inch = 914,400 EMU (PowerPoint内部単位)
1 px = 9,525 EMU (python-pptxの実装)
1 pt = 96/72 px = 1.333... px (PDF points → PowerPoint pixels)
```

この基礎を理解せずに、推測でサイズを決定していたことが問題の根源でした。

---

**次のアクション**: この計画に基づいて、Step 1から順次実装を進めてください。各ステップの完了後、テストで検証することを推奨します。特に**PowerPoint 96 DPI基準との一致**と**座標精度**を重点的に確認してください。
