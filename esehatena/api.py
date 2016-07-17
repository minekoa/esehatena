#-*- coding:utf-8 -*-

from viewmodels import createContext, getRenderer
from models import VirtualEntry
from hatena_syntax import HtmlCanvas
from my_enc_tool import *
from page_completer import PageCompleter
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

def _entry2data(entry, fields, context):
    entry_data = {}
    if 'id'         in fields: entry_data['id']         = entry.entry_id
    if 'title'      in fields: entry_data['title']      = entry.getTitle()
    if 'categories' in fields: entry_data['categories'] = entry.getCategories()
    if 'images'     in fields: entry_data['images']     = entry.getImageIdList()
    if 'html'       in fields: entry_data['html']       = _renderingEntry(context, entry)
    if 'source'     in fields: entry_data['source']     = entry.read()
    return entry_data
#------------------------------------------------------------
# API
#------------------------------------------------------------

@app.route('/api/v1/entries', methods=['GET'])
def get_entries():
    fields  = request.args.get('fields').split(',') if request.args.get('fields') != None else []
    context = createContext('entry')
    js = json.dumps( [ {'entry': _entry2data(entry, fields, context)}
                       for entry
                       in context.getEntryList() ] )
    return Response(js, status=200, mimetype='application/json')


@app.route('/api/v1/entries/<id_or_name>', methods=['GET'])
def get_entry(id_or_name):
    fields  = request.args.get('fields').split(',') if request.args.get('fields') != None else []
    context  = createContext('entry')
    if not context.existEntry(id_or_name): abort(404)
    entry    = context.getEntry(id_or_name)

    js = json.dumps({'entry' : _entry2data(entry, fields, context)})
    return Response(js, status=200, mimetype='application/json')

@app.route('/api/v1/entries/<id_or_name>', methods=['PUT'])
def update_entry(id_or_name):
    json_obj = request.json
    context  = createContext('save_entry')
    entry    = context.getEntry(id_or_name)
    entry.write(conv_encoding(json_obj['entry']['source']))

    if entry.getRendererId() == None:
        completer = PageCompleter()
        completer.complete(entry)

    # レスポンスを用意
    fields = request.args.get('fields').split(',') if request.args.get('fields') != None else []

    js = json.dumps({'entry' : _entry2data(entry, fields, context)})
    return Response(js, status=200, mimetype='application/json')

@app.route('/api/v1/entries', methods=['POST'])
def create_entry():
    json_obj = request.json
    context  = createContext('save_entry')
    entry    = context.createEntry()
    entry.write(conv_encoding(json_obj['entry']['source']))

    if entry.getRendererId() == None:
        completer = PageCompleter()
        completer.complete(entry)

    # レスポンスを用意
    fields = request.args.get('fields').split(',') if request.args.get('fields') != None else []

    js = json.dumps({'entry' : _entry2data(entry, fields, context)})
    return Response(js, status=201, mimetype='application/json')



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

