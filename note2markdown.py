import xml.etree.ElementTree as ET
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Union
import re
import html
from bs4 import BeautifulSoup


class XMLParser:
    """XMLファイルを再帰的に読み込み、構造を解析するパーサー"""
    
    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.tree = None
        self.root = None
        
    def parse(self) -> ET.Element:
        """XMLファイルを読み込み、エレメントツリーを作成"""
        try:
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
            return self.root
        except ET.ParseError as e:
            print(f"XMLパースエラー: {e}")
            raise
        except FileNotFoundError as e:
            print(f"ファイルが見つかりません: {self.xml_path}")
            raise
    
    def get_structure(self, element: Optional[ET.Element] = None, level: int = 0) -> Dict:
        """XML構造を再帰的に辿り、階層構造を取得"""
        if element is None:
            element = self.root
            
        result = {
            'tag': element.tag,
            'attributes': element.attrib,
            'text': element.text.strip() if element.text else '',
            'children': []
        }
        
        for child in element:
            result['children'].append(self.get_structure(child, level + 1))
            
        return result
    
    def print_structure(self, element: Optional[ET.Element] = None, level: int = 0):
        """XML構造を再帰的に表示"""
        if element is None:
            element = self.root
            
        indent = "  " * level
        tag_name = self._cleanup_tag_name(element.tag)
        print(f"{indent}{tag_name}: {element.attrib}")
        
        if element.text and element.text.strip():
            print(f"{indent}  text: {element.text.strip()[:100]}...")
            
        for child in element:
            self.print_structure(child, level + 1)
    
    def _cleanup_tag_name(self, tag: str) -> str:
        """名前空間を除去したタグ名を取得"""
        if '}' in tag:
            return tag.split('}')[-1]
        return tag
    
    def _find_element_by_tag_variants(self, element: ET.Element, tag_variants: List[str]) -> Optional[ET.Element]:
        """複数のタグバリエーションで要素を探す"""
        for variant in tag_variants:
            # 完全一致
            exact_match = element.find(variant)
            if exact_match is not None:
                return exact_match
            
            # WordPress.orgのプレフィックス付きのタグ
            wp_tag = ".//{{{*}}}:" + variant
            wp_match = element.find(wp_tag)
            if wp_match is not None:
                return wp_match
            
            # 任意の名前空間を持つタグ
            ns_tag = ".//{{{*}}}" + variant
            ns_match = element.find(ns_tag)
            if ns_match is not None:
                return ns_match
        
        return None
    
    def _find_text_by_tag_variants(self, element: ET.Element, tag_variants: List[str]) -> str:
        """複数のタグバリエーションで要素のテキストを探す"""
        found_element = self._find_element_by_tag_variants(element, tag_variants)
        if found_element is not None and found_element.text:
            return found_element.text.strip()
        return ""
    
    def find_articles(self, article_tag: str = 'item') -> List[ET.Element]:
        """特定のタグ（デフォルトは'item'）を持つ要素を探す"""
        if self.root is None:
            self.parse()
        
        return self.root.findall(f".//{article_tag}")
    
    def extract_article_content(self, article_element: ET.Element) -> Dict:
        """記事要素からコンテンツを抽出"""
        content = {
            'title': '',
            'link': '',
            'description': '',
            'content': '',
            'pubDate': '',
            'post_id': '',
            'guid': '',
            'post_date': '',
            'post_date_gmt': '',
            'post_modified': '',
            'post_modified_gmt': '',
            'comment_status': '',
            'ping_status': '',
            'post_name': '',
            'status': '',
            'post_parent': '',
            'menu_order': '',
            'post_type': '',
            'post_password': '',
            'is_sticky': '',
            'creator': '',
            'other_metadata': {}
        }
        
        # WordPress名前空間の要素を探す
        wp_elements = {}
        for elem in article_element:
            tag_name = self._cleanup_tag_name(elem.tag)
            if 'wordpress.org' in elem.tag or '{}' in elem.tag:
                wp_elements[tag_name] = elem.text.strip() if elem.text else ''
        
        # タイトル
        content['title'] = self._find_text_by_tag_variants(article_element, ['title'])
        
        # リンク
        content['link'] = self._find_text_by_tag_variants(article_element, ['link'])
        
        # GUID
        content['guid'] = self._find_text_by_tag_variants(article_element, ['guid'])
        
        # 作成者（名前空間付き要素）
        creator_elem = article_element.find('.//{http://purl.org/dc/elements/1.1/}creator')
        if creator_elem is not None and creator_elem.text:
            content['creator'] = creator_elem.text.strip()
        
        # コンテンツ（エンコードされた内容）
        encoded_elem = article_element.find('.//{http://purl.org/rss/1.0/modules/content/}encoded')
        if encoded_elem is not None and encoded_elem.text:
            content['content'] = encoded_elem.text.strip()
        
        # WordPressのメタデータ
        for key, value in wp_elements.items():
            if key in content:
                content[key] = value
            else:
                content['other_metadata'][key] = value
        
        return content


