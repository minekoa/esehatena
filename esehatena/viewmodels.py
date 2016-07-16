#-*- coding:utf-8 -*-

from flask import url_for, request
from models import EHContext, EHEntry, WorldDictionary, HatenaRenderer, loadRendererModule

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
    '''Renderer に渡すための引数のようなもの.多分だれも使っていない'''

    def __init__(self, page_func, request):
        assert( page_func in ["entry", "edit_entry", "save_entry"] )
        self.page_func    = page_func
        self.request      = request       # flask の requestオブジェクト

#--------------------------------------------------------------------------------
#　Model Factories
#--------------------------------------------------------------------------------

def createContext(page_func):
    url_mapper     = UrlMapper()
    world_dict     = WorldDictionary(app.config["WORLD_DICT"])
    rendering_opts = RenderingOptions(page_func, request)

    context = EHContext(app.config["CONTENTS_DIR"], world_dict,
                        url_mapper, rendering_opts)
    return context

def getRenderer(context, entry):
    assert(context != None)
    assert(entry   != None)

    # モジュールのロード
    renderer_id = entry.getRendererId()
    if renderer_id != None:
        mod = loadRendererModule( context.getEntry(renderer_id) )
    else:
        mod = None

    # レンダラーの生成
    if mod != None: #id is None or module load failure.
        return mod.createRenderer(context)
    else:
        return HatenaRenderer(context) #(default)

