#-*- coding: utf-8 -*-
from flask import Flask, redirect, url_for, request, abort, Response
import os
import os.path
import datetime
import re
import sys

import hatena_syntax

#============================================================
# Tools
#============================================================

entry_id_pattern = re.compile(r"[0-9]{8}_[0-9]{6}")

def conv_encoding(data, to_enc="utf_8"):
    """
    stringのエンコーディングを変換する
    @param ``data'' str object.
    @param ``to_enc'' specified convert encoding.
    @return str object.
    @note http://speirs.blog17.fc2.com/blog-entry-4.html より
    """
    lookup = ('utf_8', 'euc_jp', 'euc_jis_2004', 'euc_jisx0213',
            'shift_jis', 'shift_jis_2004','shift_jisx0213',
            'iso2022jp', 'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_3',
            'iso2022_jp_ext','latin_1', 'ascii')
    for encoding in lookup:
        try:
            data = data.decode(encoding)
            break
        except:
            pass
    if isinstance(data, unicode):
        return data.encode(to_enc)
    else:
        return data


class UrlMapper(object):
    def getCategoryUrl(self, name):
        return url_for('category_page', cat_name=name )

    def getImageUrl(self, img_id):
        return url_for('image', img_id=img_id)

    def getEntryPageUrl(self, id_or_name):
        return url_for('entry_page', id_or_name=id_or_name)

    def getEntryCreatePageUrl(self):
        return url_for('create_new_entry')

def _renderingHtmlHeader(canvas):
    canvas.header.writeTag('meta', '', {'HTTP-EQUIV':'Content-Style-Type', 'content':'text/css'})
    canvas.header.writeTag('link', '', {'rel':'stylesheet', 'href':url_for('stylesheet'), 'type':'text/css'})

    
def _renderingNaviBar(canvas, entry_id=None):
    canvas.writeOpenTag('div', {'class':'navibar'})
    canvas.writeText('|')
    if entry_id != None:
        canvas.writeTag('a', '編集',    {'href': url_for('edit_entry', entry_id=entry_id)})
        canvas.writeText('|')
    canvas.writeTag('a', 'トップ', {'href': url_for('index')})
    canvas.writeText('|')
    canvas.writeTag('a', '一覧',  {'href': url_for('entry_page', id_or_name='EntryList')})
    canvas.writeText('|')
    canvas.writeTag('a', 'ホーム',  {'href': url_for('entry_page', id_or_name='Home')})
    canvas.writeText('|')
    canvas.writeTag('a', '新しい記事を作る', {'href': url_for('create_new_entry')})
    canvas.writeText('|')
    canvas.writeCloseTag('div')

def _renderingPagingBar(canvas, current_page):
    canvas.writeOpenTag('div', {'class':'pagingbar'})
    canvas.writeText('|')
    if 0 < current_page:
        canvas.writeTag('a', 'newer', {'href':url_for('blog_style_page', page_num=(current_page-1))})
        canvas.writeText('|')
    canvas.writeTag('a', 'older', {'href':url_for('blog_style_page', page_num=(current_page+1))})
    canvas.writeText('|')
    canvas.writeCloseTag('div')

def _loadShebang(filepath):
    f = open(filepath, 'r')
    try:
        for line in f.readlines():
            if len(line.strip()) == 0:
                continue
            elif line[0] == '#':
                if re.match(r"#!", line) != None:
                    return line
            else:
                return ''
        else:
            return ''
    finally:
        f.close()

def _getRenderer(first_line, current_entry_id, context):

    # モジュールのロード
    mod = None
    matobj = re.match(r"#!rendering:(.*)", first_line)
    if matobj != None:
        renderer_module_name = matobj.group(1).strip()
        if renderer_module_name == 'self':
            renderer_module_name = current_entry_id

        mod = loadModule(context._asEntryId(renderer_module_name))

    # レンダラーの生成
    if mod != None:
        return mod.createRenderer(context)
    else:
        return DefaultRenderer(context)


def loadModule(module_name):
    module_file_path = os.path.join(CONTENTS_DIR, module_name)
    module_file      = open(module_file_path,'r')
    try:
        import imp
        mod = imp.load_module(module_name,
                              module_file,
                              module_file_path,
                              ('', 'r', imp.PY_SOURCE)) #suffix, file_open_mode, type
        return mod

    except ImportError:
        return None

    finally:
        module_file.close()


class DefaultRenderer(object):
    def __init__(self, context):
        self.context = context

    def renderViewPage(self, canvas, entry_id):
        filepath = self.context._createEntryFilePath(entry_id)

        # 1. parsing
        scanner = hatena_syntax.FileScanner()
        scanner.openFile(filepath)
        parser  = hatena_syntax.HatenaParser()
        hatena_document = parser.parse(scanner)

        # 2. rendering
        html_renderer = hatena_syntax.HtmlRenderingVisitor(canvas, self.context.url_mapper)
        hatena_document.accept(html_renderer)