class MarkdownExporter:
    """抽出した記事をMarkdown形式でエクスポート"""
    
    def __init__(self, output_dir: str = "assets"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_article(self, article_content: Dict, index: int = 0) -> str:
        """単一の記事をMarkdownファイルに保存"""
        # ファイル名を生成（タイトルベースまたはインデックスベース）
        if article_content['title']:
            filename = f"{self._sanitize_filename(article_content['title'])}.md"
        else:
            filename = f"article_{index:03d}.md"
        
        filepath = self.output_dir / filename
        
        # HTMLコンテンツをMarkdownに変換
        if article_content['content']:
            article_content['content'] = self.html_to_markdown(article_content['content'])
        
        # Markdownコンテンツを生成
        markdown_content = self._format_as_markdown(article_content)
        
        # ファイルに書き込み
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return str(filepath)
    
    def html_to_markdown(self, html_content: str) -> str:
        """HTMLをMarkdownに変換"""
        if not html_content:
            return ""
            
        # Beautiful Soupを使用してHTMLをパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 各要素を適切なMarkdownに変換
        self._process_element(soup)
        
        # テキストを取得して整形
        markdown = soup.get_text('\n', strip=False)
        
        # 複数の空行を2行以下に制限
        markdown = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown)
        
        # 行末の空白を削除
        markdown = re.sub(r' +$', '', markdown, flags=re.MULTILINE)
        
        return markdown.strip()
    
    def _process_element(self, element):
        """HTML要素を再帰的に処理してMarkdownに変換"""
        if element.name == 'h1':
            element.string = f"# {element.string}\n\n"
        elif element.name == 'h2':
            element.string = f"## {element.string}\n\n"
        elif element.name == 'h3':
            element.string = f"### {element.string}\n\n"
        elif element.name == 'h4':
            element.string = f"#### {element.string}\n\n"
        elif element.name == 'h5':
            element.string = f"##### {element.string}\n\n"
        elif element.name == 'h6':
            element.string = f"###### {element.string}\n\n"
        elif element.name == 'p':
            # 段落は改行とそのあとの空行で区切る
            if element.string:
                element.string = f"{element.string}\n\n"
            else:
                # 子要素を含む場合も適切に処理
                text = []
                for child in element.children:
                    if isinstance(child, str):
                        text.append(child.strip())
                    else:
                        # 再帰的に処理
                        self._process_element(child)
                        text.append(child.get_text())
                element.string = " ".join(text) + "\n\n"
        elif element.name == 'a':
            href = element.get('href', '')
            text = element.string or href
            element.string = f"[{text}]({href})"
        elif element.name == 'img':
            src = element.get('src', '')
            alt = element.get('alt', '')
            element.string = f"![]({src})"
        elif element.name == 'figure':
            # figureは画像として扱う
            img = element.find('img')
            if img:
                src = img.get('src', '')
                alt = img.get('alt', '')
                figcaption = element.find('figcaption')
                caption = figcaption.string if figcaption else ''
                element.string = f"![{caption}]({src})\n\n"
        elif element.name == 'figcaption':
            # figcaptionは単独で処理しない（figureで処理）
            element.string = ""
        elif element.name == 'ul':
            # リストの処理
            items = []
            for li in element.find_all('li', recursive=False):
                li_text = li.get_text().strip()
                items.append(f"- {li_text}")
            element.string = "\n".join(items) + "\n\n"
        elif element.name == 'ol':
            # 順序付きリストの処理
            items = []
            for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                li_text = li.get_text().strip()
                items.append(f"{idx}. {li_text}")
            element.string = "\n".join(items) + "\n\n"
        elif element.name == 'br':
            element.string = "\n"
        
        # name属性やid属性を削除（Beautiful Soupが自動的に処理）
        # 子要素も再帰的に処理
        for child in element.find_all(recursive=True):
            self._process_element(child)
    
    def _sanitize_filename(self, filename: str) -> str:
        """ファイル名として使用できない文字を置換"""
        import re
        import unicodedata
        
        # 特殊文字を適切に処理
        filename = str(filename)
        # パーセントエンコーディングをデコード
        try:
            import urllib.parse
            filename = urllib.parse.unquote(filename)
        except:
            pass
        
        # Unicode正規化
        filename = unicodedata.normalize('NFKC', filename)
        
        # 不適切な文字を置換
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)  # 連続する空白をアンダースコアに
        
        # ファイル名の長さを制限（最大100文字）
        return filename[:100]
    
    def _format_as_markdown(self, article_content: Dict) -> str:
        """記事内容をMarkdown形式に整形"""
        lines = []
        
        # FrontMatterの生成
        lines.append("---")
        
        # メタデータのフォーマット
        def safe_value(value):
            if value is None:
                return "None"
            if value == "":
                return '""'
            # エスケープ処理
            value_str = str(value)
            if ':' in value_str or '\n' in value_str or '"' in value_str:
                value_str.replace('"', '\\"')
                return f'"{value_str}"'
            return value_str
        
        # 基本的なフィールド
        lines.append(f"title: {safe_value(article_content['title'])}")
        lines.append(f"post_id: {safe_value(article_content['post_id'])}")
        lines.append(f"link: {safe_value(article_content['link'])}")
        lines.append(f"guid: {safe_value(article_content['guid'])}")
        lines.append(f"description: {safe_value(article_content['description'])}")
        lines.append(f"pubDate: {safe_value(article_content['pubDate'])}")
        lines.append(f"post_date: {safe_value(article_content['post_date'])}")
        lines.append(f"post_date_gmt: {safe_value(article_content['post_date_gmt'])}")
        lines.append(f"post_modified: {safe_value(article_content['post_modified'])}")
        lines.append(f"post_modified_gmt: {safe_value(article_content['post_modified_gmt'])}")
        lines.append(f"comment_status: {safe_value(article_content['comment_status'])}")
        lines.append(f"ping_status: {safe_value(article_content['ping_status'])}")
        lines.append(f"post_name: {safe_value(article_content['post_name'])}")
        lines.append(f"status: {safe_value(article_content['status'])}")
        lines.append(f"post_parent: {safe_value(article_content['post_parent'])}")
        lines.append(f"menu_order: {safe_value(article_content['menu_order'])}")
        lines.append(f"post_type: {safe_value(article_content['post_type'])}")
        lines.append(f"post_password: {safe_value(article_content['post_password'])}")
        lines.append(f"is_sticky: {safe_value(article_content['is_sticky'])}")
        
        # 追加のメタデータ
        for key, value in article_content.get('other_metadata', {}).items():
            lines.append(f"{key}: {safe_value(value)}")
        
        lines.append("---")
        lines.append("")
        
        # コンテンツ
        if article_content['content']:
            lines.append(article_content['content'])
        else:
            lines.append("(No content)")
        
        return "\n".join(lines)


