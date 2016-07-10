#-*- coding:utf-8 -*-
from flask import redirect, url_for, request, abort, Response
from models import EHContext, EHEntry, WorldDictionary, getRenderer
from my_enc_tool import *
from page_completer import PageCompleter
import hatena_syntax

import os
import os.path

from . import app

#--------------------------------------------------------------------------------
#　V-M Binding objects
#   依存関係逆転のため、model にインジェクションされるオブジェクト
#--------------------------------------------------------------------------------

class UrlMapper(object):
    """
    flasl.urf_for() のラッパー
    """
    def __init__(self, current_entry_id=None):
        self.current_entry_id = current_entry_id

    def getCategoryUrl(self, name):
        return url_for('category_page', cat_name=name )

    def getImageUrl(self, img_id):
        if self.current_entry_id == None:
            return url_for('image', entry_id='00000000_000000', img_id=img_id)
        else:
            return url_for('image', entry_id=self.current_entry_id, img_id=img_id)

    def getEntryPageUrl(self, id_or_name):
        return url_for('entry_page', id_or_name=id_or_name)

    def getEditEntryUrl(self, entry_id):
        return url_for('edit_entry', entry_id=entry_id)

    def getEntryCreatePageUrl(self):
        return url_for('create_new_entry')

    def clone(self, current_entry_id=None):
        return UrlMapper(current_entry_id)

class RenderingOptions(object):
    '''Renderer に渡すための引数のようなもの'''

    def __init__(self, page_func, request):
        assert( page_func in ["entry", "edit_entry", "save_entry"] )
        self.page_func    = page_func
        self.request      = request       # flask の requestオブジェクト

#--------------------------------------------------------------------------------
# Tool Functions
#--------------------------------------------------------------------------------

def _createContext(page_func):
    url_mapper     = UrlMapper()
    world_dict     = WorldDictionary(app.config["WORLD_DICT"])
    rendering_opts = RenderingOptions(page_func, request)

    context = EHContext(app.config["CONTENTS_DIR"], world_dict,
                        url_mapper, rendering_opts)
    return context

def _getImageContentType(img_id):
    ext = os.path.splitext(img_id)[1].lower()

    if   ext == '.png': return 'image/png'
    elif ext == '.gif': return 'image/gif'
    elif ext == '.jpg': return 'image/jpeg'
    else:
        return 'image/%s' % ext[1:]

def _createNewWikiPage(self, wiki_name, entry_id):
    context = _createContext('entry')
    entry = context.getEntry(entry_id)
    entry.write(conv_encoding("* %s" % wiki_name))

#--------------------------------------------------------------------------------
# Rendering Tools
#--------------------------------------------------------------------------------
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

#--------------------------------------------------------------------------------
# Pages
#--------------------------------------------------------------------------------

@app.route("/")
def index():
    context    = _createContext('entry')
    entry_list = context.getEntryList()[0:app.config["DISPLAY_PAGES"]]

    # レンダリング（ヘッダ）
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)
    html.writeTag('h1', app.config["SITE_NAME"], {'class':'site_title'})
    _renderingNaviBar(html)

    # レンダリング(各コンテンツ)
    for entry in entry_list:
        renderer = getRenderer(context, entry)
        renderer.renderViewPage(html, entry)
        html.writeOpenTag('hr')

    # レンダリング（フッダ）
    _renderingPagingBar(html, 0)
    return html.rendering()

@app.route("/page/<page_num>", methods=['POST','GET'])
def blog_style_page(page_num):
    current_page = int(page_num)
    entry_num_st = current_page * app.config["DISPLAY_PAGES"]
    entry_num_ed = entry_num_st + app.config["DISPLAY_PAGES"]

    context    = _createContext('entry')
    entry_list = context.getEntryList()[entry_num_st : entry_num_ed]

    # レンダリング（ヘッダ）
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)
    html.writeTag('h1', app.config["SITE_NAME"], {'class':'site_title'})
    _renderingNaviBar(html)

    # レンダリング(各コンテンツ)
    for entry in entry_list:
        renderer = getRenderer(context, entry)
        renderer.renderViewPage(html, entry)
        html.writeOpenTag('hr')

    # レンダリング（フッダ）
    _renderingPagingBar(html, current_page)
    return html.rendering()

@app.route("/category/<cat_name>")
def category_page(cat_name):
    context    = _createContext('entry')
    entry_list = [entry for entry in context.getEntryList() 
                  if ez_decode(cat_name) in [ez_decode(cat) for cat in entry.getCategories()]]

    # レンダリング（ページヘッダ）
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)
    html.writeTag('h1', app.config["SITE_NAME"], {'class':'site_title'})
    _renderingNaviBar(html)

    # レンダリング(カテゴリヘッダ % TOC)
    html.writeTag('h2', 'category: "%s"' % cat_name)
    html.writeOpenTag('ul')
    for entry in entry_list:
        html.writeTag('li', entry.getTitle())
    html.writeCloseTag('ul')
    html.writeTag('hr','')

    # レンダリング(各コンテンツ)
    for entry in entry_list:
        renderer = getRenderer(context, entry)
        renderer.renderViewPage(html, entry)
        html.writeOpenTag('hr')

    return html.rendering()

