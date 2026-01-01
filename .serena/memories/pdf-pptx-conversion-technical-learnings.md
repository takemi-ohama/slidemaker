# PDF→PowerPoint変換の技術的な学び

## 問題解決の記録

### 問題1: 座標が2倍スケールでスライド境界外に配置

**症状**:
```
要素の座標例:
- left: 9458325 EMU （スライド幅: 9144000 EMU を超過）
- width: 18288000 EMU （スライド幅の2倍）
```

**根本原因**:

座標変換の不整合により、要素サイズが2倍になっていた。

```
変換フロー:
1. LLM: 100% → ImageAnalyzer: 1920 pixels (slide_dimensions)
2. 1920 pixels → TextRenderer: 1920 * 9525 = 18,288,000 EMU
3. 実際のスライド幅: 9,144,000 EMU （10インチ × 914,400 EMU/inch）

問題: 18,288,000 ÷ 9,144,000 = 2倍のスケールエラー
```

**解決策**:

`slide_dimensions` をEMU変換レートに合わせる。

```python
# 修正前
slide_dimensions: tuple[int, int] = (1920, 1080)

# 修正後
slide_dimensions: tuple[int, int] = (960, 540)

# 理由: 9,144,000 EMU ÷ 9525 EMU/pixel = 960 pixels
```

**教訓**: PowerPointのEMU単位系とピクセル座標の対応を正確に保つ必要がある。

---

### 問題2: 画像要素が部分的にしか表示されない

**症状**:
- 1枚目: 4つの歯車図のうち2つのみ表示
- 3枚目: 右側の青いボックス群が欠けている

**根本原因**:

LLMが画像要素の境界を過小評価している。

```
LLMの認識:
{
  "type": "image",
  "position": {"x": 20, "y": 15},  // パーセンテージ
  "size": {"width": 40, "height": 30}  // 実際より小さい
}

実際の図表: もっと広い範囲を占めている
```

**解決策1**: 画像切り出し時に自動的に余白（padding）を追加

```python
# src/slidemaker/workflows/conversion.py
padding_ratio = 0.25  # 25%の余白を追加
padding_x = int(width_px * padding_ratio)
padding_y = int(height_px * padding_ratio)

# 座標を広げる
x_px = max(0, x_px - padding_x)
y_px = max(0, y_px - padding_y)
width_px = min(img_width - x_px, width_px + 2 * padding_x)
height_px = min(img_height - y_px, height_px + 2 * padding_y)
```

**解決策2**: プロンプト改善でLLMの検出精度を向上

```python
# src/slidemaker/llm/prompts/image_processing.py
CRITICAL FOR IMAGE ELEMENTS:
- Diagrams, charts, icons, and illustrations should be detected as IMAGE elements
- Include the COMPLETE boundaries of all graphic elements, including:
  * All connected shapes, boxes, arrows, and lines
  * Related labels and annotations within the graphic
  * Sufficient margin to avoid cropping important parts
- For complex diagrams with multiple components, specify coordinates that encompass ALL parts
- When in doubt, make the image boundaries LARGER rather than smaller
```

**教訓**: 
1. LLMの座標推定には誤差があることを前提とした後処理が必要
2. プロンプトで明示的に「完全な境界」を指示すると精度が向上
3. padding比率（15%→25%）は試行錯誤で最適値を見つける

---

## PowerPoint座標系の理解

### EMU（English Metric Units）

PowerPointの内部座標単位。

```
1 inch = 914,400 EMU
1 cm = 360,000 EMU
1 pixel ≈ 9,525 EMU（96 DPI想定）
```

### 16:9スライドのサイズ

```
幅: 10 inches = 9,144,000 EMU = 960 pixels
高さ: 5.625 inches = 5,143,500 EMU = 540 pixels

比率: 9,144,000 ÷ 9,525 ≈ 960
```

### 座標変換フロー

