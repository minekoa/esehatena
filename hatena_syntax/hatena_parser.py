#-*- coding: shift_jis -*-
import re
from hatena_document import *
from hatena_inline_parser import *

#============================================================
# Facade (front-end object)
#============================================================

class TextScanner(object):
    def setSource(self, a_str):
        self.source = (i for i in a_str.splitlines())
        self.line = self.source.next()
        print self.source

    def advanceLine(self):
        self.line = self.source.next()

    def getLine(self):
        return self.line + '\n'


class FileScanner(object):
    def openFile(self, path):
        f = open(path, 'r')
        self.lines = (i for i in f.readlines())
        self.line  = None  #�x�����[�h (try��O�� next �� StopIteration ���Ă��܂����Ƃ�h����)

    def advanceLine(self):
        self.line = self.lines.next()

    def getLine(self):
        if self.line == None: self.advanceLine()
        return self.line


class HatenaParser(object):

    def parse(self, scanner):
        parsers = []
        parsers.append(EntrySyntax())
        parsers.append(AnonymousEntrySyntax())

        for parser in parsers:
            parser.setScanner(scanner)

        root_node = HatenaNode()
        while True:
            try:
                for parser in parsers:
                    tmp = parser.parse(root_node)
                    if tmp != None: break
                else:
                    raise ValueError(scanner.getLine())

            except StopIteration:
                break
        return root_node


#================================================
# Syntax Tree (= Parser parts)
#================================================

class HatenaSyntax(object):
    '''abstract'''
    def ___init__(self):
        pass

    def setScanner(self, scanner):
        self.scanner = scanner

class EntrySyntax(HatenaSyntax):
    '''
    ���o���s�� �͂Ăȃ_�C�����L�@

    [EntryHeader] [EntryContent]

    @note:
    > *[�J�e�S��] ���o���s
    > �E�E�E�{��
    
    �Ƃ����\���̂͂Ăȃ_�C�A���[�̃G���g���\�������҂���B
    '''
    def __init__(self):
        HatenaSyntax.__init__(self)
        self._elaborate()

    def _elaborate(self):
        self.header_syntax  = EntryHeaderSyntax()
        self.content_syntax = EntryContentSyntax()

    def setScanner(self, scanner):
        self.scanner = scanner
        self.header_syntax.setScanner(scanner)
        self.content_syntax.setScanner(scanner)

    def _isEntryHeader(self, line):
        return self.header_syntax.isMatch(line)

    def parse(self, parent_node):
        # �ŏ��ɁA���҂���\���i�����o���s + �{��) ���ǂ����𔻒肷��B
        # (�ʖڂ��������ʂ����̕��@�̃X�L���i�ɐ؂�ւ��邽��)
        line = self.scanner.getLine()
        if not self._isEntryHeader(line): return None

        # ��͊J�n
        tmp = EntryNode()
        parent_node.append(tmp)
        self.header_syntax.parse(tmp)  # ���o���s���
        self.content_syntax.parse(tmp) # �{�����
        return parent_node

class AnonymousEntrySyntax(HatenaSyntax):
    '''
    ���o���s�Ȃ��͂Ăȃ_�C�����[�L�@

     [EntryContent]
    '''

    def __init__(self):
        HatenaSyntax.__init__(self)
        self._elaborate()

    def _elaborate(self):
        self.header_syntax  = EntryHeaderSyntax()
        self.content_syntax = EntryContentSyntax()

    def setScanner(self, scanner):
        self.scanner = scanner
        self.header_syntax.setScanner(scanner)
        self.content_syntax.setScanner(scanner)

    def _isEntryHeader(self, line):
        return self.header_syntax.isMatch(line)

    def parse(self, parent_node):
        line = self.scanner.getLine()
        if self._isEntryHeader(line): return None

        tmp = EntryNode()
        parent_node.append(tmp)
        self.content_syntax.parse(tmp)
        return parent_node



class EntryHeaderSyntax(HatenaSyntax):
    def __init__(self):
        HatenaSyntax.__init__(self)
        self.ptn = re.compile(r"(\*+)(([ ]*\[[^\]]+\])*)(.*)$")        

    def isMatch(self, line):
        matobj = self.ptn.match(line)
        if matobj == None:
            return False
        elif len(matobj.group(1)) == 1:
            return True
        else:
            return False

    def parse(self, parent_node):
        line = self.scanner.getLine()

        matobj = self.ptn.match(line)
        if matobj == None: return None
        if len(matobj.group(1)) != 1: return None

        if matobj.group(2) == None: cats = []
        else                      : cats = self._make_cats_list(matobj.group(2))
        node = EntryHeaderNode(cats, matobj.group(4))

        parent_node.append(node)
        self.scanner.advanceLine()
        return parent_node

    def _make_cats_list(self, src):
        cats = []
        in_cat = False
        tmp  = ''

        print "CATSOURCE:" , src
        for c in src:
            if not in_cat and c == '[' : in_cat = True
            elif in_cat and c == ']':
                cats.append(tmp.strip())
                in_cat = False
                tmp = ''
            else: tmp += c
        return cats


