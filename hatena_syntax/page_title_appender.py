#-*- coding: utf-8 -*-

from HTMLParser import HTMLParser
import urllib
import chardet
import re


#------------------------------------------------------------
# Web からタイトル取得

class HtmlTitleGetter(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.is_in_title_element = False
        self.title = None

    def handle_starttag(self, tag, attrs):
        if tag == 'title': self.is_in_title_element = True

    def handle_data(self, data):
        if not self.is_in_title_element: return
        self.title = data
        self.is_in_title_element = False

def getPageTitle(url):
    title_getter= HtmlTitleGetter()

    try:
        connection = urllib.urlopen(url)
        encoding   = connection.headers.getparam('charset')
        page = connection.read().decode(encoding) if encoding !=None else connection.read()

        title_getter.feed(page)
        title_getter.close()
    except IOError:
        pass

    return title_getter.title

#------------------------------------------------------------
# タイトル未取得の Link にタイトルをセット

class PageTitleAppender(object):
    def __init__(self):
        self.link_list =[]

    def visit_node(self, node):
        for child in node.children: child.accept(self)
    def visit_entry(self, node):
        for child in node.children: child.accept(self)
    def visit_entry_header(self, node): pass
    def visit_header(self, node): pass

    def visit_supre_pre(self, supre_pre): pass
    def visit_paragraph(self, paragraph):
        for line in paragraph.lines: line.accept(self)

    def visit_block_quote(self, block_quote):
        for line in block_quote.content: line.accept(self)
        if block_quote.link != None:     block_quote.link.accept(self)

    def visit_table(self, table): pass
    def visit_data_list(self, a_datalist): pass

    def visit_list(self, a_list):        self._visit_list_proc(a_list)
    def visit_number_list(self, a_list): self._visit_list_proc(a_list)
    def _visit_list_proc(self, a_list):
        for lv, txt in a_list.lists: txt.accept(self)

    # inline element ------------------------
    def visit_plane_text(self, text): pass
    def visit_footnote(self, footnote): pass
    def vislt_image(self, img): pass
    def visit_wiki_name(self, wiki): pass

    def visit_html_link(self, html_link):
        for i in range(0, len(html_link.options)):
            matobj = re.match(r"title(=.*)?", html_link.options[i])
            if matobj == None or  matobj.group(1) != None: continue

            title = getPageTitle(html_link.getUrl())
            if title == None or title.strip() == '':
                html_link.options[i] = u'title=(タイトルが取得できませんでした) %s' % html_link.getUrl()
            else:
                html_link.options[i] = 'title=%s' % title
                self.link_list.append(html_link)
