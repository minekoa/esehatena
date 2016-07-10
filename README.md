# BlogっぽいWikiっぽい何か「エセハテナ」の 駆け足紹介

自分のローカルブロク兼、Python の遊び場です。
ブログっぽく使えますが、**公開すると大変危険** です。

## 特色

### 1. はてな記法で記述できます

自分の趣味ではてな記法を採用しました。はてな記法の解釈は
hatena_syntax フォルダ以下の一連のオブジェクトが担います。

### 2. ページに書いたPython コードがそのまま実行されます

大変恐ろしいことに、ページ内に特定の宣言をつけて
Pythonコードを書くとそれが実行されます。

この際、実行されているスクリプトの持つ権限で
コンピュータ資源を漁ることができてしまいます。

本アプリは現状認証機能もパーミッションもない
ノーガードな代物なので、
絶対にインターネット上に晒さないようにしてください。


## 技術的構成

実行環境として Python 2.x + Flask が必要です。
Windows(7)/Ubuntu (14.04) での動作確認はしています。

## 構成

```
/
  +-- run.py         ... Flask の Webサーバーで動かすときはこちら
  +-- esehatena/     ... アプリケーション本体です
      +-- __init__.py
      +-- models.py           .. モデル
      +-- views.py            .. ビュー
      +-- page_completer.py   .. title記法があった時、urlからタイトルを拾ってくるモジュール
      +-- my_enc_tool.py      .. 文字列エンコードのユーティリティ
  +-- hatena_syntax/ ... はてな記法のパーザ
      +-- __init__.py
      +-- hatena_document.py
      +-- hatena_html_renderer.py
      +-- hatena_parser.py
      +-- hatena_inline_parser.py
      +-- unittest_hatena.py          .. ユニットテスト
      +-- unittest.py                 .. ユニットテスト
  +-- instance_sample/    ... インスタンスのサンプル。 instance にリネームしてテンプレートとして使用できます
      +-- confing.py      ... 設定ファイルです（設定方法は後述）
      +-- worlddict.txt   ... キーバリューのシリアライズファイル。Wikiワードの登録先です
      +-- stylesheet.css  ... スタイルシートです（staticに配置しないのは将来はentry にしたいので)
      +-- contents/       ... コンテンツの格納先フォルダです
        +-- 20150927_225524  ... 一覧（逆順）のレンダラーサンプルです
        +-- 20150927_225956  ... Python コードレンダラーのサンプルです
        +-- 20160402_133925  ... カテゴリ別一覧のレンダラーサンプルです
        +-- 20160710_210502  ... ホームページのサンプルです
```

## 設定

instance/config.py に設定を記述します

```
#-*- coding:utf-8 -*-

CONTENTS_DIR  = './instance/contents/'
SITE_NAME     = 'esehatena'
WORLD_DICT    = './instance/worlddict.txt'
STYLE_SHEET   = './instance/stylesheet.css'
DISPLAY_PAGES = 3
```

* CONTENTS_DIR  ..blogページファイルの保存先ディレクトリです
* SITE_NAME     ..このサイトの名前です
* WORLD_DICT    ..Wikiネームを保存するファイルのパスです
* STYLE_SHEET   ..このWebAppに適用されるスタイルシートのパスです
* DISPLAY_PAGES ..1ページに表示ずるページ数を指定します

このサンプルのように Dropbox の同期フォルダなどを指定できるように、という
意図でコンテンツ関連をアプリの相対パスから切り離しています。

## 固定辞書の作成

worlddict.txt は、ページID の代わりになる
ページに任意の名前付けを行う、辞書になっています。

|*キー名       |*意味                                                                   |
|PythonRenderer|Pythonのソースコードをレンダリングするレンダラ                          |
|EntryList     |ヘッダのナビバーにある「一覧」で呼ばれるページ。一覧レンダラを指定します|
|Home          |ヘッダのナビバーにある「ホーム」で呼ばれるページ                        |

そのうち、EntryList、PythonRenderer、 Home は予約された名前になっています。

EntryList, PythonRenderer は、最初はinstance_sampleの該当ファイルを紐付けたままにしておくことをおすすめします
>||
EntryList:20150927_225524
PythonRenderer:20150927_225956
||<


## Python スクリプトの書き方

Webページを作成方法を解説します

以下は Python スクリプトのサンプルです

```
01|# Python code renderer
02|#!rendering:self
03|
04|class PythonCodeRenderer(object):
05|    def __init__(self, context):
06|        self.context = context
07|
08|    def renderViewPage(self,canvas, entry):
09|        canvas.writeOpenTag('pre')
10|        for line in entry.readlines():
11|            canvas.writeText(line)
12|        canvas.writeCloseTag('pre')
13|
14|def createRenderer(mapper):
15|    return PythonCodeRenderer(mapper)
```

### 1行目 .. このページのタイトルになります

通常は はてな記法で書かれたタイトルがページのタイトルになりますが、
スクリプトページには記述できないので一行目のコメントがタイトルになります

### 2行目 .. このページのレンダラを指定

このページをレンダリングするレンダラを指定します。

指定できるのは

* ページID (URLの末尾のユニーク名, 例えば "20130107_112828" など)
* WorldDict のキー
* 予約後 "self"

のいずれかです。

### 4行目 .. レンダラクラスの定義

レンダリングを実行するクラスを定義します。
メソッド

* init(self, context)
* renderViewPage(self, canvas, entry)

を持つクラスを定義してください。
各メソッドの引数の意味は以下の通りです。

* context  .. EHContext クラスのインスタンス。models.pyを参照
* canvas   .. hatena_syntax.HtmlCanvas クラスのインスタンス。
* entry_id .. EHEntry クラスのインスタンス。models.pyを参照


### 14行目 .. レンダラのファクトリメソッドの定義

createRenderer(context) メソッドと定義します。上記で作成したレンダラを返すメソッドです。

## その他

あとはコードを読んでください。基本はてな記法なのですが、一部オリジナルになってしまってるので、
そのうちにサンプルページにマニュアル書こうかな？と思ってます。


それではお楽しみください。

―以上―