@app.route("/entry/<id_or_name>", methods=['POST','GET'])
def entry_page(id_or_name):
    context  = _createContext('entry')
    entry    = context.getEntry(id_or_name)
    entry_id = context.asEntryId(id_or_name)

    # 名前のときは新しいページの作成へ
    if entry_id != id_or_name and (not context.existEntry(entry_id)):
        return create_new_wiki_entry(id_or_name, entry_id)

    # レンダリング(ヘッダ）
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)
    html.writeTag('h1', app.config["SITE_NAME"], {'class':'site_title'})
    _renderingNaviBar(html, entry_id)

    # レンダリング(本体)
    renderer = getRenderer(context, context.getEntry(entry_id))
    renderer.renderViewPage(html, entry)

    return html.rendering()

@app.route("/create_new_entry")
def create_new_entry():
    context  = _createContext('entry')
    html = hatena_syntax.HtmlCanvas()

    # ヘッダ
    _renderingHtmlHeader(html)
    html.writeOpenTag('h1')
    html.writeText('新しいエントリー')
    html.writeCloseTag('h1')

    tmstr = context.createNewEntryId()

    html.writeOpenTag('form', {'method':'post',
                               'action': url_for('save_entry', entry_id=tmstr)})
    html.writeTag('textarea', '', {'name':'hatena_entry'})
    html.writeOpenTag('div')
    html.writeOpenTag('input', {'type':'submit',
                                'value':'Accept'})
    html.writeCloseTag('div')
    html.writeCloseTag('form')

    return html.rendering()

def create_new_wiki_entry(name, entry_id):
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)

    html.writeOpenTag('h1')
    html.writeText('新しいエントリー')
    html.writeCloseTag('h1')

    html.writeOpenTag('form', {'method':'post',
                               'action': url_for('save_entry', entry_id=entry_id)})
    html.writeTag('textarea', '* %s' % name, {'name':'hatena_entry'})
    html.writeOpenTag('div')
    html.writeOpenTag('input', {'type':'submit',
                                'value':'Accept'})
    html.writeCloseTag('div')
    html.writeCloseTag('form')

    return html.rendering()

@app.route("/edit_entry/<entry_id>")
def edit_entry(entry_id):
    html    = hatena_syntax.HtmlCanvas()
    context = _createContext('edit_entry')
    entry   = context.getEntry(entry_id)

    # HTMLヘッダのレンダリング
    _renderingHtmlHeader(html)
    html.writeTag('h1', 'エントリの編集')
    html.writeOpenTag('p')
    html.writeTag('a', '戻る', {'href': url_for('entry_page', id_or_name=entry_id)})
    html.writeCloseTag('p')

    # Entry edit form
    html.writeOpenTag('form', {'method':'post',
                               'action': url_for('save_entry', entry_id=entry_id)})

    html.writeTag('textarea', entry.read(), {'name':'hatena_entry'})

    html.writeOpenTag('div')
    html.writeTag('input', '', {'type':'submit',
                                'value':'Accept'})
    html.writeCloseTag('div')
    html.writeCloseTag('form')

    # Image upload form
    html.writeOpenTag('form', {'method':'post',
                               'enctype':"multipart/form-data",
                               'action': url_for('upload_image', entry_id=entry_id)})
    html.writeOpenTag('ul')
    for img in entry.getImageIdList():
        html.writeTag('li', img)
    html.writeOpenTag('li')
    html.writeTag('input', '', {'type':'file',
                                'accept':'image/*',
                                'name':'image'})
    html.writeTag('input', '', {'type':'submit',
                                'value':'upload'})
    html.writeCloseTag('li')
    html.writeCloseTag('ul')
    html.writeCloseTag('form')

    return html.rendering()

@app.route("/save_entry/<entry_id>", methods=['POST'])
def save_entry(entry_id):
    context = _createContext('save_entry')
    entry   = context.getEntry(entry_id)
    entry.write(conv_encoding(request.form['hatena_entry']))

    # hack! 本当は一度セーブ前にcompleteするのがよいですが、
    # renderer の同定とかがファイルを開く処理になっているのでめんどいので。
    if entry.getRendererId() == None:
        completer = PageCompleter()
        completer.complete(entry)

    # レンダリング
    html = hatena_syntax.HtmlCanvas()
    _renderingHtmlHeader(html)
    _renderingNaviBar(html, entry_id)

    html.writeTag('p', '以下のファイルを作成しました。')
    renderer = getRenderer(context, entry)
    renderer.renderViewPage(html, entry)

    return html.rendering()

@app.route('/image/<entry_id>/<img_id>')
def image(entry_id, img_id):
    context = _createContext('entry')
    entry   = context.getEntry(entry_id)

    try:
        if img_id in entry.getImageIdList():
            return Response(entry.loadImage(img_id),
                            content_type=_getImageContentType(img_id))
        else: # old stype path (global image path)
            path = os.path.join(context.contents_dir, img_id)
            rf = open(img_path,'rb')
            return Response(rf.read(),
                            content_type=_getImageContentType(img_id))
    except IOError:
        abort(404)

@app.route('/upload_image/<entry_id>', methods=['POST'])
def upload_image(entry_id):
    context = _createContext('save_entry')
    entry   = context.getEntry(entry_id)

    f = request.files['image']
    if not f.filename == '':
        entry.saveImage(f)

    return redirect(url_for('edit_entry', entry_id=entry_id))

@app.route('/stylesheet.css')
def stylesheet():
    return open(app.config["STYLE_SHEET"]).read()

