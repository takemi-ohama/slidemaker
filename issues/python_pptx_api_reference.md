# python-pptx APIリファレンス

## 概要

python-pptxは、PowerPoint（.pptx）ファイルの作成、読み取り、更新を実現するPythonライブラリです。PowerPointアプリケーションのインストールが不要で、プログラム的にプレゼンテーションを生成・編集できます。

**公式ドキュメント**: https://python-pptx.readthedocs.io/

---

## 1. Presentationオブジェクトの作成

### 概要

`Presentation`クラスはPresentationML形式のプレゼンテーションを表します。`pptx.Presentation()`関数経由でアクセスします。

### 主要APIメソッド

#### `pptx.Presentation(pptx=None) → Presentation`

`.pptx`ファイルをロードするか、新規プレゼンテーションを作成します。

**パラメータ:**
- `pptx` (str | IO[bytes] | None): ファイルパス、ファイルライクオブジェクト、またはNone
  - `None`の場合、デフォルトテンプレート（4:3アスペクト比）が読み込まれる

**戻り値:**
- `Presentation`: プレゼンテーションオブジェクト

### コード例

```python
from pptx import Presentation

# 新規Presentation作成（デフォルトテンプレート使用）
prs = Presentation()

# 既存ファイルの読み込み
prs = Presentation('existing_presentation.pptx')

# ファイルライクオブジェクトから読み込み
from io import BytesIO
with open('presentation.pptx', 'rb') as f:
    prs = Presentation(BytesIO(f.read()))

# 保存
prs.save('output.pptx')

# ファイルライクオブジェクトに保存
from io import BytesIO
output = BytesIO()
prs.save(output)
```

### 主要プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `slides` | Slides | プレゼンテーション内のスライドコレクション |
| `slide_layouts` | SlideLayouts | 最初のスライドマスターに属するレイアウトコレクション |
| `slide_master` | SlideMaster | プレゼンテーションの第一スライドマスター |
| `slide_masters` | SlideMasters | プレゼンテーション内の全スライドマスター |
| `slide_width` | int | スライド幅（EMU単位）、読み書き可能 |
| `slide_height` | int | スライド高さ（EMU単位）、読み書き可能 |
| `core_properties` | CoreProperties | ダブリンコア文書プロパティ（タイトル、著者等） |
| `notes_master` | NotesMaster | プレゼンテーション用ノートマスター |

---

## 2. スライドサイズ設定

### 概要

スライドサイズは`Presentation`オブジェクトの`slide_width`と`slide_height`プロパティで設定します。単位はEMU（English Metric Units）です。

### APIメソッド

#### `Presentation.slide_width` プロパティ

スライドの幅を取得・設定します（EMU単位）。

**型**: `int`

#### `Presentation.slide_height` プロパティ

スライドの高さを取得・設定します（EMU単位）。

**型**: `int`

### 標準サイズ一覧

| アスペクト比 | 幅 (インチ) | 高さ (インチ) | 幅 (EMU) | 高さ (EMU) |
|------------|------------|-------------|---------|-----------|
| 4:3        | 10         | 7.5         | 9144000 | 6858000   |
| 16:9       | 10         | 5.625       | 9144000 | 5143500   |
| 16:10      | 10         | 6.25        | 9144000 | 5715000   |

**EMU換算式**: 1インチ = 914400 EMU

### コード例

```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()

# 4:3サイズの設定
prs.slide_width = Inches(10)
prs.slide_height = Inches(7.5)

# 16:9サイズの設定
prs.slide_width = Inches(10)
prs.slide_height = Inches(5.625)

# 16:10サイズの設定
prs.slide_width = Inches(10)
prs.slide_height = Inches(6.25)

# カスタムサイズの設定（例: A4サイズ）
prs.slide_width = Inches(11.69)   # 297mm
prs.slide_height = Inches(8.27)   # 210mm

# EMU単位で直接設定
prs.slide_width = 9144000    # 10インチ
prs.slide_height = 5143500   # 16:9の高さ

# 現在のサイズを取得
width_emu = prs.slide_width
height_emu = prs.slide_height
width_inches = Inches(width_emu / 914400)

prs.save('custom_size.pptx')
```

### 注意点

- スライドサイズは作成時に設定するのがベストプラクティス
- サイズ変更後に追加したスライドに新しいサイズが適用される
- 既存のスライドのサイズは自動調整されない場合がある

---

## 3. スライド操作

### 概要

スライドの追加はSlidesコレクションの`add_slide()`メソッドを使用します。スライドレイアウトを指定して追加し、個別のスライドオブジェクトとして操作します。

### 主要APIメソッド

#### `Slides.add_slide(slide_layout) → Slide`

新しいスライドを追加します。

**パラメータ:**
- `slide_layout` (pptx.slide.SlideLayout): 適用するスライドレイアウト

