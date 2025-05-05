# XML to Markdown Converter

[note.com エクスポート機能](https://www.help-note.com/hc/ja/articles/16143457500953-%E3%82%A8%E3%82%AF%E3%82%B9%E3%83%9D%E3%83%BC%E3%83%88%E6%A9%9F%E8%83%BD%E3%81%AE%E4%BB%95%E6%A7%98)のXMLファイルを読み込み、各記事を個別のMarkdownファイルに変換するツールです。HTMLコンテンツをクリーンなMarkdown形式に自動変換します。

## 特徴

- XMLファイルを再帰的に解析
- 各記事を個別のMarkdownファイルに分割
- HTMLコンテンツを適切なMarkdownに自動変換
- フロントマター形式でメタデータを保持
- WordPress特有の名前空間付きタグに対応
- コマンドライン引数での柔軟な設定

## インストール

必要なパッケージをインストールします：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本的な使用方法

```bash
python note2markdown.py your_export.xml
```

### オプション付きの使用方法

```bash
# 出力ディレクトリを指定
python note2markdown.py your_export.xml -o ./output_directory

# カスタムのタグ名を指定（デフォルトはitem）
python note2markdown.py your_export.xml -t article

# 全オプションを指定
python note2markdown.py your_export.xml -o ./output -t entry
```

### コマンドラインオプション

```bash
positional arguments:
  xml_path              入力XMLファイルのパス

options:
  -h, --help            ヘルプメッセージを表示
  -o, --output OUTPUT   出力ディレクトリの場所（デフォルト: assets）
  -t, --tag TAG         記事要素のタグ名（デフォルト: item）
```

## 出力形式

各記事は以下の形式で保存されます：

```markdown
---
title: "記事のタイトル"
post_id: 123
link: "https://example.com/article"
guid: "n123abc456"
description: ""
pubDate: "Mon, 05 May 2025 11:52:19 +0900"
post_date: "2025-05-05 11:52:19"
post_date_gmt: "2025-05-05 02:52:19"
post_modified: "2025-05-05 11:52:19"
post_modified_gmt: "2025-05-05 02:52:19"
comment_status: "open"
ping_status: "open"
post_name: "article-title"
status: "publish"
post_parent: 0
menu_order: 0
post_type: "post"
post_password: "None"
is_sticky: 0
---

## 見出し例

記事の本文がここに続きます。

HTMLタグは自動的に適切なMarkdownに変換されます。
```

## HTML→Markdown変換

以下のHTML要素が自動的に変換されます：

| HTML | Markdown |
|------|----------|
| `<h1>` ~ `<h6>` | `#` ~ `######` |
| `<p>` | 段落（空行による区切り） |
| `<a>` | `[text](url)` |
| `<img>` | `![alt](src)` |
| `<ul>`/`<li>` | `- item` |
| `<ol>`/`<li>` | `1. item` |
| `<figure>` | キャプション付き画像 |
| `<br>` | 改行 |

## 注意事項

- HTMLの`name`や`id`属性は自動的に削除されます
- ファイル名として使用できない文字は`_`に置換されます
- ファイル名は最大100文字に制限されます
- パーセントエンコーディングは自動的にデコードされます

## エラーハンドリング

- XMLパースエラー時は詳細なエラーメッセージを表示
- 記事が見つからない場合は警告を表示し、XMLファイル内の全タグをリスト表示
- スタックトレースを表示してデバッグを容易に

## ライセンス

MIT License

## 貢献

プルリクエストや課題の報告を歓迎します。

## トラブルシューティング

### よくある問題

1. **記事が見つからない場合**
   - タグ名が正しいか確認してください（デフォルトは`item`）
   - XMLファイルの構造を確認してください

2. **エンコーディングエラー**
   - XMLファイルがUTF-8エンコーディングであることを確認してください

3. **パースエラー**
   - XMLファイルが破損していないか確認してください
   - 無効なXML構造がないか確認してください


## 更新履歴

- v1.0.0: 初回リリース
  - XMLからMarkdownへの基本的な変換機能
  - HTMLコンテンツの自動変換
  - コマンドライン引数対応
