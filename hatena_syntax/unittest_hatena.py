#-*- coding:shift_jis -*-

from hatena_parser import *
import unittest

def dump_hatena_doc_tree(doc, indent=0):
    txt = '%s%s\n' % (' ' * indent, type(doc))
    try:
        txt += '\n'.join(dump_hatena_doc_tree(c, indent+1) for c in doc.children)
    except AttributeError:
        pass
    return txt

class HatenaDocDumper(object):
    def __init__(self):
        self.txtbuf = ""
        self.indent_lvl = 0

        #iwrite 用ワーク
        self.inline_sep_char = '/'
        self.cr_char         = '↓'
        self.last_is_iwrite = False


    def iwrite(self, txt):
        '''inline_plane_text 用特別版write関数'''
        # 前回 iwrite してたらセパレータを挿入
        if self.last_is_iwrite:
            self.txtbuf += self.inline_sep_char

        # 要素内改行文字の処理
        lines = txt.split('\n')
        for i in range(0, len(lines)):
            if self.txtbuf[-1] == '\n':
                self.txtbuf += self.indent_str()
            self.txtbuf += lines[i]
            if i < (len(lines) -1):
                self.txtbuf += '%s' % self.cr_char

        # iwrite 継続中フラグを建てる
        self.last_is_iwrite = True

    def writeln(self, txt):
        # 継続iwrite のクローズ処理
        if self.last_is_iwrite:
            self.txtbuf += '\n'
            self.last_is_iwrite = False

        self.txtbuf += '%s%s\n' % (self.indent_str(), txt)

    def indent(self): self.indent_lvl += 1
    def unindent(self): self.indent_lvl -= 1
    def indent_str(self): return '  ' * self.indent_lvl

    #===========================================
    # 要素別レンダリング
    #===========================================

    def visit_node(self, node):
        '''未知の種類のノード'''
        self.writeln('<node>')
        self.indent()
        for child in node.children:
            child.accept(self)
        self.unindent()
        self.writeln('</node>')
    
    def visit_entry(self, entry):
        self.writeln('<entry>')
        self.indent()
        for child in entry.children:
            child.accept(self)
        self.unindent()
        self.writeln('</entry>')

    def visit_entry_header(self, entry_header):
        self.writeln('<entry_header>')
        self.writeln(':category:%s' % entry_header.category)
        self.writeln(':text:%s' % entry_header.text)
        self.writeln('</entry_header>')

    def visit_header(self, header):
        self.writeln('<header>')
        self.writeln(':level:%s' % header.level)
        self.writeln(':text:%s' % header.text)
        self.writeln('</header>')

    def visit_paragraph(self, paragraph):
        self.writeln('<paragraph>')
        self.indent()
        for line in paragraph.lines:
            line.accept(self)
        self.unindent()
        self.writeln('</paragraph>')

    def visit_supre_pre(self, supre_pre):
        self.writeln('<supre_pre>')
        self.indent()
        for line in supre_pre.content:
            self.writeln('"%s"' % line)
        self.unindent()
        self.writeln('</supre_pre>')

    def visit_block_quote(self, block_quote):
        self.writeln('<blockquote>')

        self.indent()
        for line in block_quote.content:
            line.accept(self)
        self.unindent()

        if block_quote.link != None:
            self.writeln(':link:')
            self.indent()
            block_quote.link.accept(self)        
            self.unindent()

        self.writeln('</blockquote>')


    def visit_table(self, table):
        self.writeln('<table>')

        self.indent()
        for row in table.rows:
            self.writeln('(table_row)')
            self.indent()
            for cel in row:
                self.writeln('(table_cel)%s(/table_cel)' % cel)
            self.unindent()
            self.writeln('(/table_row)')

        self.unindent()
        self.writeln('</table>')


    def visit_list(self, a_list):
        self.writeln('<list>')
        self.indent()

        for lv, txt in a_list.lists:
            self.writeln("(item)")
            self.writeln(":level:%s" % lv)

            self.indent()
            txt.accept(self)
            self.unindent()
            self.writeln("(/item)")

        self.unindent()
        self.writeln('</list>')


    def visit_number_list(self, a_list):
        self.writeln('<number_list>')
        self.indent()

        for lv, txt in a_list.lists:
            self.writeln("(item)")
            self.writeln(":level:%s" % lv)

            self.indent()
            txt.accept(self)
            self.unindent()
            self.writeln("(/item)")

        self.unindent()
        self.writeln('</number_list>')



    #----------------------------------------
    # inline element

    def visit_plane_text(self, text):
