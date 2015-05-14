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
  +-- worlddict.txt  ... キーバリューのシリアライズファイル。現状は固定キーのみ対応。将来はWikiワードとして登録可能にしたい
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

**○固定辞書の作成

worlddict.txt は、ページID の代わりになる
ページに任意の名前付けを行う、辞書になっています。

現状コミットされている worlddict は
>||
PythonRenderer:20130107_112828
TodoRenderer:20130115_083329
EntryList:20130107_124248
Home:20130124_131057
||<

のようになっていますので、
運用時にはお使いの環境で作成した任意のページIDに差し替えてください。

|*キー名       |*意味                                                                   |
|PythonRenderer|Pythonのソースコードをレンダリングするレンダラ                          |
|TodoRenderer  |Todoリストを実現するレンダラ                                            |
|EntryList     |ヘッダのナビバーにある「一覧」で呼ばれるページ。一覧レンダラを指定します|
|Home          |ヘッダのナビバーにある「ホーム」で呼ばれるページ                        |

なお、PythonRenderer, TodoRenderer, EntryList については、
次項「Pythonスクリプトの書き方」内のサンプルをご利用ください。


*** note:
現状 WorldDict を ページIDの代わりに手繰り寄せする仕組みはできているのですが、

- WorldDictを主としたリンクを記述する記法
- WorldDictを動的に更新する機能

が存在していないため、Wiki 名としての利用ができない実装状況です。

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

指定できるのは

- ページID (URLの末尾のユニーク名, 例えば "20130107_112828" など)
- WorldDict のキー
- 予約後 "self"

のいずれかです。

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

**** a) PythonRenderer
Pythonソースコードを表示するためのレンダラです。
本ページのサンプルをあたらしページを作成してコピペした後、そのページIDを
worlddict.txt  に

>||
PythonRenderer:YYYYMMDD_HHMMSS
||<
と登録してください。

>||
# Python code renderer
#!rendering:self

class PythonCodeRenderer(object):
    def __init__(self, context):
        self.context = context

    def renderViewPage(self,canvas, entry_id):
        f = self.context.open(entry_id, 'r')
        canvas.writeOpenTag('pre')
        for line in f.readlines():
            canvas.writeText(line)
        canvas.writeCloseTag('pre')

def createRenderer(mapper):
    return PythonCodeRenderer(mapper)
||<


**** b)ToDoRenderer
TODOリストを実現するレンダラです。
本ページのサンプルをあたらしページを作成してコピペした後、そのページIDを
worlddict.txt  に

>||
TodoRenderer:YYYYMMDD_HHMMSS
||<

と登録してください。

>||
# todo renderer
#-*- coding: UTF-8 -*-
#!rendering:20130107_112828
import re

class TodoItem(object):
    def __init__(self, level, check, text):
        self.id    = None
        self.level = level
        self.check = check
        self.text  = text

    def setId(self, id):
        self.id = id

    def getSource(self):
        return '%s[%s]%s' % (' ' * self.level,
                             self.getCheckChar(),
                             self.text)
    def getCheckChar(self):
       return 'v' if self.check else ''


class TodoList(object):
    def __init__(self, context):
        self.context = context

    def _splitHeader(self, lines):
        isInHeader =True
        header = []
        body   = []
        for line in lines:
            if isInHeader:
                if len(line) == 0 or len(line.strip()) == 0:
                    header.append(line)
                    continue
                if line[0] == '#':
                    header.append(line)
                    continue
                isInHeader = False
            body.append(line)
        return header, body

    def _parseTodoItems(self, lines):
        items = []
        for line in lines:
            item = self._parseTodoItem(line)
            if item != None:
                items.append(item)

        # Unique ID を振る
        for i in range(0, len(items)):
           items[i].setId('todo%02d'%i)
        return items

    def _parseTodoItem(self, source):
        matobj = re.match(r"([ ])?\[([ |v])?\](.*)", source)
        if matobj == None:
            return None

        level = 0     if matobj.group(1) == None else len(matobj.group(1))
        check = False if matobj.group(2) == None else matobj.group(2) == 'v'
        text  = matobj.group(3).strip()
        return TodoItem(level, check, text)

    def _renderTodo(self, canvas, items):
        items.sort(cmp=lambda x, y:cmp(x.id, y.id))

        canvas.writeOpenTag('form',
                             {'method': 'post',
                              'action': self.context.url_mapper.getEntryPageUrl(self.context.entry_id)})
        canvas.writeOpenTag('ul')
        for item in items:
            canvas.writeOpenTag('li')
            canvas.writeRawText('&nbsp;&nbsp;' * item.level )
            canvas.writeTag('input',item.text,
                            {'type' :'checkbox',
                             'name' :item.id,
                             'value':item.getSource(),
                             'checked' if item.check else '': ''})
            canvas.writeCloseTag('li')
        canvas.writeCloseTag('ul')
              
        canvas.writeTag('input', '',
                        {'type' :"submit",
                         'value':'Update'})

        canvas.writeCloseTag('form')

    def renderViewPage(self, canvas, page):
        if self.context.page_func == 'entry' and self.context.request.method == 'POST':
            self.renderPost(canvas, page)
        else:
            self.renderGet(canvas, page)

    def _load(self, page):
        f = self.context.open(page,'r')
        header, lines = self._splitHeader(f.readlines())

        items  = self._parseTodoItems(lines)
        if items == None: items = []

        f.close()
        return header, items

    def _save(self, page, header, items):
        f = self.context.open(page, 'w')

        # ヘッダの書き出し
        for hline in header:
            f.write(hline)

        # コンテンツの書き出し
        items.sort(cmp=lambda x, y:cmp(x.id, y.id))
        for item in items:
            f.write('%s\n' % item.getSource())
        f.close()

    def renderGet(self, canvas, page):
        header, items = self._load(page)
        self._renderTodo(canvas, items)

    def renderPost(self, canvas, page):
        # 編集前todoの取得
        header, ritems = self._load(page)

        # 編集後todoの取得
        checked_items = []
        for key, item in self.context.request.form.iteritems():
            matobj = re.match(r"todo([0-9]+)", key)
            if matobj == None: continue

            item = self._parseTodoItem(item)
            if item != None:
               item.setId(key)
               item.check = True
               checked_items.append(item)
           
        # マージ
        item_dict = {}
        for i in ritems:
           item_dict[i.id] = i
           i.check = False
        for j in checked_items:
           item_dict[j.id] = j

        # レンダリング
        self._renderTodo(canvas, item_dict.values())

        # セーブ
        self._save(page, header, item_dict.values())


def createRenderer(context):
    return TodoList(context)
||<

こんな感じに使えます。
たとえば、以下のような内容でページを作成すると
>||
#!rendering:TodoRenderer

[ ]今日やること
 [ ]起きる
 [ ]朝ご飯をたべる
 [ ]昼ごはんをたべる
 [ ]昼寝をする
 [ ]夕ごはんを食べる
 [ ]寝る
[ ]明日やること
 [ ]家の掃除をする
||<

チェックボックス付きのTODOリストが生成されます。
TODOを実行したら、チェックをしたのち、Update ボタンを押すと
チェックの内容がサーバー上のファイル（つまりこのページの内容）に反映されます。

**** c) EntryList
ページの一覧を表示するスクリプトのサンプルです。

本ページのサンプルをあたらしページを作成してコピペした後、そのページIDを
worlddict.txt  に
>||
EntryList:YYYYMMDD_HHMMSS
||<
と登録してください。
（ベージヘッダのナビバーにある「一覧」から エントリーの一覧表示が可能になります）

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