```
LLMの出力（パーセンテージ）
  ↓
ImageAnalyzer: パーセンテージ → pixels
  position.x = percentage_x * slide_dimensions[0] / 100
  ↓
TextRenderer/ImageRenderer: pixels → EMU
  left = position_x * EMU_PER_PIXEL
  ↓
python-pptx: EMUで配置
```

**重要**: `slide_dimensions` と `EMU_PER_PIXEL` の組み合わせが、最終的なスライドサイズと一致する必要がある。

```python
# 正しい組み合わせ
slide_dimensions = (960, 540)
EMU_PER_PIXEL = 9525

# 検証
960 * 9525 = 9,144,000 EMU ✓ (スライド幅と一致)
540 * 9525 = 5,143,500 EMU ✓ (スライド高さと一致)
```

---

## LLMによる画像分析の特性

### 長所

1. **意味理解**: 図表の種類（フローチャート、組織図等）を理解できる
2. **柔軟性**: 多様なレイアウトに対応可能
3. **テキスト抽出**: 画像内のテキストを正確に認識

### 短所

1. **座標精度**: ピクセル単位の正確な座標は苦手
2. **過小評価**: 図表の境界を控えめに推定する傾向
3. **複雑な図表**: 複数コンポーネントを持つ図表で一部を見落とすことがある

### 対策

1. **後処理でのpadding追加**: 座標誤差を吸収
2. **プロンプト設計**: 「完全な境界」「すべて含める」を明示
3. **検証フィードバックループ**: 生成→検証→修正のサイクル

---

## ベストプラクティス

### 1. 座標系の一貫性

```python
# プロジェクト全体で統一
SLIDE_WIDTH_PX = 960
SLIDE_HEIGHT_PX = 540
EMU_PER_PIXEL = 9525

# 検証コード
assert SLIDE_WIDTH_PX * EMU_PER_PIXEL == 9_144_000
assert SLIDE_HEIGHT_PX * EMU_PER_PIXEL == 5_143_500
```

### 2. padding比率の調整

```python
# 画像要素の種類によって調整可能
if element.alt_text.contains("diagram"):
    padding_ratio = 0.30  # 複雑な図表は広めに
elif element.alt_text.contains("icon"):
    padding_ratio = 0.15  # シンプルなアイコンは狭めに
else:
    padding_ratio = 0.25  # デフォルト
```

### 3. プロンプトでの具体例

```python
# 良い例を含める
Examples:
- Complex diagram with multiple boxes on right side:
  position: {{"x": 50, "y": 20}}, size: {{"width": 50, "height": 60}}
  (ensure ALL boxes are included)
```

---

## 今後の改善アイデア

### 1. 画像要素の自動検証

生成後に画像を再度LLMで分析し、切り出し範囲が適切かチェック。

```python
# 切り出した画像をLLMに送信
response = llm.analyze_image(cropped_image, prompt="""
Is this a complete diagram/chart without any cropping?
If any parts are cut off, respond with 'incomplete'.
""")

if response == "incomplete":
    # padding比率を増やして再切り出し
```

### 2. 学習データの蓄積

正しい座標データを蓄積し、Few-shot promptingで精度向上。

### 3. ハイブリッドアプローチ

画像処理（OpenCV等）でエッジ検出を行い、LLMの座標推定と組み合わせる。

---

## まとめ

PDF→PowerPoint変換における主要な学び:

1. **座標系の理解**: EMU単位系とピクセル座標の対応を正確に保つ
2. **LLMの特性**: 座標推定には誤差があることを前提に後処理で補正
3. **検証ループ**: 生成→キャプチャ→比較→修正のサイクルで品質向上
4. **プロンプト設計**: 明示的な指示でLLMの検出精度が向上
5. **padding比率**: 試行錯誤で最適値を見つける（15%→25%で改善）

これらの知見により、画像要素の表示完全性が大幅に向上しました。
