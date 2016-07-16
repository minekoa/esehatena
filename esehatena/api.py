#-*- coding:utf-8 -*-

from viewmodels import createContext, getRenderer
from models import EHEntry
from hatena_syntax import HtmlCanvas
from my_enc_tool import *
import hatena_syntax

from flask import request, abort, Response
import re
import json

from . import app

#------------------------------------------------------------
# Tools
#------------------------------------------------------------

def _renderingEntry(context, entry):
    html     = HtmlCanvas()
    renderer = getRenderer(context, entry)
    renderer.renderViewPage(html, entry)
    return html.rendering()

def _getCatMap(context):
    catmap = {}
    for entry in sorted(context.getEntryList(), key=lambda entry: entry.entry_id, reverse=True):
        cats  = entry.getCategories()
        for cat in cats:
            if not cat in catmap: catmap[cat] = []
            catmap[cat].append(entry)
    return catmap


class VirtualEntry(EHEntry):
    def __init__(self, context, entry_id, entry_name, source):
        EHEntry.__init__(self, context, entry_id, entry_name)
        self.source = ez_decode(source)

    #----------------------------------------
    # ファイル操作
    #----------------------------------------
    def read(self):              return conv_encoding(self.source)
    def readlines(self):         return self.source.split(u'\n')
    def write(self, text):       self.source = ez_decode(text)
    def writelines(self, lines): u'\n'.join(ez_decode(l) for l in lines)
    def createScanner(self):
        scanner = hatena_syntax.TextScanner()
        scanner.setSource(self.source)
        return scanner

    #----------------------------------------
    # メタ情報
    #----------------------------------------
    def getImageIdList(self):
        return []

    def getRendererId(self):
        '''
        自身をレンダリングして欲しいモジュールの entry_idを取得する
        '''
        first_line = self._loadShebang()

        matobj = re.match(r"#!rendering:(.*)", first_line)
        if matobj != None:
            renderer_id = matobj.group(1).strip()
            if renderer_id == 'self':
                renderer_id = self.entry_id
            return renderer_id
        else:
            return None

    def _loadShebang(self):
        for line in self.readlines():
            if len(line.strip()) == 0:
                continue
            elif line[0] == '#':
                if re.match(r"#!", line) != None:
                    return line
            else:
                return ''
        else:
            return ''

    #----------------------------------------
    # イメージ操作
    #----------------------------------------
    def saveImage(self, uploadFile): pass
    def loadImage(self, img_id):     pass

    #----------------------------------------
    # private (このクラスの中以外で使っちゃダメよ)
    #----------------------------------------
    def _getCatsAndTitle(self):
        headline = self.source[0]
        if len(headline) == 0:   headline = '(無題)'
        elif headline[0] == '*': headline = headline[1:]
        return self._parseTitle(headline)

def _entry2data(entry, fields, context):
    entry_data = {}
    if 'id'         in fields: entry_data['id']         = entry.entry_id
    if 'title'      in fields: entry_data['title']      = entry.getTitle()
    if 'categories' in fields: entry_data['categories'] = entry.getCategories()
    if 'html'       in fields: entry_data['html']       = _renderingEntry(context, entry)
    if 'source'     in fields: entry_data['source']     = entry.read()
    return entry_data
#------------------------------------------------------------
# API
#------------------------------------------------------------

@app.route('/api/v1/entries', methods=['GET'])
def get_entries():
    fields  = request.args.get('fields').split(',')
    context = createContext('entry')
    js = json.dumps( [ {'entry': _entry2data(entry, fields, context)}
                       for entry
                       in context.getEntryList() ] )
    return Response(js, status=200, mimetype='application/json')


@app.route('/api/v1/entries/<id_or_name>', methods=['GET'])
def get_entry(id_or_name):
    fields = request.args.get('fields').split(',')
    context  = createContext('entry')
    if not context.existEntry(id_or_name): abort(404)
    entry    = context.getEntry(id_or_name)

    js = json.dumps({'entry' : _entry2data(entry, fields, context)})
    return Response(js, status=200, mimetype='application/json')

@app.route('/api/v1/categories', methods=['GET'])
def get_categories():
    context = createContext('entry')
    catmap  = _getCatMap(context)

    lst = []
    for cat, entries in sorted(catmap.items(), key= lambda x : x[0].upper()):
        lst.append(
            {'category': {'name'   : cat,
                          'entries': [ {'entry': {'id': e.entry_id, 'title': e.getTitle()}}
                                       for e in entries ] }} )
    return Response(json.dumps(lst), status=200, mimetype='application/json')

@app.route('/api/v1/categories/<category_name>', methods=['GET'])
def get_category(category_name):
    context = createContext('entry')
    catmap  = _getCatMap(context)
    js = json.dumps(
        {'category': {'name'   : category_name,
                      'entries': [ {'entry': {'id': e.entry_id, 'title': e.getTitle()}}
                                   for e in catmap[category_name] ] }}
    )
    return Response(js, status=200, mimetype='application/json')

@app.route('/api/v1/preview', methods=['POST'])
def api_preview():
    json_obj = request.json
    context  = createContext('entry')
    entry    = VirtualEntry(context,
                            json_obj['id'], '', ez_decode(json_obj['source']))
                       
    js = json.dumps(
        {'entry' : {'id'   : entry.entry_id,
                    'title': entry.getTitle(),
                    'categories': entry.getCategories(),
                    'html': _renderingEntry(context, entry) }}
    )
    return Response(js, status=200, mimetype='application/json')

