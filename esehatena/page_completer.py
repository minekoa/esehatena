#-*- coding:utf-8 -*-

import hatena_syntax
import codecs
import re
from my_enc_tool import *

class PageCompleter(object):
    '''
    Hatena記法で書かれたページに対して、あとはお任せで完成させる処理。
    具体的には、
      -  link記法でかれた title を wget で取得して補完する
    を行う。
    '''

    def _parse(self, filepath):
        scanner = hatena_syntax.FileScanner()
        scanner.openFile(filepath)
        parser  = hatena_syntax.HatenaParser()
        return parser.parse(scanner)

    def complete(self, entry):
        # 1. parsing
        hatena_document = self._parse(entry._getFilePath())

        # 2. wget Link URL
        title_appender = hatena_syntax.PageTitleAppender()
        hatena_document.accept(title_appender)

        # 3. source_complete
        new_contents = []
        for line in entry.readlines():
            for linkobj in title_appender.link_list:
                target_ptn = r'%s:title([^=])' % re.escape(linkobj.getUrl())
                repl_txt   = r"%s\1" % linkobj.asString()

                line = re.sub( ez_decode(target_ptn),
                               ez_decode(repl_txt),
                               ez_decode(line) )
                print 'replace!', line[:-1]
            new_contents.append(line)

        # 4. save
        entry.writelines(new_contents)