**戻り値:**
- `Slide`: 新しく追加されたスライドオブジェクト

#### `Slides.get(slide_id, default=None) → Slide | None`

スライドIDから特定のスライドを検索します。

**パラメータ:**
- `slide_id` (int): スライドID
- `default` (Slide | None): 見つからない場合のデフォルト値

**戻り値:**
- `Slide | None`: スライドオブジェクトまたはNone

#### `Slides.index(slide) → int`

スライドのゼロベースのインデックス位置を返します。

**パラメータ:**
- `slide` (pptx.slide.Slide): 対象スライド

**戻り値:**
- `int`: スライドのインデックス

### スライドレイアウト

PowerPointの標準テーマには約9種類のレイアウトがあります：

| インデックス | レイアウト名 | 説明 |
|------------|------------|------|
| 0 | Title Slide | タイトルスライド |
| 1 | Title and Content | タイトル＋コンテンツ（箇条書き） |
| 2 | Section Header | セクションヘッダー |
| 3 | Two Content | 2列コンテンツ |
| 4 | Comparison | 比較レイアウト |
| 5 | Title Only | タイトルのみ |
| 6 | Blank | 空白 |
| 7 | Content with Caption | コンテンツ＋キャプション |
| 8 | Picture with Caption | 画像＋キャプション |

### コード例

```python
from pptx import Presentation

prs = Presentation()

# 定数でレイアウトを指定
SLD_LAYOUT_TITLE_SLIDE = 0
SLD_LAYOUT_TITLE_AND_CONTENT = 1
SLD_LAYOUT_BLANK = 6

# タイトルスライドの追加
title_slide_layout = prs.slide_layouts[SLD_LAYOUT_TITLE_SLIDE]
title_slide = prs.slides.add_slide(title_slide_layout)

# コンテンツスライドの追加
content_slide_layout = prs.slide_layouts[SLD_LAYOUT_TITLE_AND_CONTENT]
content_slide = prs.slides.add_slide(content_slide_layout)

# 空白スライドの追加
blank_slide_layout = prs.slide_layouts[SLD_LAYOUT_BLANK]
blank_slide = prs.slides.add_slide(blank_slide_layout)

# スライド数を取得
slide_count = len(prs.slides)

# スライドをイテレート
for slide in prs.slides:
    print(f"Slide ID: {slide.slide_id}")

# インデックスでスライドを取得
first_slide = prs.slides[0]

# スライドのインデックスを取得
index = prs.slides.index(content_slide)
print(f"Content slide index: {index}")

prs.save('slides_example.pptx')
```

### スライドの削除

**注意**: 記事執筆時点（2025年）では、python-pptxはスライド削除機能を公式にサポートしていません。スライド削除やスライド位置変更の機能はバックログ状態です。

回避策として、XMLレベルでの操作が必要になる場合があります。

```python
# 非推奨: XMLレベルでの削除（公式サポート外）
# from lxml import etree
# rId = slide.part.package.relate_to(...)
# ...
```

---

## 4. テキストボックス

### 概要

テキストボックスはスライド上に任意の位置・サイズでテキストを配置できる要素です。`Shapes.add_textbox()`メソッドで追加し、`TextFrame`オブジェクトを介してテキストとフォーマットを設定します。

### 主要APIメソッド

#### `Shapes.add_textbox(left, top, width, height) → Shape`

テキストボックスを追加します。

**パラメータ:**
- `left` (Length): 左上隅のX座標（EMU単位）
- `top` (Length): 左上隅のY座標（EMU単位）
- `width` (Length): 幅（EMU単位）
- `height` (Length): 高さ（EMU単位）

**戻り値:**
- `Shape`: テキストボックスのShapeオブジェクト

### テキストフレーム設定

#### `TextFrame`クラスの主要プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `text` | str | フレーム内の全テキスト（読み書き可能） |
| `paragraphs` | list[Paragraph] | 段落のリスト |
| `word_wrap` | bool | テキスト折り返しの有効/無効 |
| `vertical_anchor` | MSO_ANCHOR | テキストの垂直配置 |
| `auto_size` | MSO_AUTO_SIZE | 自動サイズ調整モード |
| `margin_top` | Length | 上余白（EMU単位） |
| `margin_bottom` | Length | 下余白（EMU単位） |
| `margin_left` | Length | 左余白（EMU単位） |
| `margin_right` | Length | 右余白（EMU単位） |

#### `TextFrame`クラスの主要メソッド

- `add_paragraph()` - 新しい段落を追加
- `clear()` - 1つの空の段落を残して全削除
- `fit_text(...)` - テキストを図形内に収まるよう自動調整

### フォント設定

#### `Font`クラスの主要プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `name` | str | フォント名（例: "Arial"） |
| `size` | Length | フォントサイズ（EMU単位、Pt()で指定可能） |
| `bold` | bool | 太字設定 |
| `italic` | bool | 斜体設定 |
| `underline` | bool | 下線設定 |
| `color` | ColorFormat | 色設定 |

