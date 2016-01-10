# coding=utf-8
import unicodedata


def calc_author_name_key(author_name):
    author_name = unicode(author_name)
    elements = author_name.split(',')
    swapped = ''.join(reversed(elements))
    lower = swapped.lower()
    nfkd = unicodedata.normalize('NFKD', lower)

    remainder = []
    for l in nfkd:
        if l in ' ._:-;&?`%':
            continue
        if unicodedata.combining(l):
            continue
        remainder.append(l)

    result = ''.join(remainder)
    return result
