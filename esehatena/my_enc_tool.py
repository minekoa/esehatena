#-*- coding:utf-8 -*-

def ez_decode(data):
    if isinstance(data, unicode):
        return data

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
    return data

def conv_encoding(data, to_enc="utf_8"):
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

