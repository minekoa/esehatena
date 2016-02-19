#-*- coding:shift_jis -*-
import re

from hatena_document import *

#==========================================================
# Parser and Scanner
#==========================================================

class InLineScanner(object):
    def __init__(self, line):
        self.line           = line
        self.token          = None
        self.scan_buf       = self.line 
        self.rollback_state = None

        self.separater_ptn = re.compile(r"[ \t\[\]\(\)]")

    #----------------------------------------
    # rollback proc
    def createRollbackPoint(self):
        self.rollback_state = (self.token, self.scan_buf)

    def deleteRollbackPoint(self):
        self.rollback_state = None

    def rollback(self):
        if self.rollback_state == None:
            raise ValueError('rollback point not found')
        self.token          = self.rollback_state[0]
        self.scan_buf       = self.rollback_state[1]
        self.rollback_state = None


    #----------------------------------------
    # scan proc
    def getLine(self):
        return self.line

    def getToken(self):
        if self.token == None:
            self.advanceToken()
        return self.token
#        return '<' + self.token +'>'

    def advanceToken(self):
        tmp = ''
        if len(self.scan_buf) == 0:
            raise StopIteration

        matobj = self.separater_ptn.search(self.scan_buf)
        if matobj == None:
            self.token    = self.scan_buf
            self.scan_buf = ''
        elif matobj.span()[0] == 0: # 先頭でマッチ
            self.token    = matobj.group(0)
            self.scan_buf = self.scan_buf[matobj.span()[1]:]
        else:                       # 先頭以外でマッチ
            self.token    = self.scan_buf[0:matobj.span()[0]]
            self.scan_buf = self.scan_buf[matobj.span()[0]:]

class InLineParserBase(object):
    def __init__(self):
        self.inline_syntaxes = []
        self.elaborate()

        self.enable_plain_text_parse = True

    def elaborate():
        raise 'subclass responsibility'

    def parse(self, line_str):
        # in-line scanner の初期化
        line_node = LineNode()
        scanner   = InLineScanner(line_str)

        for syntax in self.inline_syntaxes:
            syntax.setScanner(scanner)

        # inline-parse
        try:
            while True:
                for syntax in self.inline_syntaxes:
                    tmp = syntax.parse(line_node)
                    if tmp != None:
                        break
                else:
                    if self.enable_plain_text_parse:
                        self._plainTextParse(line_node, scanner)
                    else:
                        break

        except StopIteration:
            pass
        return line_node

    def _plainTextParse(self, line_node, scanner):
        token = scanner.getToken()
        node = PlainTextINode(token)
        line_node.append(node)

        scanner.advanceToken()


class InLineParser(InLineParserBase):
    def elaborate(self):
        self.inline_syntaxes.append(HtmlLinkSyntax())
        self.inline_syntaxes.append(WikiNameSyntax())
        self.inline_syntaxes.append(ImageSyntax())
        self.inline_syntaxes.append(FootnoteSyntax())
        self.enable_plain_text_parse = True


class HtmlLinkParser(InLineParserBase):
    def elaborate(self):
        self.inline_syntaxes.append(HtmlLinkSyntax())
        self.enable_plain_text_parse = False



#==========================================================
# Inline Syntax 
#==========================================================

class HatenaInlineSyntax(object):
    '''abstract'''

    def setScanner(self, scanner):
        self.scanner = scanner

    #==================================
    # template methods

    def parse(self, parent_node):
        self.scanner.createRollbackPoint()
        ret = self.parse_proc(parent_node)
        if ret == None:
            self.scanner.rollback()
        else:
            self.scanner.deleteRollbackPoint()
        return ret

    def parse_proc(self, parent_node):
        raise "subclass responsibirity"

    #----------------------------------
    # tools

    def scanBlacketContents(self):
        '''スキャナーの復元ポイントはセーブしたままにしておく
        （取得したブラケットの中身が
        欲しい書式じゃないときにロールバックしたいだろうため）

        スキャン後は "]" を指して止まる。
        （進めてしまうと、最終行のとき、StopIteration が発生するので面倒)

        @ret [token, token, token,,,]
        '''
        token = self.scanner.getToken()
        if token != '[':
            return None

        # ブラケットで囲われている場合はその中身を取得
        tokens = []
        try:
            while True:
                self.scanner.advanceToken()
                token = self.scanner.getToken()

                if token == ']':
                    break
                tokens.append(token)

        except StopIteration:
            return None

        return tokens