class WorldDictionary(object):
    '''世界辞書。ユニークな名前とコンテンツIDのマッピングを行う'''
    def __init__(self, dict_file_path):
        self.dict_file_path = dict_file_path
        self.load()

    def load(self):
        self.dict_ = {} 

        f = open(self.dict_file_path, 'r')
        for line in f.readlines():
            key_value = line.split(':')
            if len(key_value) != 2:
                continue
            key   = key_value[0].strip()
            value = key_value[1].strip()

            if entry_id_pattern.match(value) == None:
                continue

            self.dict_[key] = value
        f.close()

    def save(self):
        f.open(self.dict_file_path, 'w')
        for key, value in self.dict_items.iteritems():
            f.write('%s:%s\n' % (key,value))
        f.close

    def __getitem__(self, key):
        return self.dict_[key]

    def __setitem__(self, key, value):
        self.dict_[key] = value


class EHContext(object):
    '''サーバサイドレンダラーに渡されるコンテキスト'''
    def __init__(self, contents_dir, world_dict, url_mapper, page_func, request):
        self.contents_dir = contents_dir  # コンテンツファイルのパス
        self.world_dict   = world_dict    # 世界辞書
        self.url_mapper   = url_mapper    # url_mapper
        self.page_func    = page_func     # "entry" or "edit_entry" or "save_entry"
        self.request      = request       # flask の 
        self.entry_id     = None

    def setCurrentEntry(self, entry_id_or_name):
        aId = self._asEntryId(entry_id_or_name)
        self.entry_id   = aId
        self.entry_name = entry_id_or_name if entry_id_or_name == aId else ''

    def open(self, entry_id_or_name, mode):
        '''コンテンツファイルを開く'''
        fpath = self._createEntryFilePath(entry_id_or_name)
        f = open(fpath, mode)
        return ContentFileWrapper(entry_id_or_name, f)

    def _asEntryId(self, entry_id_or_name):
        if entry_id_pattern.match(entry_id_or_name) != None:
            return entry_id_or_name
        return self.world_dict[entry_id_or_name]

    def _createEntryFilePath(self, id_or_name):
        entry_id = self._asEntryId(id_or_name)
        return os.path.join(self.contents_dir, entry_id)


def _createContext(entry_id_or_name, page_func):
    url_mapper    = UrlMapper()
    world_dict    = WorldDictionary(WORLD_DICT)

    context = EHContext(CONTENTS_DIR, world_dict,
                        url_mapper, page_func, request)
    context.setCurrentEntry(entry_id_or_name)
    return context


class ContentFileWrapper(object):
    '''contents/ 配下のIDアライズされたファイルの操作ラッパー
    '''

    def __init__(self, entry_id, f):
        self.entry_id = entry_id
        self.f = f

    def readline(self):
        self.f.readline()

    def readlines(self):
        return self.f.readlines()

    def write(self, line):
        self.f.write(conv_encoding(line))

    def close(self):
        self.f.close()


#============================================================
# グローバルオブジェクトの構築
#============================================================

# Application Framework の初期化
app = Flask(__name__)

# 設定情報（パスなど）の読み込み
from setting import *

#============================================================
# URL Mapping
#============================================================
@app.route('/stylesheet.css')
def stylesheet():
    return open(STYLE_SHEET).read()



@app.route("/")
def index():
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)
    html.writeTag('h1', SITE_NAME, {'class':'site_title'})
    _renderingNaviBar(html)

    for dpath, dirs, files in os.walk(CONTENTS_DIR):
        files.sort()
        files.reverse()
        selected_files = [fpath for fpath in files if re.match(r"^[0-9]+_[0-9]+$",fpath) != None][0:DISPLAY_PAGES]

        for fpath in selected_files:
            # 1. parsing
            scanner = hatena_syntax.FileScanner()
            scanner.openFile(os.path.join(CONTENTS_DIR,fpath))
            parser  = hatena_syntax.HatenaParser()
            hatena_document = parser.parse(scanner)

            # 2. rendering
            url_mapper    = UrlMapper()
            html_renderer = hatena_syntax.HtmlRenderingVisitor(html, url_mapper)

            hatena_document.accept(html_renderer)
            html.writeOpenTag('hr')
    _renderingPagingBar(html, 0)
    return html.rendering()


