#-*- coding: shift_jis -*-
import xml.sax.saxutils
import re

def _conv_encoding(data, to_enc="utf_8"):
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

#============================================================
# Html Rendering
#============================================================

class HtmlCanvasBase(object):
    '''Base Class for HtmlHeaderCanvas and HtmlCanvas(=body+header)'''
    def __init__(self):
        self.buf = ''

    def _write(self, text):
        self.buf += _conv_encoding(text)

    def _html_escape(self, aStr):
        return xml.sax.saxutils.escape(aStr)

    def _attr_escape(self, aStr):
        return xml.sax.saxutils.quoteattr(aStr)

    def writeOpenTag(self, tag_name, attr_list={}):
        self._write('<%s' % tag_name)
        for key, value in attr_list.items():
            self._write(' %s=%s' % (key, self._attr_escape(value)))
        self._write('>')

    def writeCloseTag(self, tag_name):
        self._write('</%s>' % tag_name)

    def writeText(self, text):
        self._write(self._html_escape(text))

    def writeRawText(self, text):
        self._write(text)

    def writeTag(self, tag_name, text, attr_list={}):
        self.writeOpenTag(tag_name, attr_list)
        self.writeText(text)
        self.writeCloseTag(tag_name)

class HtmlHeaderCanvas(HtmlCanvasBase):
    """todo: <head> 's attribute writer"""
    pass

class HtmlCanvas(HtmlCanvasBase):
    """todo: <body> 's attribute writer"""
    def __init__(self):
        HtmlCanvasBase.__init__(self)    # html body
        self.header = HtmlHeaderCanvas() # html header

    def rendering(self):
        return ''.join(['<html>',
                        '<head>', self.header.buf, '</head>'
                        '<body>', self.buf, '</body>'
                        '</html>'])