### テキスト配置

#### `Paragraph.alignment` プロパティ

`PP_PARAGRAPH_ALIGNMENT`（別名: `PP_ALIGN`）列挙型を使用します。

| 定数 | 説明 |
|-----|------|
| `PP_ALIGN.LEFT` | 左揃え |
| `PP_ALIGN.CENTER` | 中央揃え |
| `PP_ALIGN.RIGHT` | 右揃え |
| `PP_ALIGN.JUSTIFY` | 両端揃え |

### RGB色の指定方法

#### `RGBColor`クラス

RGB色を表す不変の値オブジェクトです。

**コンストラクタ:**
```python
RGBColor(r, g, b)
```

**パラメータ:**
- `r` (int): 赤成分（0-255）
- `g` (int): 緑成分（0-255）
- `b` (int): 青成分（0-255）

**クラスメソッド:**
```python
RGBColor.from_string(hex_string)
```

**パラメータ:**
- `hex_string` (str): 16進数文字列（例: "3C2F80"）

### コード例

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, MSO_AUTO_SIZE
from pptx.dml.color import RGBColor

prs = Presentation()
blank_slide_layout = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank_slide_layout)

# テキストボックスの追加
left = Inches(1)
top = Inches(2)
width = Inches(8)
height = Inches(1)
textbox = slide.shapes.add_textbox(left, top, width, height)

# テキストフレームの設定
text_frame = textbox.text_frame
text_frame.word_wrap = True
text_frame.vertical_anchor = MSO_ANCHOR.TOP
text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT

# 余白設定（EMU単位またはInches）
text_frame.margin_bottom = Inches(0.08)
text_frame.margin_left = 0  # EMU単位で0

# 最も簡単なテキスト設定
text_frame.text = "シンプルなテキスト"

# 詳細な制御（段落とランを使用）
text_frame.clear()  # 既存テキストをクリア
p = text_frame.paragraphs[0]
p.alignment = PP_ALIGN.CENTER  # 中央揃え

run = p.add_run()
run.text = "フォーマット付きテキスト"

# フォント設定
font = run.font
font.name = "Arial"
font.size = Pt(24)
font.bold = True
font.italic = False

# RGB色の指定（直接）
font.color.rgb = RGBColor(255, 0, 0)  # 赤色

# RGB色の指定（16進数から）
font.color.rgb = RGBColor.from_string("FF7F50")  # オレンジ色

# 複数段落の追加
p2 = text_frame.add_paragraph()
p2.text = "2番目の段落"
p2.alignment = PP_ALIGN.LEFT
p2.font.size = Pt(18)

# ハイパーリンクの追加
run_with_link = p2.add_run()
run_with_link.text = "クリックしてください"
run_with_link.hyperlink.address = "https://github.com/scanny/python-pptx"

prs.save('textbox_example.pptx')
```

### 位置とサイズの設定（EMU単位）

```python
from pptx.util import Inches, Pt, Cm

# Inchesを使用（最も一般的）
left = Inches(1.5)
top = Inches(2.0)
width = Inches(6.0)
height = Inches(1.0)

# Cmを使用
left = Cm(3.81)    # 1.5インチ相当
top = Cm(5.08)     # 2インチ相当

# EMU単位で直接指定
left = 1371600     # 1.5インチ相当（1.5 * 914400）
top = 1828800      # 2インチ相当

# 作成後に位置・サイズを変更
textbox.left = Inches(2)
textbox.top = Inches(3)
textbox.width = Inches(5)
textbox.height = Inches(1.5)
```

### 注意点とベストプラクティス

1. **テキストフレームへのアクセス**: すべてのShapeがテキストフレームを持つわけではないため、`shape.has_text_frame`で確認する
2. **文字レベルの書式**: Runレベルで適用する（フォント、サイズ、色、太字、斜体）
3. **段落レベルの書式**: Paragraphレベルで適用する（配置、行間隔、インデント）
4. **自動サイズ調整**: `auto_size`と`word_wrap`の組み合わせに注意
5. **余白設定**: テキストが図形の境界に近すぎる場合は余白を調整

---

## 5. 画像操作

### 概要

画像はスライド上に任意の位置・サイズで配置できます。`Shapes.add_picture()`メソッドで追加し、アスペクト比を維持した自動調整も可能です。

### 主要APIメソッド

#### `Shapes.add_picture(image_file, left, top, width=None, height=None) → Picture`

画像を追加します。

**パラメータ:**
- `image_file` (str | IO[bytes]): 画像ファイルパスまたはファイルライクオブジェクト
- `left` (Length): 左上隅のX座標（EMU単位）
- `top` (Length): 左上隅のY座標（EMU単位）
- `width` (Length | None): 幅（EMU単位、オプション）
- `height` (Length | None): 高さ（EMU単位、オプション）

**戻り値:**
- `Picture`: 画像のPictureオブジェクト

### サイズ設定の挙動

| width | height | 動作 |
|-------|--------|------|
| None  | None   | 画像の元のサイズが使用される |
| 指定  | None   | 幅を指定、高さはアスペクト比を保持して自動計算 |
| None  | 指定   | 高さを指定、幅はアスペクト比を保持して自動計算 |
| 指定  | 指定   | 両方指定、アスペクト比に関わらず拡大縮小 |

### コード例

```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()
blank_slide_layout = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank_slide_layout)

