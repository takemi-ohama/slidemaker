# PowerPoint Templates Directory

このディレクトリは、PowerPoint MCP サーバーが使用するテンプレートファイルを格納します。

## 概要

PowerPoint MCP サーバー（office-powerpoint-mcp-server）は、以下の形式のテンプレートファイルをサポートします：

- **.pptx** - PowerPointプレゼンテーションファイル
- **.potx** - PowerPointテンプレートファイル

## テンプレートの配置

1. **このディレクトリに配置**
   ```
   templates/
   ├── company_template.pptx
   ├── quarterly_review.potx
   └── brand_guidelines.pptx
   ```

2. **環境変数で別のディレクトリを指定**
   `.claude/mcp.json` で：
   ```json
   {
     "env": {
       "PPT_TEMPLATE_PATH": "./custom_templates:/another/path"
     }
   }
   ```

## 組み込みテンプレート（25以上）

MCPサーバーには、以下の組み込みテンプレートが含まれています：

### タイトル・導入スライド
- `title_slide` - タイトルスライド
- `chapter_intro` - セクション区切り
- `thank_you_slide` - 終了スライド

### コンテンツレイアウト
- `text_with_image` - テキスト+画像
- `two_column_text` - 2列テキスト
- `full_image_slide` - フルサイズ画像

### ビジネス・分析
- `key_metrics_dashboard` - メトリクスダッシュボード
- `before_after_comparison` - 比較スライド
- `data_table_slide` - データテーブル

## カラースキーム（4種類）

- **modern_blue** - Modern Blue
- **corporate_gray** - Corporate Gray
- **elegant_green** - Elegant Green
- **warm_red** - Warm Red

## 使用例

### 組み込みテンプレートの使用

```
「list_slide_templates ツールで利用可能なテンプレートを表示してください」
```

### カスタムテンプレートの使用

```
「templates/company_template.pptxから新しいプレゼンテーションを作成してください」
```

---

**最終更新**: 2024-12-24