#        if not len(text.text.strip()) == 0: #ゴミ除去
            self.iwrite('%s' % (text.text))

    def visit_html_link(self, html_link):
        self.writeln('(html_link)')
        self.writeln(':url:%s' % html_link.getUrl())
        self.writeln(':options:%s' % html_link.options)
        self.writeln('(/html_link)')

    def visit_footnote(self, footnote):
        self.writeln('(footnote)')
        self.writeln(':content:%s' % footnote.content)
        self.writeln('(/footnote)')
 
    def visit_image(self, img):
        self.writeln('(image)')
        self.writeln(':id:%s' % img.img_id)
        self.writeln('(/image)')


def create_test_environment():
    scanner      = TextScanner()
    parser       = HatenaParser()
    dump_visitor = HatenaDocDumper()
    return (scanner, parser, dump_visitor)




#======================================================


class HatenaSyntaxParserTestCase(unittest.TestCase):
    def setup(self):
        pass

    def terDown(self):
        pass

    def testParagraph_01(self):
        src, ans = (
"""
hogehogehogera
piyopiyo

pipipi
fugafuga
""",
"""
<node>
  <entry>
    <paragraph>
      <node>
        hogehogehogera↓
      </node>
      <node>
        piyopiyo↓
      </node>
    </paragraph>
    <paragraph>
      <node>
        pipipi↓
      </node>
      <node>
        fugafuga↓
      </node>
    </paragraph>
  </entry>
</node>
"""
        )
        scanner, parser, dump_visitor = create_test_environment()
        scanner.setSource(src[1:-1])
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf
        self.assertEqual(dump_visitor.txtbuf.strip(), ans.strip())


    def testParagraph_02(self):
        src, ans = (
"""
*[tech]Todays Learning

**description
This is a test entry for hatena-syntax-paraser's unit-test.

**What Hatena-Syntax

Hatena Syntax is one of the text-base markup language which used in Hatena Dialy.
This Syntax is designed for Programming Geek((ex, super-pre syntax has syntax-highlight for many Programming Language)). 
""",
"""
<node>
  <entry>
    <entry_header>
    :category:tech
    :text:Todays Learning
    </entry_header>
    <header>
    :level:2
    :text:description
    </header>
    <paragraph>
      <node>
        This/ /is/ /a/ /test/ /entry/ /for/ /hatena-syntax-paraser's/ /unit-test.↓
      </node>
    </paragraph>
    <header>
    :level:2
    :text:What Hatena-Syntax
    </header>
    <paragraph>
      <node>
        Hatena/ /Syntax/ /is/ /one/ /of/ /the/ /text-base/ /markup/ /language/ /which/ /used/ /in/ /Hatena/ /Dialy.↓
      </node>
      <node>
        This/ /Syntax/ /is/ /designed/ /for/ /Programming/ /Geek
        (footnote)
        :content:ex, super-pre syntax has syntax-highlight for many Programming Language
        (/footnote)
        ./ /↓
      </node>
    </paragraph>
  </entry>
</node>
""")

        scanner, parser, dump_visitor = create_test_environment()
        scanner.setSource(src[1:-1])
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf
        self.assertEqual(dump_visitor.txtbuf, ans[1:])



    def testHtmlSyntax_01(self):
        src, ans = (
"""
[http://hogehoge.co.jp/piyo.html:title=Page of Hoge]
""",
"""
<node>
  <entry>
    <paragraph>
      <node>
        (html_link)
        :url:http://hogehoge.co.jp/piyo.html
        :options:['title=Page of Hoge']
        (/html_link)
        ↓
      </node>
    </paragraph>
  </entry>
</node>
""")

        scanner, parser, dump_visitor = create_test_environment()
        scanner.setSource(src[1:-1])
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf
        self.assertEqual(dump_visitor.txtbuf, ans[1:])


    def testTableSyntax_01(self):
        src, ans = (
"""
||*h_a|*h_b|*h_c|
|*h_0|a0|b0|c0|
|*h_1|a1|b1|c1|
|*h_2|a2|b2|c2|
""",
"""
<node>
  <entry>
    <table>
      (table_row)
        (table_cel)(/table_cel)
        (table_cel)*h_a(/table_cel)
        (table_cel)*h_b(/table_cel)
        (table_cel)*h_c(/table_cel)
      (/table_row)
      (table_row)
        (table_cel)*h_0(/table_cel)
        (table_cel)a0(/table_cel)
        (table_cel)b0(/table_cel)
        (table_cel)c0(/table_cel)
      (/table_row)
      (table_row)
        (table_cel)*h_1(/table_cel)
        (table_cel)a1(/table_cel)
        (table_cel)b1(/table_cel)
        (table_cel)c1(/table_cel)
      (/table_row)
      (table_row)
        (table_cel)*h_2(/table_cel)
        (table_cel)a2(/table_cel)
        (table_cel)b2(/table_cel)
        (table_cel)c2(/table_cel)
      (/table_row)
    </table>
  </entry>
</node>
""")

        scanner, parser, dump_visitor = create_test_environment()
        scanner.setSource(src[1:-1])
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf
        self.assertEqual(dump_visitor.txtbuf, ans[1:])


    def testListSyntax_01(self):
        src, ans = (
"""
-list_item1
-list_item2
--list_item2-2
-list_item3
--list_item3-1
--list_item3-2
---list_item3-2-1
---list_item3-2-2
-list_item4
""",
"""
<node>
  <entry>
    <list>
      (item)
      :level:1
        <node>
          list/_/item1
        </node>
      (/item)
      (item)
      :level:1
        <node>
          list/_/item2
        </node>
      (/item)
      (item)
      :level:2
        <node>
          list/_/item2-2
        </node>
      (/item)
      (item)
      :level:1
        <node>
          list/_/item3
        </node>
      (/item)
      (item)
      :level:2
        <node>
          list/_/item3-1
        </node>
      (/item)
      (item)
      :level:2
        <node>
          list/_/item3-2
        </node>
      (/item)
      (item)
      :level:3
        <node>
          list/_/item3-2-1
        </node>
      (/item)
      (item)
      :level:3
        <node>
          list/_/item3-2-2
        </node>
      (/item)
      (item)
      :level:1
        <node>
          list/_/item4
        </node>
      (/item)
    </list>
  </entry>
</node>
""")

        scanner, parser, dump_visitor = create_test_environment()
        scanner.setSource(src[1:-1])
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf
        self.assertEqual(dump_visitor.txtbuf, ans[1:])


    def testNumberListSyntax_01(self):
        src, ans = (
"""
+list_item1
+list_item2
++list_item2-2
+list_item3
++list_item3-1
++list_item3-2
+++list_item3-2-1
+++list_item3-2-2
+list_item4
""",
"""
<node>
  <entry>
    <number_list>
      (item)
      :level:1
        <node>
          list/_/item1
        </node>
      (/item)
      (item)
      :level:1
        <node>
          list/_/item2
        </node>
      (/item)
      (item)
      :level:2
        <node>
          list/_/item2-2
        </node>
      (/item)
      (item)
      :level:1
        <node>
          list/_/item3
        </node>
      (/item)
      (item)
      :level:2
        <node>
          list/_/item3-1
        </node>
      (/item)
      (item)
      :level:2
        <node>
          list/_/item3-2
        </node>
      (/item)
      (item)
      :level:3
        <node>
          list/_/item3-2-1
        </node>
      (/item)
      (item)
      :level:3
        <node>
          list/_/item3-2-2
        </node>
      (/item)
      (item)
      :level:1
        <node>
          list/_/item4
        </node>
      (/item)
    </number_list>
  </entry>
</node>
""")

        scanner, parser, dump_visitor = create_test_environment()
        scanner.setSource(src[1:-1])
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf
        self.assertEqual(dump_visitor.txtbuf.strip(), ans.strip())

    def testHtmlSyntax_02(self):
        src, ans = (
"""
[http://hogehoge.co.jp/piyo_hoge.html:title=Page of Hoge and Piyo]
""",
"""
<node>
  <entry>
    <paragraph>
      <node>
        (html_link)
        :url:http://hogehoge.co.jp/piyo_hoge.html
        :options:['title=Page of Hoge and Piyo']
        (/html_link)
        ↓
      </node>
    </paragraph>
  </entry>
</node>
""")
        scanner, parser, dump_visitor = create_test_environment()
        scanner.setSource(src[1:-1])
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf
        self.assertEqual(dump_visitor.txtbuf.strip(), ans.strip())



    def testHtmlSyntax_in_blockquote_01(self):
        scanner, parser, dump_visitor = create_test_environment()

        scanner.setSource('''
>http://hogehoge.co.jp/piyo_hoge.html:title=Page of Hoge and Piyo>
hogehogehoge
<<
        ''')
        doc = parser.parse(scanner)
        doc.accept(dump_visitor)
        #print dump_visitor.txtbuf







if __name__ == '__main__':
    unittest.main()
