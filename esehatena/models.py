#-*- coding:utf-8 -*-

from my_enc_tool import *
import hatena_syntax

import os
import os.path
import datetime
import re
import sys
import codecs

from werkzeug import secure_filename

#------------------------------------------------------------
# Constants
#------------------------------------------------------------

entry_id_pattern = re.compile(r"[0-9]{8}_[0-9]{6}")

#------------------------------------------------------------
# Tools
#------------------------------------------------------------

def _loadShebang(filepath):
    with open(filepath, 'r') as f:
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

#------------------------------------------------------------
# Context and Entreis 
#------------------------------------------------------------

class EHContext(object):
    '''サーバサイドレンダラーに渡されるコンテキスト'''
    def __init__(self, contents_dir, world_dict, url_mapper, rendering_opts):
        self.contents_dir   = contents_dir  # コンテンツファイルのパス
        self.world_dict     = world_dict    # 世界辞書
        self.url_mapper     = url_mapper    # url_mapper
        self.rendering_opts = rendering_opts # 描画用オプション

    def getEntry(self, entry_id_or_name):
        aId   = self._asEntryId(entry_id_or_name)
        aName = entry_id_or_name if entry_id_or_name == aId else ''
        return EHEntry(self, aId, aName)

    def getEntryList(self):
        files = os.listdir(self.contents_dir)
        files.sort()
        files.reverse()
        selected_files = [fpath for fpath in files if re.match(r"^[0-9]+_[0-9]+$",fpath) != None]
        return [EHEntry(self, entry_id, '') for entry_id in selected_files] 

    def existEntry(self, id_or_name):
        eid = self._asEntryId(id_or_name)
        fpath = os.path.join(self.contents_dir, eid)
        return os.path.exists(fpath)

    def createNewEntryId(self):
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S") 

    #----------------------------------------
    # Utilities
    #----------------------------------------
    def _asEntryId(self, entry_id_or_name):
        '''
        EntryID と Name を扱うツール
          world_dict に依存するので、共通のツール関数ではなく
          このクラス内に置かれる
        注意!: (というかTODO)
            name でこの関数を呼び出すと勝手にworlddictに登録したうえでentry_idを返す。
        '''

        if entry_id_pattern.match(entry_id_or_name) != None:
            return entry_id_or_name
        try:    
            name     = conv_encoding(entry_id_or_name)
            return self.world_dict[name]
        except KeyError:
            name     = conv_encoding(entry_id_or_name)
            entry_id = self.createNewEntryId()

            self.world_dict[name] = entry_id
            self.world_dict.save()   # Todo: 並列性を考える (Python の GILを当てにして良い？ --> Flaskの実装次第)
            return entry_id