# 元のサイズで画像を追加
img_path = 'logo.png'
left = Inches(1)
top = Inches(1)
pic = slide.shapes.add_picture(img_path, left, top)

# 幅を指定、アスペクト比を維持
pic2 = slide.shapes.add_picture(img_path, Inches(2), Inches(2), width=Inches(4))

# 高さを指定、アスペクト比を維持
pic3 = slide.shapes.add_picture(img_path, Inches(3), Inches(3), height=Inches(3))

# 幅と高さを両方指定（アスペクト比無視）
pic4 = slide.shapes.add_picture(
    img_path,
    Inches(1), Inches(4),
    width=Inches(5),
    height=Inches(2)
)

# ファイルライクオブジェクトから画像を追加
from io import BytesIO
with open('image.jpg', 'rb') as f:
    image_stream = BytesIO(f.read())

pic5 = slide.shapes.add_picture(image_stream, Inches(6), Inches(1))

# 画像のサイズと位置を後から変更
pic5.left = Inches(7)
pic5.top = Inches(2)
pic5.width = Inches(2)
pic5.height = Inches(1.5)

# 画像のアスペクト比を取得
aspect_ratio = pic5.width / pic5.height

prs.save('images_example.pptx')
```

### アスペクト比の維持方法

```python
from pptx import Presentation
from pptx.util import Inches

def add_picture_with_max_size(slide, image_path, left, top, max_width, max_height):
    """
    アスペクト比を維持しながら、最大サイズ内に収まるように画像を追加
    """
    # まず元のサイズで追加
    pic = slide.shapes.add_picture(image_path, left, top)

    # 元のサイズを取得
    original_width = pic.width
    original_height = pic.height

    # アスペクト比を計算
    aspect_ratio = original_width / original_height

    # 最大サイズに収まるように調整
    if original_width > max_width or original_height > max_height:
        if max_width / max_height > aspect_ratio:
            # 高さが制約
            pic.height = max_height
            pic.width = int(max_height * aspect_ratio)
        else:
            # 幅が制約
            pic.width = max_width
            pic.height = int(max_width / aspect_ratio)

    return pic

# 使用例
prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[6])
pic = add_picture_with_max_size(
    slide,
    'large_image.jpg',
    Inches(1), Inches(1),
    Inches(8),  # 最大幅
    Inches(5)   # 最大高さ
)

prs.save('aspect_ratio_example.pptx')
```

### 注意点とベストプラクティス

1. **対応画像形式**: PNG, JPEG, GIF, BMP, TIFF等の一般的な形式に対応
2. **ファイルサイズ**: 大きな画像はプレゼンテーションファイルサイズを増大させる
3. **相対パス**: 相対パスを使用する場合、スクリプト実行ディレクトリに注意
4. **アスペクト比**: 品質を保つため、可能な限りアスペクト比を維持する
5. **位置調整**: `left`, `top`プロパティで後から位置を変更可能

---

## 6. 背景設定

### 概要

スライドの背景は`Slide.background`プロパティを介して設定します。単色塗りつぶし、グラデーション、パターン、画像背景をサポートします。

### 主要APIクラス

#### `Slide`クラスの背景関連プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `background` | _Background | スライド背景のプロパティを提供するオブジェクト |
| `follow_master_background` | bool | マスターからの背景継承を制御（True/False） |

#### `_Background`クラス

スライドの背景プロパティを管理します。

**主要プロパティ:**
- `fill` (FillFormat): 背景の塗りつぶし設定

#### `FillFormat`クラス

塗りつぶしプロパティを管理します。

**主要メソッド:**
- `solid()` - 単色塗りつぶしに設定
- `patterned()` - パターン塗りつぶしに設定
- `gradient()` - グラデーション塗りつぶしに設定
- `background()` - 背景として設定

**主要プロパティ:**
- `fore_color` (ColorFormat): 前景色
- `back_color` (ColorFormat): 背景色（パターン塗りつぶし用）
- `type` (MSO_FILL_TYPE): 現在の塗りつぶしタイプ

### 背景色の設定方法

```python
from pptx import Presentation
from pptx.util import Inches
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[6])