class EntryContentSyntax(HatenaSyntax):
    '''
    �͂ĂȋL�@ �{����͊�
    '''
    def __init__(self):
        HatenaSyntax.__init__(self)
        self.inline_parser = InLineParser()

        self.header_syntax = EntryHeaderSyntax()
        self._elaborate()

    def _elaborate(self):
        self.syntaxes = []
        self.syntaxes.append(HeaderSyntax())
        self.syntaxes.append(SuprePreSyntax())
        self.syntaxes.append(BlockQuoteSyntax())
        self.syntaxes.append(TableSyntax())
        self.syntaxes.append(ListSyntax())
        self.syntaxes.append(NumberListSyntax())
#        self.syntaxes.append(DataListSyntax())

    def setScanner(self, scanner):
        self.scanner = scanner
        for syntax in self.syntaxes:
            syntax.setScanner(scanner)

    def _isEntryHeader(self, line):
        return self.header_syntax.isMatch(line)

    def parse(self, parent_node):
        paragraph = None

        while True:
            line = self.scanner.getLine()
            if self._isEntryHeader(line): return None

            # ���炩�̂͂ĂȋL�@���o
            for syntax in self.syntaxes:
                tmp = syntax.parse(parent_node)
                if tmp != None:
                    paragraph = None
                    break
            else: # ���̑��͒n�̕�����
                if len(line.strip()) == 0:
                    paragraph = None
                    self.scanner.advanceLine()
                    continue

                if paragraph == None:
                    paragraph = ParagraphNode()
                    parent_node.append(paragraph)
                paragraph.append(self.inline_parser.parse(line))
                self.scanner.advanceLine()

        return parent_node
        

class HeaderSyntax(HatenaSyntax):
    def __init__(self):
        HatenaSyntax.__init__(self)
        self.starter_ptn = re.compile(r"\*(\*+)(.*)$")

    def parse(self, parent_node):
        line = self.scanner.getLine()

        matobj = self.starter_ptn.match(line)
        if matobj == None: return None

        node = HeaderNode(len(matobj.group(1)) +1, # level (h2,3,4...)
                          matobj.group(2).strip()) # text
        parent_node.append(node)
        self.scanner.advanceLine()
        return parent_node

class SuprePreSyntax(HatenaSyntax):
    '''
    todo: ���ꕶ�@���̃V���^�b�N�X�n�C���C�g
    �v���O�C���@�\
    '''
    def __init__(self):
        HatenaSyntax.__init__(self)
        self.start_ptn = re.compile(r"^>\|([a-zA-Z0-9]+)?\|")
        self.end_ptn   = re.compile(r"^\|\|<")
        pass

    def parse(self, parent_node):
        line = self.scanner.getLine()

        # detect starting
        matobj = self.start_ptn.match(line) 
        if matobj == None: return None

        if matobj.group(1) != None: lang = matobj.group(1)
        else:                       lang = ''
        node = SuperPreNode(lang)
        parent_node.append(node)

        # contents puts
        while True:
            self.scanner.advanceLine()
            line = self.scanner.getLine()

            if self.end_ptn.match(line) != None:
                self.scanner.advanceLine()
                break

            node.append(line)

        return parent_node