@app.route("/page/<page_num>", methods=['POST','GET'])
def blog_style_page(page_num):
    current_page = int(page_num)

    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)
    html.writeTag('h1', SITE_NAME, {'class':'site_title'})
    _renderingNaviBar(html)

    for dpath, dirs, files in os.walk(CONTENTS_DIR):
        files.sort()
        files.reverse()

        entry_num_st = current_page * DISPLAY_PAGES
        entry_num_ed = entry_num_st + DISPLAY_PAGES
        selected_files = [fpath for fpath in files if re.match(r"^[0-9]+_[0-9]+$",fpath) != None][entry_num_st : entry_num_ed]

        for fpath in selected_files:
            # 1. parsing
            scanner = hatena_syntax.FileScanner()
            scanner.openFile(os.path.join(CONTENTS_DIR,fpath))
            parser  = hatena_syntax.HatenaParser()
            hatena_document = parser.parse(scanner)

            # 2. rendering
            url_mapper    = UrlMapper()
            html_renderer = hatena_syntax.HtmlRenderingVisitor(html, url_mapper)

            hatena_document.accept(html_renderer)
            html.writeOpenTag('hr')

    _renderingPagingBar(html, current_page)
    return html.rendering()


@app.route("/entry/<id_or_name>", methods=['POST','GET'])
def entry_page(id_or_name):
    # 環境構築
    context  = _createContext(id_or_name, 'entry')
    entry_id = context._asEntryId(id_or_name)

    # レンダリングフレームワーク構築
    canvas        = hatena_syntax.HtmlCanvas()
    canvas.header.writeTag('meta', '', {'HTTP-EQUIV':'Content-Style-Type', 'content':'text/css'})
    canvas.header.writeTag('link', '', {'rel':'stylesheet', 'href':url_for('stylesheet'), 'type':'text/css'})
    canvas.header.writeTag('script', '', {'src':'http://www.brython.info/brython.js'})

#    canvas.writeOpenTag('body', {'onload': 'brython()'})

    # ページヘッダの描画
    canvas.writeTag('h1', SITE_NAME, {'class':'site_title'})
    _renderingNaviBar(canvas, entry_id)

    # レンダリングエンジンの同定
    filepath = context._createEntryFilePath(entry_id)
    renderer = _getRenderer(_loadShebang(filepath), entry_id, context)

    # レンダリング
    renderer.renderViewPage(canvas, entry_id)

    return canvas.rendering()


@app.route("/create_new_entry")
def create_new_entry():
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)

    html.writeOpenTag('h1')
    html.writeText('新しいエントリー')
    html.writeCloseTag('h1')

    tmstr = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") 

    html.writeOpenTag('form', {'method':'post',
                               'action': url_for('save_entry', entry_id=tmstr)})
    html.writeTag('textarea', '', {'name':'hatena_entry'})
    html.writeOpenTag('div')
    html.writeOpenTag('input', {'type':'submit',
                                'value':'Accept'})
    html.writeCloseTag('div')
    html.writeCloseTag('form')

    return html.rendering()

@app.route("/edit_entry/<entry_id>")
def edit_entry(entry_id):
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)

    html.writeTag('h1', 'エントリの編集')

    html.writeOpenTag('form', {'method':'post',
                               'action': url_for('save_entry', entry_id=entry_id)})

    rf = open(os.path.join(CONTENTS_DIR,entry_id),'r')
    html.writeTag('textarea', rf.read(), {'name':'hatena_entry'})
    rf.close()

    html.writeOpenTag('div')
    html.writeOpenTag('input', {'type':'submit',
                                'value':'Accept'})
    html.writeCloseTag('div')
    html.writeCloseTag('form')

    return html.rendering()


@app.route("/save_entry/<entry_id>", methods=['POST'])
def save_entry(entry_id):
    wf = open(os.path.join(CONTENTS_DIR,entry_id),'w')
    wf.write(conv_encoding(request.form['hatena_entry']))
    wf.close()

    canvas        = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(canvas)
    _renderingNaviBar(canvas, entry_id)

    # レンダリングエンジンの同定
    context = _createContext(entry_id, 'save_entry')

    filepath = os.path.join(CONTENTS_DIR, entry_id)
    renderer = _getRenderer(_loadShebang(filepath), entry_id, context)

    # レンダリング
    canvas.writeTag('p', '以下のファイルを作成しました。')
    renderer.renderViewPage(canvas, entry_id)

    return canvas.rendering()

@app.route("/category/<cat_name>")
def category_page(cat_name):
    pass


def _getImageContentType(img_id):
    ext = os.path.splitext(img_id)[1].lower()

    if   ext == '.png': return 'image/png'
    elif ext == '.gif': return 'image/gif'
    elif ext == '.jpg': return 'image/jpeg'
    else:
        return 'image/%s' % ext[1:]

@app.route('/image/<img_id>')
def image(img_id):
    try:
        rf = open(os.path.join(CONTENTS_DIR,img_id),'rb')
    except IOError:
        abort(404)

    return Response(rf.read(),
                    content_type=_getImageContentType(img_id))

if __name__ == '__main__':
    app.run(debug=True)