class EHEntry(object):
    '''エントリーにアクセスするためのオブジェクト'''

    def __init__(self, context, entry_id, entry_name):
        self.context    = context
        self.entry_id   = entry_id
        self.entry_name = entry_name

    def _getFilePath(self):
        return os.path.join(self.context.contents_dir, self.entry_id)

    def _getDirPath(self):
        return os.path.join(self.context.contents_dir, self.entry_id+'d')

    #----------------------------------------
    # ファイル操作
    #----------------------------------------
    def read(self):
        '''コンテンツの中身を読み込む'''
        with codecs.open(self._getFilePath(), 'r', 'utf-8') as rf:
            return rf.read()

    def readlines(self):
        with codecs.open(self._getFilePath(), 'r', 'utf-8') as rf:
            return rf.readlines()

    def write(self, text):
        with codecs.open(self._getFilePath(),'w', 'utf-8') as wf:
            wf.write(ez_decode(text))

    def writelines(self, lines):
        with codecs.open(self._getFilePath(), 'w', 'utf-8') as wf:
            for line in lines:
                wf.write(line)

    #----------------------------------------
    # メタ情報
    #----------------------------------------
    def getTitle(self):
        return self._getCatsAndTitle()[1]

    def getCategories(self):
        return self._getCatsAndTitle()[0]

    def getImageIdList(self):
        assert(self.entry_id != None)
        dpath = self._getDirPath()
        if not os.path.exists(dpath): return []
        return [img_name for img_name in os.listdir(dpath) if os.path.splitext(img_name)[1].lower() in ['.png', '.jpg', '.jpeg', '.gif']]

    def getRendererId(self):
        '''
        自身をレンダリングして欲しいモジュールの entry_idを取得する
        '''
        first_line = _loadShebang(self._getFilePath())

        matobj = re.match(r"#!rendering:(.*)", first_line)
        if matobj != None:
            renderer_id = matobj.group(1).strip()
            if renderer_id == 'self':
                renderer_id = self.entry_id
            return renderer_id
        else:
            return None

    #----------------------------------------
    # レンダリング用
    #----------------------------------------
    def getUrlMapper(self):
        return self.context.url_mapper.clone(self.entry_id)

    def getViewPageUrl(self):
        return self.context.url_mapper.getEntryPageUrl(self.entry_id)

    def getEditPageUrl(self):
        return self.context.url_mapper.getEditEntryUrl(self.entry_id)

    #----------------------------------------
    # イメージ操作
    #----------------------------------------
    def saveImage(self, uploadFile):
        dirPath = self._getDirPath()
        if not os.path.exists(dirPath):
            os.mkdir(dirPath)
        uploadFile.save(os.path.join(dirPath, secure_filename(uploadFile.filename)))

    def loadImage(self, img_id):
        path = os.path.join(self._getDirPath(), img_id)
        with open(path, 'rb') as f:
            return f.read()

    #----------------------------------------
    # private (このクラスの中以外で使っちゃダメよ)
    #----------------------------------------
    def _getCatsAndTitle(self):
        assert(self.entry_id != None)
        with open(self._getFilePath(),'r') as f:
            headline = f.readline().strip()
            if len(headline) == 0:   headline = '(無題)'
            elif headline[0] == '*': headline = headline[1:]
            return self._parseTitle(headline)

    def _parseTitle(self, title_line):
        cats = []
        in_cat = False
        tmp  = ''

        for c in title_line:
            if not in_cat and c == '[' : in_cat = True
            elif in_cat and c == ']':
                cats.append(tmp.strip())
                in_cat = False
                tmp = ''
            else: tmp += c
        return (cats, tmp.strip()) # ([cat:string], title:string)

#------------------------------------------------------------
# World Dictionary
#------------------------------------------------------------

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
        f = open(self.dict_file_path, 'w')
        for key, value in self.dict_.iteritems():
            f.write('%s:%s\n' % (key,value))
        f.close

    def __getitem__(self, key):
        return self.dict_[key]

    def __setitem__(self, key, value):
        self.dict_[key] = value

#------------------------------------------------------------
# Renderer Module Loader (for Renderer Entry)
#------------------------------------------------------------

def loadRendererModule(module_entry):
    try:
        with open(module_entry._getFilePath(), 'r') as module_file:
            import imp
            mod = imp.load_module(module_entry.entry_id,
                                  module_file,
                                  module_entry._getFilePath(),
                                  ('', 'r', imp.PY_SOURCE)) #suffix, file_open_mode, type
            return mod

    except ImportError:
        return None

class HatenaRenderer(object):
    def __init__(self, context):
        self.context = context

    def renderViewPage(self, canvas, entry):
        # 1. parsing
        scanner = hatena_syntax.FileScanner()
        scanner.openFile(entry._getFilePath())
        parser  = hatena_syntax.HatenaParser()
        hatena_document = parser.parse(scanner)

        # 2. wget Link URL
        title_appender = hatena_syntax.PageTitleAppender()
        hatena_document.accept(title_appender)

        # 3. rendering
        html_renderer = hatena_syntax.HtmlRenderingVisitor(canvas, entry.getUrlMapper())
        hatena_document.accept(html_renderer)