# マスター背景の継承を無効化
slide.follow_master_background = False

# 単色背景の設定
background = slide.background
fill = background.fill
fill.solid()
fill.fore_color.rgb = RGBColor(0, 128, 255)  # 青色

# テーマカラーを使用
fill.solid()
fill.fore_color.theme_color = MSO_THEME_COLOR.ACCENT_1

# 明るさ調整
fill.fore_color.brightness = 0.4  # 40%明るくする

prs.save('background_color_example.pptx')
```

### 背景画像の設定方法

```python
from pptx import Presentation
from pptx.util import Inches
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[6])

# 方法1: 全体を覆う画像を追加（背景風）
img_path = 'background.jpg'
left = top = Inches(0)
pic = slide.shapes.add_picture(
    img_path,
    left, top,
    width=prs.slide_width,
    height=prs.slide_height
)

# 画像を最背面に移動（Z-orderを変更）
# 注: python-pptxでは直接Z-orderを変更するAPIがないため、
# 追加順序に注意する（先に追加した要素が背面になる）

# 方法2: XMLレベルでの背景画像設定（高度な方法）
# python-pptxの標準APIではサポートされていないため、
# XMLを直接操作する必要がある

prs.save('background_image_example.pptx')
```

### コード例（包括的）

```python
from pptx import Presentation
from pptx.util import Inches
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR

prs = Presentation()

# スライド1: 単色背景
slide1 = prs.slides.add_slide(prs.slide_layouts[6])
slide1.follow_master_background = False
background1 = slide1.background
fill1 = background1.fill
fill1.solid()
fill1.fore_color.rgb = RGBColor(240, 248, 255)  # AliceBlue

# スライド2: グラデーション背景（テーマカラー）
slide2 = prs.slides.add_slide(prs.slide_layouts[6])
slide2.follow_master_background = False
background2 = slide2.background
fill2 = background2.fill
fill2.solid()
fill2.fore_color.theme_color = MSO_THEME_COLOR.ACCENT_2
fill2.fore_color.brightness = 0.5

# スライド3: 画像背景
slide3 = prs.slides.add_slide(prs.slide_layouts[6])
# 背景画像として全体を覆う画像を追加
pic = slide3.shapes.add_picture(
    'background.png',
    Inches(0), Inches(0),
    width=prs.slide_width,
    height=prs.slide_height
)

# 画像の上にテキストボックスを追加
textbox = slide3.shapes.add_textbox(Inches(2), Inches(2), Inches(6), Inches(1))
text_frame = textbox.text_frame
text_frame.text = "背景画像の上のテキスト"

prs.save('backgrounds_example.pptx')
```

### 注意点とベストプラクティス

1. **マスター継承**: `follow_master_background`をFalseに設定しないと、カスタム背景が適用されない
2. **背景画像**: python-pptxは背景画像の直接設定をサポートしていないため、全体を覆う画像を追加する回避策を使用
3. **Z-order**: 背景として使う要素は最初に追加することで背面に配置される
4. **テーマカラー**: 統一感のあるデザインにはテーマカラーを活用
5. **パフォーマンス**: 背景画像は高解像度すぎるとファイルサイズが増大

---

## 7. マスタースライドとテーマ

### 概要

マスタースライドはプレゼンテーション全体のデザインテンプレートです。テーマカラー、デフォルトフォント、スライドレイアウトを定義します。

### 主要APIクラス

#### `Presentation`クラスのマスター関連プロパティ

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `slide_master` | SlideMaster | プレゼンテーションの第一スライドマスター |
| `slide_masters` | SlideMasters | プレゼンテーション内の全スライドマスター |

#### `SlideMaster`クラス

スライドマスターを表します。

**主要プロパティ:**
- `slide_layouts` (SlideLayouts): このマスターに属するレイアウト
- `shapes` (Shapes): マスター上の図形

#### `SlideLayout`クラス

スライドレイアウトを表します。

**主要プロパティ:**
- `name` (str): レイアウト名
- `slide_master` (SlideMaster): このレイアウトの親マスター
- `shapes` (Shapes): レイアウト上の図形

### マスタースライドのカスタマイズ方法

**注意**: python-pptxは現在、マスタースライドの編集機能を限定的にしかサポートしていません。以下は可能な範囲での操作です。

```python
from pptx import Presentation

# テンプレートファイルから読み込み（推奨）
prs = Presentation('custom_template.pptx')

# マスター情報の取得
master = prs.slide_master
print(f"Master layouts: {len(master.slide_layouts)}")

# レイアウト情報を列挙
for i, layout in enumerate(master.slide_layouts):
    print(f"Layout {i}: {layout.name}")

# 特定のレイアウトを選択してスライドを追加
title_layout = master.slide_layouts[0]
slide = prs.slides.add_slide(title_layout)

