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

#------------------------------------------------------------
# API
#------------------------------------------------------------

@app.route('/api/v1/entries', methods=['GET'])
def get_entries():
    context = createContext('entry')
    return json.dumps( [ {'entry': {'id'   : entry.entry_id,
                                    'title': entry.getTitle(),
                                    'categories': entry.getCategories()}}
                          for entry
                          in context.getEntryList() ]
                       )

@app.route('/api/v1/entry/<id_or_name>', methods=['GET'])
def get_entry(id_or_name):
    print id_or_name
    context  = createContext('entry')
    if not context.existEntry(id_or_name): abort(404)
    entry    = context.getEntry(id_or_name)

    # レンダリング
    return json.dumps(
        {'entry' : {'id'   : entry.entry_id,
                    'title': entry.getTitle(),
                    'categories': entry.getCategories(),
                    'html': _renderingEntry(context, entry) }}
    )

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
    return json.dumps(lst)

@app.route('/api/v1/category/<category_name>', methods=['GET'])
def get_category(category_name):
    context = createContext('entry')
    catmap  = _getCatMap(context)
    return json.dumps(
        {'category': {'name'   : category_name,
                      'entries': [ {'entry': {'id': e.entry_id, 'title': e.getTitle()}}
                                   for e in catmap[category_name] ] }}
    )

@app.route('/api/v1/preview', methods=['POST'])
def api_preview():
    json_obj = request.json
    context  = createContext('entry')
    entry    = VirtualEntry(context,
                            json_obj['id'], '', ez_decode(json_obj['source']))
                       
    return json.dumps(
        {'entry' : {'id'   : entry.entry_id,
                    'title': entry.getTitle(),
                    'categories': entry.getCategories(),
                    'html': _renderingEntry(context, entry) }}
    )