class BlockQuoteSyntax(HatenaSyntax):
    '''
    BlockQuote�X�L���i�B

    @todo BlockQuote�̂Ƀl�X�g�ɑΉ����Ă��Ȃ��B
    �܂��AEntryContextSyntax �̓�d�����ɂȂ��Ă��܂��Ă��āA
    �R�[�h�I�ɔ������Ȃ��B
    EntryContentSyntax ���ċA����\�����]�܂�����    
    ���̍\���ł�Parser�������O���t�ɂȂ��Ă��܂��Ή��o���Ȃ��B
    '''
    def __init__(self):
        self.link_parser   = HtmlLinkParser()
        self.inline_parser = InLineParser()
        self._elaborate()

        self.start_ptn = re.compile(r"^>([^>]+)?>")
        self.end_ptn   = re.compile(r"^<<")

    def _elaborate(self):
        self.syntaxes = []
        self.syntaxes.append(HeaderSyntax())
        self.syntaxes.append(SuprePreSyntax())
        self.syntaxes.append(TableSyntax())
        self.syntaxes.append(ListSyntax())
        self.syntaxes.append(NumberListSyntax())

    def setScanner(self, scanner):
        self.scanner = scanner
        for syntax in self.syntaxes:
            syntax.setScanner(scanner)

    def _parseBqStart(self):
        line = self.scanner.getLine()

        matobj = self.start_ptn.match(line) 
        if matobj == None: return None

        if matobj.group(1) != None:
            link = self.link_parser.parse(matobj.group(1))
            if link.isEmpty(): return None
        else:
            link = None
        bq_node = BlockQuoteNode(link)

        self.scanner.advanceLine()
        return bq_node

    def parse(self, parent_node):
        # detect BQ start line
        bq_node = self._parseBqStart()
        if bq_node == None: return None
        parent_node.append(bq_node)

        # contents source collect
        lines = ''
        paragraph = None

        while True:
            line = self.scanner.getLine()

            # �I�������o
            if self.end_ptn.match(line) != None:
                self.scanner.advanceLine()
                break

            # ���炩�̂͂ĂȋL�@���o
            for syntax in self.syntaxes:
                tmp = syntax.parse(bq_node)
                if tmp != None:
                    paragraph = None
                    break

            else: # ���̑��͒n�̕�����
                if len(line.strip()) == 0:
                    paragraph = None
                    self.scanner.advanceLine()
                    continue

                if paragraph == None:
                    paragraph = ParagraphNode()
                    bq_node.append(paragraph)
                paragraph.append(self.inline_parser.parse(line))
                self.scanner.advanceLine()

        else:
            return None

        return parent_node


class TableSyntax(HatenaSyntax):

    def parse(self, parent_node):
        line = self.scanner.getLine()

        # detect starting
        if line[0] != '|' or  line.strip()[-1] != '|':
            return None

        node = TableNode()
        parent_node.append(node)

        # colelct rows
        while True:
            if line[0] != '|' or  line.strip()[-1] != '|':
                break

            cells = line.strip().split('|')[1:-1]
            node.append(cells)

            self.scanner.advanceLine()
            line = self.scanner.getLine()

        return parent_node


class ListSyntaxBase(HatenaSyntax):
    '''
    ���X�g�L�@ (- hogehoge) �� �ԍ����X�g�L�@ (+ hogehoge) �ɋ��ʂ�
    ���������肾�����N���X
    '''
    def __init__(self):
        self.inline_parser = InLineParser()

    def parse(self, parent_node):
        line = self.scanner.getLine()
        if self.ptn.match(line) == None:
            return None

        node = self.createNode()
        parent_node.append(node)

        while True:
            matobj = self.ptn.match(line)
            if matobj == None:
                break

            node.append(len(matobj.group(1)), #level
                        self.inline_parser.parse(matobj.group(2)))

            self.scanner.advanceLine()
            line = self.scanner.getLine()

        return parent_node

class ListSyntax(ListSyntaxBase):
    def __init__(self):
        ListSyntaxBase.__init__(self)
        self.ptn = re.compile(r"(\-+)(.*)")

    def createNode(self):
        return ListNode()

class NumberListSyntax(ListSyntaxBase):
    def __init__(self):
        ListSyntaxBase.__init__(self)
        self.ptn = re.compile(r"(\++)(.*)")

    def createNode(self):
        return NumberListNode()

class DataListSyntax(HatenaSyntax):
    def __init__(self):
        self.datatitle_ptn = re.compile(r"^:([^:]+):([^:]*)$")
        self.databody_ptn  = re.compile(r"^::([^:].*)")

    def _getParentDataListNode(self, parent_node):
        if is_instance(parent_node, DataListNode):
            return parent_node
        else:
            datalist_node = DataListNode()
            parrent_node.append(datalist_node)
            return datalist_node

    def parse(self, parent_node):
        line = self.scanner.getLine()

        # detect datalist-tiltle
        matobj = self.datatitle_ptn.match(line)
        if matobj != None:
            datalist_node = self._getParrentDataListNode(parent_node)
            datalist_node.addTitle(matobj.group(1))
            if matobj.group(2) != "":
                datalist_node.addData(matobj.group(2))

            return datalist_node

        # detect datalist-data
        matobj = self.databody_ptn.match(line)                
        if matobj != None:
            datalist_node = self._getParrentDataListNode(parent_node)
            datalist_node.addData(matobj.group(1))
            return datalist_node

        return parent_node