prs.save('using_master.pptx')
```

### テーマの適用方法

**推奨アプローチ**: PowerPointでカスタムテーマを作成し、テンプレートファイルとして保存して使用します。

```python
from pptx import Presentation

# カスタムテンプレートを使用
prs = Presentation('my_custom_theme.pptx')

# テンプレートのレイアウトを使用してスライドを追加
for layout in prs.slide_layouts:
    slide = prs.slides.add_slide(layout)

prs.save('themed_presentation.pptx')
```

### デフォルトフォントの設定方法

**注意**: python-pptxはテーマフォントの設定を直接サポートしていません。回避策として、各テキスト要素でフォントを明示的に設定します。

```python
from pptx import Presentation
from pptx.util import Pt

def set_default_font(presentation, font_name, font_size):
    """
    プレゼンテーション内の全テキストにデフォルトフォントを設定

    注: この関数は既存のテキストには適用されない
    新しく追加するテキストにフォントを設定する必要がある
    """
    # 新しいテキストに適用するヘルパー関数
    def apply_font(text_frame):
        for paragraph in text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.name = font_name
                run.font.size = Pt(font_size)

    return apply_font

# 使用例
prs = Presentation()
apply_font = set_default_font(prs, "Arial", 18)

slide = prs.slides.add_slide(prs.slide_layouts[1])
title = slide.shapes.title
title.text = "タイトル"
apply_font(title.text_frame)

prs.save('default_font_example.pptx')
```

### コード例（テンプレート活用）

```python
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor

# カスタムテンプレートを読み込み
template_path = 'corporate_template.pptx'
prs = Presentation(template_path)

# テンプレートのレイアウトを列挙
print("Available layouts:")
for i, layout in enumerate(prs.slide_layouts):
    print(f"  {i}: {layout.name}")

# タイトルスライドを追加
title_slide = prs.slides.add_slide(prs.slide_layouts[0])
title = title_slide.shapes.title
subtitle = title_slide.placeholders[1]
title.text = "プレゼンテーションタイトル"
subtitle.text = "サブタイトル"

# コンテンツスライドを追加
content_slide = prs.slides.add_slide(prs.slide_layouts[1])
title = content_slide.shapes.title
title.text = "コンテンツページ"

# テンプレートに定義されたテーマカラーを使用
# （マスタースライドで定義されたカラースキームが自動適用される）

prs.save('templated_presentation.pptx')
```

### 注意点とベストプラクティス

1. **テンプレート使用**: マスターやテーマのカスタマイズはPowerPointで行い、テンプレートファイルとして保存
2. **読み取り専用**: python-pptxはマスターの読み取りは可能だが、編集機能は限定的
3. **フォント設定**: デフォルトフォントはテキスト追加時に個別に設定する必要がある
4. **テーマカラー**: `MSO_THEME_COLOR`を使用してテーマカラーを参照
5. **一貫性**: 同じテンプレートを使用することでプレゼンテーション間の一貫性を保つ

---

## 8. 単位変換

### 概要

python-pptxは内部的にEMU（English Metric Units）を使用しますが、`pptx.util`モジュールが便利な変換ユーティリティを提供します。

### EMU（English Metric Units）について

- PowerPointの内部単位
- 1インチ = 914400 EMU
- 1センチ = 360000 EMU
- 1ポイント = 12700 EMU

### 主要な単位クラス

#### `Length`基底クラス

すべての単位クラスの基底クラスです。

**利用可能なコンストラクタクラス:**

| クラス | 説明 | 例 |
|-------|------|-----|
| `Inches` | インチ単位 | `Inches(1.5)` |
| `Cm` | センチメートル単位 | `Cm(3.81)` |
| `Mm` | ミリメートル単位 | `Mm(38.1)` |
| `Pt` | ポイント単位 | `Pt(12)` |
| `Emu` | EMU単位 | `Emu(914400)` |
| `Centipoints` | ポイントの1/100 | `Centipoints(1200)` |

### 利用可能な変換プロパティ

`Length`オブジェクトから各単位への変換が可能です：

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| `.inches` | float | インチ単位 |
| `.cm` | float | センチメートル単位 |
| `.mm` | float | ミリメートル単位 |
| `.pt` | float | ポイント単位 |
| `.emu` | int | EMU単位 |
| `.centipoints` | int | ポイントの1/100単位 |

### インチとEMUの変換

```python
from pptx.util import Inches

# インチからEMUへ変換
length = Inches(1)
print(length.emu)        # 914400

# EMU値を取得
left = Inches(1.5)
left_emu = left          # EMU値として使用可能（内部的にintに変換）

# インチ値を取得
print(length.inches)     # 1.0

# 他の単位への変換
print(length.cm)         # 2.54
print(length.mm)         # 25.4
print(length.pt)         # 72.0
```

### PtとEMUの変換

```python
from pptx.util import Pt