# メイン処理
def process_xml_to_markdown(xml_path: str, output_dir: str = "assets", article_tag: str = "item"):
    """XMLファイルを読み込み、記事をMarkdownに変換"""
    
    print(f"XMLファイルを読み込んでいます: {xml_path}")
    
    # XMLパーサーとエクスポーターを初期化
    parser = XMLParser(xml_path)
    exporter = MarkdownExporter(output_dir)
    
    try:
        # XMLファイルをパース
        parser.parse()
        
        # XML構造を表示（簡易版）
        print("\nXML構造（簡易表示）:")
        root = parser.root
        print(f"Root tag: {parser._cleanup_tag_name(root.tag)}")
        
        # channelとitemのサンプル構造を表示
        channel = root.find('.//channel')
        if channel is not None:
            print(f"  Channel found")
            print(f"  Channel内の要素数: {len(list(channel))}")
            for i, child in enumerate(channel):
                tag_name = parser._cleanup_tag_name(child.tag)
                print(f"    {tag_name}")
                if tag_name == article_tag:
                    print(f"      (この要素が記事要素です)")
                if i >= 15:  # 最初の15要素だけ表示
                    print("    ...")
                    break
        
        # 記事要素を探す
        articles = parser.find_articles(article_tag)
        print(f"\n{len(articles)}個の記事が見つかりました。")
        
        if len(articles) == 0:
            print("\n警告：記事が見つかりません。以下をチェックしてください：")
            print("1. article_tagが正しいか確認してください（デフォルト：'item'）")
            print("2. XMLファイルの構造を確認してください")
            
            # 全要素の種類を表示
            print("\nXMLファイル内のすべてのタグ：")
            all_tags = set()
            for elem in root.iter():
                tag_name = parser._cleanup_tag_name(elem.tag)
                all_tags.add(tag_name)
            for tag in sorted(all_tags):
                print(f"  - {tag}")
            
            return []
        
        # 各記事を処理
        exported_files = []
        for i, article in enumerate(articles):
            content = parser.extract_article_content(article)
            filepath = exporter.export_article(content, i)
            exported_files.append(filepath)
            print(f"\n記事#{i+1}を保存しました: {filepath}")
            
            # 簡易プレビュー
            if content['title']:
                print(f"  タイトル: {content['title']}")
            print(f"  リンク: {content['link']}")
            print(f"  投稿日: {content['post_date']}")
        
        print(f"\n処理完了！ 合計{len(exported_files)}個のMarkdownファイルを作成しました。")
        print(f"出力ディレクトリ: {output_dir}")
        
        return exported_files
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        raise


# コマンドライン引数の解析
def parse_arguments():
    """コマンドライン引数をパース"""
    import argparse
    parser = argparse.ArgumentParser(description="XMLファイルを読み込み、記事をMarkdownに変換します。")
    
    parser.add_argument("xml_path", help="入力XMLファイルのパス")
    parser.add_argument("-o", "--output", default="assets", help="出力ディレクトリの場所（デフォルト: assets）")
    parser.add_argument("-t", "--tag", default="item", help="記事要素のタグ名（デフォルト: item）")
    
    return parser.parse_args()


# メイン実行コード
if __name__ == "__main__":
    # コマンドライン引数を解析
    args = parse_arguments()
    
    print(f"入力XMLファイル: {args.xml_path}")
    print(f"出力ディレクトリ: {args.output}")
    print(f"記事タグ: {args.tag}")
    print("-" * 50)
    
    # 処理を実行
    try:
        process_xml_to_markdown(
            xml_path=args.xml_path,
            output_dir=args.output,
            article_tag=args.tag
        )
    except Exception as e:
        print(f"処理に失敗しました: {e}")
        exit(1)