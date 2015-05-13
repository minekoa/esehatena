* BlogっぽいWikiっぽい何か「エセハテナ」の 駆け足紹介

自分のローカルブロク兼、Python の遊び場です。
ブログっぽく使えますが、**公開すると大変危険** です。

** ○特色
*** 1. はてな記法で記述できます

自分の趣味ではてな記法を採用しました。はてな記法の解釈は
hatena_syntax フォルダ以下の一連のオブジェクトが担います。


*** 2. ページに書いたPython コードがそのまま実行されます

大変恐ろしいことに、ページ内に特定の宣言をつけて
Pythonコードを書くとそれが実行されます。

この際、実行されているスクリプトの持つ権限で
コンピュータ資源を漁ることができてしまいます。

本アプリは現状認証機能もパーミッションもない
ノーガードな代物なので、
絶対にインターネット上に晒さないようにしてください。


** ○技術的構成
実行環境として Python 2.x + Flask が必要です。
Windows(7)/Ubuntu (13.10, 14.04) での動作確認はしています。

** ○構成
>||
/
  +-- webapp.py      ... Flask の Webサーバーで動かすときはこちら
  +-- webapp.wsgi    ... WSGI 経由で動かす場合はこちら
  +-- setting.py     ... 設定ファイルです（設定方法は後述）
  +-- worlddict.txt  ... 将来 Wiki記法をサポートしたときの キーバリューのシリアライズファイル。今は未使用
  +-- hatena_syntax/ ... はてな記法のパーザ
      +-- __init__.py
      +-- hatena_document.py
      +-- hatena_html_renderer.py
      +-- hatena_parser.py
      +-- hatena_inline_parser.py
      +-- unittest_hatena.py          .. ユニットテスト
      +-- unittest.py                 .. ユニットテスト
||<


**○設定
setting.py に設定を記述します
>||
#-*- coding: utf-8 -*-

CONTENTS_DIR  = '/home/foo/Dropbox/contents/esehatena/contents'
SITE_NAME     = 'esehatena'
WORLD_DICT    = '/home/foo/Dropbox/contents/esehatena/worlddict.txt'
STYLE_SHEET   = '/home/foo/Dropbox/contents/esehatena/stylesheet.css'
DISPLAY_PAGES = 3
||<

- CONTENTS_DIR  ..blogページファイルの保存先ディレクトリです
- SITE_NAME     ..このサイトの名前です
- WORLD_DICT    ..Wikiネームを保存するファイルのパスです
- STYLE_SHEET   ..このWebAppに適用されるスタイルシートのパスです
- DISPLAY_PAGES ..1ページに表示ずるページ数を指定します

このサンプルのように Dropbox の同期フォルダなどを指定できるように、という
意図でコンテンツ関連をアプリの相対パスから切り離しています。


**○Python スクリプトの書き方
Webページを作成方法を解説します

以下は Python スクリプトのサンプルです

>||
01|# test renderer
02|#-*- coding: utf-8 -*-
03|#!rendering:self
04|
05|class PythonCodeRenderer(object):
06|    def __init__(self, context):
07|        self.context = context
08|
09|    def renderViewPage(self, canvas, data_path):
10|        canvas.writeTag('h1', '自己定義レンダラーのテスト')
11|
12|        canvas.writeOpenTag('pre')
13|        f = open(data_path, 'r')
14|        for line in f.readlines():
15|           canvas.writeText(line)
16|        canvas.writeCloseTag('pre')
17|
18|def createRenderer(url_mapper):
19|    return PythonCodeRenderer(url_mapper)
||<

*** 1行目 .. このページのタイトルになります
通常は はてな記法で書かれたタイトルがページのタイトルになりますが、
スクリプトページには記述できないので一行目のコメントがタイトルになります

*** 3行目 .. このページのレンダラを指定
このページをレンダリングするレンダラを指定します。
ページIDを指定します(URLの末尾のユニーク名, 例えば "20130107_112828" など)
また、自身をレンダラとする場合は
>||
#!rendering:self 
||<

*** 5行目 .. レンダラクラスの定義
レンダリングを実行するクラスを定義します。
メソッド

- init(self, context)
- renderViewPage(self, canvas, entry_id)

を持つクラスを定義してください。
各メソッドの引数の意味は以下の通りです。

- context  .. EHContext クラスのインスタンス。WebApp.py を差n章
- canvas   .. hatena_syntax.HtmlCanvas クラスのインスタンス。
- entry_id .. レンダリングすべきページのID。string。例えば "20130107_112828" など。

※本コードサンプルでは f = open(entry_id, 'r') 的なことを行っています。
これは entry_id が現状ではファイルの名前になっており、
このコードが実行される時のカレントディレクトリの直下に配置されているので
普通に open 関数で開くことができてしまうためです。

あまりよくないので、将来的には塞ぐつもりです。
実際に実用的なスクリプトを書く場合には、
__init__() で渡された context クラスに容易されている _createEntryFilePath で
パスを取得するようにしてください。

>||
filepath = self.context._createEntryFilePath(entry_id)
||<

*** 18行目 .. レンダラのファクトリメソッドの定義
createRenderer(context) メソッドと定義します。上記で作成したレンダラを返すメソッドです。


*** サンプル
ページの一覧を表示するスクリプトのサンプルです。

>||
# entry_list(reversed)
#-*- coding: utf-8 -*-
#!rendering: self

import re
import os

class EntryListRenderer(object):
    def __init__(self, context):
        self.context = context

    def renderViewPage(self, html, filepath):
        html.writeTag('h1', '一覧（逆順）')

        html.writeOpenTag('p')
        html.writeTag('a', '新しい記事を作る',
                      {'href': self.context.url_mapper.getEntryCreatePageUrl()})
        html.writeCloseTag('p')

        html.writeOpenTag('table', {'border':'1'})
        for dpath, dirs, files in os.walk(self.context.contents_dir):
            files.sort()
            files.reverse()

            for fpath in files:
                if re.match(r"^[0-9]+_[0-9]+$", fpath) == None:
                    continue

                path = os.path.join(dpath, fpath)
                f = open(path, 'r')
                headline = f.readline().strip()
                if len(headline) == 0:
                    headline = '(無題)'
                elif headline[0] == '*':
                    headline = headline[1:]

                html.writeOpenTag('tr')
                html.writeOpenTag('td')
                html.writeTag('a', headline,
                              {'href': self.context.url_mapper.getEntryPageUrl(fpath)})
                html.writeCloseTag('td')
                html.writeCloseTag('tr')
                f.close()
        html.writeCloseTag('table')

def createRenderer(mapper):
    return EntryListRenderer(mapper)
||<

**○その他
あとはコードを読むなりしてください。

このページは 本 WebApp で使用している記法をつかっているので、
新しいページを作ってコピペしておくといいでしょう。

それではお楽しみください。

―以上―