# ポイントからEMUへ変換
font_size = Pt(12)
print(font_size.emu)     # 152400

# ポイント値を取得
print(font_size.pt)      # 12.0

# インチへの変換
print(font_size.inches)  # 0.16666...

# センチメートルへの変換
print(font_size.cm)      # 0.423...
```

### コード例（包括的）

```python
from pptx.util import Inches, Cm, Mm, Pt, Emu

# インチを基準とした変換
one_inch = Inches(1)
print(f"1 inch = {one_inch.emu} EMU")              # 914400
print(f"1 inch = {one_inch.cm} cm")                # 2.54
print(f"1 inch = {one_inch.mm} mm")                # 25.4
print(f"1 inch = {one_inch.pt} pt")                # 72.0
print(f"1 inch = {one_inch.centipoints} cp")       # 7200

# ポイントを基準とした変換
twelve_pt = Pt(12)
print(f"12 pt = {twelve_pt.emu} EMU")              # 152400
print(f"12 pt = {twelve_pt.inches} inches")        # 0.16666...
print(f"12 pt = {twelve_pt.cm} cm")                # 0.423...

# センチメートルを基準とした変換
five_cm = Cm(5)
print(f"5 cm = {five_cm.emu} EMU")                 # 1800000
print(f"5 cm = {five_cm.inches} inches")           # 1.968...
print(f"5 cm = {five_cm.mm} mm")                   # 50.0

# EMUから他の単位への変換
emu_value = Emu(914400)
print(f"914400 EMU = {emu_value.inches} inches")   # 1.0
print(f"914400 EMU = {emu_value.cm} cm")           # 2.54
print(f"914400 EMU = {emu_value.pt} pt")           # 72.0

# 実用例: 位置とサイズの設定
from pptx import Presentation

prs = Presentation()
slide = prs.slides.add_slide(prs.slide_layouts[6])

# 異なる単位で指定
textbox = slide.shapes.add_textbox(
    Inches(1),      # 左位置: 1インチ
    Cm(5),          # 上位置: 5センチ
    Mm(150),        # 幅: 150ミリ
    Pt(72)          # 高さ: 72ポイント（1インチ相当）
)

# 現在の値を取得して別の単位で表示
print(f"Textbox left: {textbox.left} EMU")
print(f"Textbox left: {Emu(textbox.left).inches} inches")
print(f"Textbox left: {Emu(textbox.left).cm} cm")

# EMU値を直接使用
textbox.left = 1828800  # 2インチ相当
textbox.top = 914400    # 1インチ相当

prs.save('units_example.pptx')
```

### 換算表

#### インチ換算

| 単位 | 1インチ = |
|------|----------|
| EMU | 914400 |
| cm | 2.54 |
| mm | 25.4 |
| pt | 72 |
| centipoints | 7200 |

#### ポイント換算

| 単位 | 1ポイント = |
|------|-----------|
| EMU | 12700 |
| inches | 0.01389 (1/72) |
| cm | 0.0353 |
| mm | 0.353 |
| centipoints | 100 |

#### センチメートル換算

| 単位 | 1cm = |
|------|-------|
| EMU | 360000 |
| inches | 0.3937 |
| mm | 10 |
| pt | 28.35 |

### よく使用する変換

```python
from pptx.util import Inches, Pt, Cm

# A4サイズ（210mm x 297mm）
width = Cm(21.0)   # または Mm(210)
height = Cm(29.7)  # または Mm(297)

# 標準的なフォントサイズ
title_size = Pt(32)
body_size = Pt(18)
caption_size = Pt(12)

# 標準的な余白
margin = Inches(0.5)  # または Cm(1.27)

# スライド標準サイズ（16:9）
slide_width = Inches(10)
slide_height = Inches(5.625)
```

### 注意点とベストプラクティス

1. **一貫性**: プロジェクト内で単位を統一する（通常はInchesが推奨）
2. **可読性**: EMU値を直接使用せず、単位クラスを使用する
3. **精度**: EMUはint型のため、小数点以下は切り捨てられる
4. **PowerPoint内部**: PowerPointはEMUとcentipointsで内部保存
5. **変換タイミング**: 計算は単位クラスで行い、最後にEMUに変換

---

## 補足情報

### 主要な列挙型

#### MSO_AUTO_SIZE

テキストフレームの自動サイズ調整モード

| 定数 | 説明 |
|-----|------|
| `NONE` | 自動サイズ調整なし、テキストは境界を超えて拡張 |
| `SHAPE_TO_FIT_TEXT` | 図形がテキストに合わせて調整される |
| `TEXT_TO_FIT_SHAPE` | テキストが図形内に収まるようフォントサイズが縮小 |
| `MIXED` | 複数の設定の組み合わせ（読み取り専用） |

#### MSO_ANCHOR

テキストの垂直配置

| 定数 | 説明 |
|-----|------|
| `TOP` | 上揃え |
| `MIDDLE` | 中央揃え |
| `BOTTOM` | 下揃え |

#### MSO_THEME_COLOR

テーマカラーのインデックス

| 定数 | 説明 |
|-----|------|
| `ACCENT_1` ～ `ACCENT_6` | 強調色1～6 |
| `DARK_1`, `DARK_2` | 濃い色1、2 |
| `LIGHT_1`, `LIGHT_2` | 明るい色1、2 |
| `HYPERLINK` | ハイパーリンク色 |
| `FOLLOWED_HYPERLINK` | クリック済みハイパーリンク色 |

### セキュリティとエラーハンドリング

#### ファイルパス検証

```python
import os
from pptx import Presentation