class HtmlLinkSyntax(HatenaInlineSyntax):
    def __init__(self):
        self.ptn = re.compile(r"^(http:|https:|ftp:|mailto:)([^:]+)(.*)")

    def parse_proc(self, parent_node):
        token = self.scanner.getToken()

        # ブラケットで囲われている場合はその中身を取得
        blacket_tokens = self.scanBlacketContents()
        if blacket_tokens != None:
            # token の連結 (文字コード問題避けのため join を使わない)
            text = ''
            for t in blacket_tokens: text += t

            # parse 実行
            ret = self._parse_content(parent_node, text)
            if ret != None:
                self.scanner.advanceToken() # ']' の分
            return ret

        # ブラケット外はそのままパーズ
        else:
            ret = self._parse_content(parent_node, token)
            if ret != None:
                self.scanner.advanceToken() # 本文の分
            return ret


    def _parse_content(self, parent_node, text):
        matobj = self.ptn.match(text)
        if matobj == None:
            return None

        protocol = matobj.group(1)
        url_body = matobj.group(2)
        if matobj.group(3) != None and len(matobj.group(3).strip()) != 0:
            options  = matobj.group(3)[1:].strip().split(':') #":title=hogehoge" 的な文字列なので、先頭要素は必ず空になる→除去
        else:
            options = []

        node = HtmlLinkINode(protocol, url_body, options)
        parent_node.append(node)

        return parent_node


class ImageSyntax(HatenaInlineSyntax):
    def __init__(self):
        self.ptn = re.compile(r"image:(.+)")

    def parse_proc(self, parent_node):

        # ブラケットで囲われている中身を取得
        blacket_tokens = self.scanBlacketContents()
        if blacket_tokens == None:
            return None

        # イメージ記法チェック
        source = ''
        for t in blacket_tokens: source += t

        matobj = self.ptn.match(source)
        if matobj == None:
            return None

        # node 生成
        img_id = matobj.group(1).strip()
        node = ImageINode(img_id)
        parent_node.append(node)

        self.scanner.advanceToken() # ']' の分進める
        return parent_node

class WikiNameSyntax(HatenaInlineSyntax):
    def __init__(self):
        self.ptn = re.compile(r"wiki:(.+)")

    def parse_proc(self, parent_node):

        # ブラケットで囲われている中身を取得
        blacket_tokens = self.scanBlacketContents()
        if blacket_tokens == None:
            return None

        # イメージ記法チェック
        source = ''
        for t in blacket_tokens: source += t

        matobj = self.ptn.match(source)
        if matobj == None:
            return None

        # node 生成
        wiki_name = matobj.group(1).strip()
        node = WikiNameINode(wiki_name)
        parent_node.append(node)

        self.scanner.advanceToken() # ']' の分進める
        return parent_node


class FootnoteSyntax(HatenaInlineSyntax):
    def __init__(self):
        pass

    def parse_proc(self, parent_node):
        token = self.scanner.getToken()
        if token != '(': return None

        # start (( detect
        opn_cnt = 1

        while True:
            self.scanner.advanceToken()
            token = self.scanner.getToken()

            if token == '(': opn_cnt += 1
            else:
                if opn_cnt == 2:
                    break
                else:
                    return None

        # capture contents and end )) detect
        contents = []
        contents.append(self.scanner.getToken())
        cls_cnt  = 0

        while True:
            self.scanner.advanceToken()
            token = self.scanner.getToken()

            if token == ')': cls_cnt += 1
            else:
                if cls_cnt == 2:
                    break
                elif 0 < cls_cnt:
                    for i in range(0, cls_cnt):
                        contents.append(')')
                    end_cnt = 0
                else:
                    contents += token

        # create Node
        contents_str = ''
        for tok in contents: contents_str += tok

        node = FootnoteINode(contents_str)
        parent_node.append(node)
        return parent_node

