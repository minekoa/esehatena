#-*- coding: shift_jis -*-
import re

#================================================
# Block Element Node
#================================================

class HatenaNode(object):
    '''abstract'''
    def __init__(self):
        self.parent   = None
        self.children = []

    def append(self, child):
        child.parent = self
        self.children.append(child)

    def accept(self, visitor):
        visitor.visit_node(self)

class EntryNode(HatenaNode):
    def __init__(self):
        HatenaNode.__init__(self)

    def accept(self, visitor):
        visitor.visit_entry(self)


class EntryHeaderNode(HatenaNode):
    def __init__(self, category, text):
        self.category = category
        self.text     = text

    def accept(self, visitor):
        visitor.visit_entry_header(self)


class HeaderNode(HatenaNode):
    def __init__(self, level, text):
        self.level    = level #int
        self.text     = text

    def accept(self, visitor):
        visitor.visit_header(self)


class ParagraphNode(HatenaNode):
    def __init__(self):
        self.lines = []

    def append(self, line):
        self.lines.append(line)

    def accept(self, visitor):
        visitor.visit_paragraph(self)


class SuperPreNode(HatenaNode):
    def __init__(self, lang):
        self.lang    = lang
        self.content = []

    def append(self, line):
        self.content.append(line)

    def accept(self, visitor):
        visitor.visit_supre_pre(self)


class BlockQuoteNode(HatenaNode):
    def __init__(self, link):
        self.link    = link
        self.content = []

    def append(self, line):
        self.content.append(line)

    def accept(self, visitor):
        visitor.visit_block_quote(self)


class TableNode(HatenaNode):
    def __init__(self):
        self.rows = []

    def append(self, cells):
        self.rows.append(cells)

    def accept(self, visitor):
        visitor.visit_table(self)


class ListNode(HatenaNode):
    def __init__(self):
        self.lists = []

    def append(self, level, content):
        self.lists.append((level, content))

    def accept(self, visitor):
        visitor.visit_list(self)


class NumberListNode(HatenaNode):
    def __init__(self):
        self.lists = []

    def append(self, level, content):
        self.lists.append((level, content))

    def accept(self, visitor):
        visitor.visit_number_list(self)


class LineNode(HatenaNode):
    def isEmpty(self):
        return len(self.children) == 0


class DataListNode(HatenaNode):
    def __init__(self):
        self.contents = []

    def addTitle(self, title):
        self.contents.append( ("title", title) )

    def addData(self, data):
        self.contents.append( ("data", data) )

    def accept(self, visitor):
        visitor.visit_data_list(self)


#------------------------------------------------------------
# Inline Element Node
#------------------------------------------------------------

class HatenaInlineNode(object):
    '''abstract'''
    pass

class PlainTextINode(HatenaInlineNode):
    def __init__(self, text):
        self.text = text

    def accept(self, visitor):
        visitor.visit_plane_text(self)

class HtmlLinkINode(HatenaInlineNode):
    def __init__(self, protocol, url_body, options):
        self.protocol = protocol
        self.url_body = url_body
        self.options  = options

    def getUrl(self):
        return '%s%s' % (self.protocol, self.url_body)

    def getTitleOption(self):
        for opt in self.options:
            if re.match(r"title(=.*)?", opt): return opt
        else:
            return ''

    def asString(self):
        optstr = ':'.join(self.options)
        return self.getUrl() + ':' + optstr if optstr != '' else self.getUrl()

    def accept(self, visitor):
        visitor.visit_html_link(self)

class FootnoteINode(HatenaInlineNode):
    def __init__(self, content):
        self.content = content

    def accept(self, visitor):
        visitor.visit_footnote(self)

class ImageINode(HatenaInlineNode):
    def __init__(self, img_id):
        self.img_id = img_id

    def accept(self, visitor):
        visitor.visit_image(self)

class WikiNameINode(HatenaInlineNode):
    def __init__(self, wiki_name):
        self.wiki_name = wiki_name

    def accept(self, visitor):
        visitor.visit_wiki_name(self)