def safe_open_presentation(file_path):
    """安全にプレゼンテーションファイルを開く"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

    if not file_path.endswith('.pptx'):
        raise ValueError("拡張子が.pptxではありません")

    try:
        prs = Presentation(file_path)
        return prs
    except Exception as e:
        raise RuntimeError(f"プレゼンテーションの読み込みに失敗: {e}")

# 使用例
try:
    prs = safe_open_presentation('presentation.pptx')
except (FileNotFoundError, ValueError, RuntimeError) as e:
    print(f"エラー: {e}")
```

#### RGB値検証

```python
from pptx.dml.color import RGBColor

def safe_rgb_color(r, g, b):
    """RGB値を検証してRGBColorオブジェクトを作成"""
    if not all(0 <= val <= 255 for val in [r, g, b]):
        raise ValueError(f"RGB値は0-255の範囲である必要があります: ({r}, {g}, {b})")

    return RGBColor(r, g, b)

# 使用例
try:
    color = safe_rgb_color(255, 128, 64)
except ValueError as e:
    print(f"エラー: {e}")
```

### パフォーマンス最適化

#### 大量のスライド生成

```python
from pptx import Presentation
from pptx.util import Inches

def create_bulk_slides(count):
    """大量のスライドを効率的に生成"""
    prs = Presentation()
    blank_layout = prs.slide_layouts[6]

    # レイアウトを再利用
    for i in range(count):
        slide = prs.slides.add_slide(blank_layout)
        # スライドの内容を追加

    return prs

# 使用例
prs = create_bulk_slides(100)
prs.save('bulk_slides.pptx')
```

### トラブルシューティング

#### よくある問題と解決策

**Q: フォントが正しく表示されない**
```python
# システムにフォントがインストールされているか確認
font.name = "Arial"  # 正確なフォント名を指定
```

**Q: 画像が追加できない**
```python
# ファイルパスが正しいか確認
import os
if not os.path.exists(image_path):
    print(f"画像が見つかりません: {image_path}")
```

**Q: テキストが図形から溢れる**
```python
# auto_sizeを設定
text_frame.auto_size = MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE
# または
text_frame.word_wrap = True
text_frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
```

**Q: EMU値が大きすぎる**
```python
# 単位クラスを使用
from pptx.util import Inches
left = Inches(1)  # 914400 EMU
# 直接EMU値を使用しない
```

---

## 参考リンク

- **公式ドキュメント**: https://python-pptx.readthedocs.io/
- **GitHub リポジトリ**: https://github.com/scanny/python-pptx
- **PyPI**: https://pypi.org/project/python-pptx/
- **クイックスタートガイド**: https://python-pptx.readthedocs.io/en/latest/user/quickstart.html
- **APIリファレンス**: https://python-pptx.readthedocs.io/en/latest/api/index.html

---

## まとめ

python-pptxは強力なPowerPoint生成ライブラリですが、以下の制約があります：

### サポートされている機能
✅ Presentationの作成・読み込み・保存
✅ スライドの追加とレイアウト指定
✅ スライドサイズの設定
✅ テキストボックスの追加とフォーマット
✅ 画像の追加とサイズ調整
✅ 背景色の設定
✅ 単位変換ユーティリティ

### 制約・未サポート機能
❌ スライドの削除（公式サポートなし）
❌ マスタースライドの編集（読み取りのみ）
❌ 背景画像の直接設定（回避策あり）
❌ Z-orderの直接制御
❌ アニメーション・トランジション

### ベストプラクティス
1. **テンプレート活用**: マスターやテーマはPowerPointで作成し、テンプレートファイルとして使用
2. **単位の一貫性**: プロジェクト内で単位を統一（通常はInches）
3. **エラーハンドリング**: ファイルパスやRGB値の検証を実施
4. **パフォーマンス**: 大量のスライド生成時はレイアウトを再利用
5. **可読性**: EMU値を直接使用せず、単位クラスを活用

---

**作成日**: 2025-12-21
**対象バージョン**: python-pptx 0.6.x
**ドキュメント元**: https://python-pptx.readthedocs.io/