class HtmlRenderingVisitor(object):
    def __init__(self, canvas, url_mapper):
        self.canvas     = canvas
        self.url_mapper = url_mapper

        self.entry_id = ''
        self.footnote_cache = []


    def visit_node(self, node):
        '''未知の種類のノード'''
        for child in node.children:
            child.accept(self)
    
    def visit_entry(self, entry):
        for child in entry.children:
            child.accept(self)

        # 最下部に脚注を出す
        for i in range(0, len(self.footnote_cache)):
            footnote = self.footnote_cache[i]
            self.canvas.writeOpenTag('div')
            self.canvas.writeTag('a', '*%d' % (i+1),
                                 {'id'  : '%sf%d'   % (self.entry_id, i+1),
                                  'href': '#%sfn%d' % (self.entry_id, i+1)})
            self.canvas.writeText(footnote.content)
            self.canvas.writeCloseTag('div')
        self.footnote_cache = []

    def visit_entry_header(self, entry_header):
        self.canvas.writeOpenTag('h1')
        if entry_header.category != '':
            self.canvas.writeText('[')
            self.canvas.writeOpenTag('a', {'href':self.url_mapper.getCategoryUrl(entry_header.category)})
            self.canvas.writeText(entry_header.category)
            self.canvas.writeCloseTag('a')
            self.canvas.writeText(']')
        self.canvas.writeText(entry_header.text)
        self.canvas.writeCloseTag('h1')

    def visit_header(self, header):
        self.canvas.writeOpenTag('h%d' % header.level)
        self.canvas.writeText(header.text)
        self.canvas.writeCloseTag('h%d' % header.level)

    def visit_paragraph(self, paragraph):
        self.canvas.writeOpenTag('p')

        for line in paragraph.lines:
            line.accept(self)
        self.canvas.writeCloseTag('p')

    def visit_supre_pre(self, supre_pre):
        self.canvas.writeOpenTag('pre', {'class':'code'})
        for line in supre_pre.content:
            self.canvas.writeText(line)
        self.canvas.writeCloseTag('pre')

    def visit_block_quote(self, block_quote):
        attr = {}
        if block_quote.link != None:
            attr['cite'] = block_quote.link.children[0].getUrl()

        self.canvas.writeOpenTag('blockquote', attr)

        for line in block_quote.content:
            line.accept(self)

        if block_quote.link != None:
            self.canvas.writeOpenTag('div', {'class':'ehatena_quo_cite'})
            block_quote.link.accept(self)
            self.canvas.writeCloseTag('div')

        self.canvas.writeCloseTag('blockquote')

    def visit_table(self, table):
        '''note: th と td の見分けをここでやるのは本当は良くない
        (parse 時にcellの属性として設定するのが好ましい）
        '''
        self.canvas.writeOpenTag('table', {'border':'1'})

        for row in table.rows:
            self.canvas.writeOpenTag('tr')
            for cel in row:
                if 1 < len(cel) and cel[0] == '*':
                    self.canvas.writeOpenTag('th')
                    self.canvas.writeText(cel[1:])
                    self.canvas.writeCloseTag('th')
                else:
                    self.canvas.writeOpenTag('td')
                    self.canvas.writeText(cel)
                    self.canvas.writeCloseTag('td')
            self.canvas.writeCloseTag('tr')
        self.canvas.writeCloseTag('table')


    def visit_list(self, a_list):
        self._visit_list_proc('ul', a_list)

    def visit_number_list(self, a_list):
        self._visit_list_proc('ol', a_list)

    def _visit_list_proc(self, tag_name, a_list):
        self.canvas.writeOpenTag(tag_name)

        last_lv = -1

        for lv, txt in a_list.lists:
            if last_lv == -1: pass
            elif last_lv == lv:
                self.canvas.writeCloseTag('li')
            elif last_lv < lv:
                diff = lv - last_lv
                self.canvas.writeOpenTag(tag_name)
                for i in range(0, diff -1):
                    self.canvas.writeOpenTag('li')
                    self.canvas.writeOpenTag(tag_name)
            elif lv < last_lv:
                diff = last_lv - lv
                for i in range(0, diff):
                    self.canvas.writeCloseTag(tag_name)
                    self.canvas.writeCloseTag('li')

            self.canvas.writeOpenTag('li')
            txt.accept(self)
            last_lv = lv

        for i in range(0, last_lv -1):
            self.canvas.writeCloseTag(tag_name)
            self.canvas.writeCloseTag('li')

        self.canvas.writeCloseTag(tag_name)

        
    def visit_data_list(self, a_datalist):
        self.canvas.writeOpenTag('dl')
        for kind, content in a_datalist.contents:
            if kind == 'title':
                self.canvas.writeOpenTag('dt')
                self.canvas.writeText(content)
                self.canvas.writeCloseTag('dt')
            if kind == 'data':
                self.canvas.writeOpenTag('dd')
                self.canvas.writeText(content)
                self.canvas.writeCloseTag('dd')
        self.canvas.writeCloseTag('dl')

    #----------------------------------------
    # inline element

    def visit_plane_text(self, text):
        self.canvas.writeText(text.text)

    def visit_html_link(self, html_link):
        self.canvas.writeOpenTag('a',
                                 {'href': html_link.getUrl()})

        for opt in html_link.options:
            matobj = re.match(r"title(=.*)?", opt)
            if matobj == None: continue

            if matobj.group(1) != None:
                title = matobj.group(1).strip()[1:] # '=" の除去
                break
            else:
                title = '(タイトル未取得): %s' % html_link.getUrl()
                break
        else:
            title = html_link.getUrl()

        self.canvas.writeText(title)

        self.canvas.writeCloseTag('a')


    def visit_footnote(self, footnote):
        self.footnote_cache.append(footnote)
        fn_id = len(self.footnote_cache)
        self.canvas.writeTag('a', '*%d' % fn_id,
                             {'href' : '#%sf%d' % (self.entry_id, fn_id),
                              'id'   : '%sfn%d' % (self.entry_id, fn_id),
                              'title': footnote.content})

    def visit_image(self, img):
        url = self.url_mapper.getImageUrl(img.img_id)
        self.canvas.writeOpenTag('img',
                                 {'src':url})

    def visit_wiki_name(self, wiki):
        url = self.url_mapper.getEntryPageUrl(wiki.wiki_name)
        self.canvas.writeTag('a', wiki.wiki_name,
                             {'href': url})


