# coding: utf8
if False:
    from ide_fake import *


import time
import re
from web2py.applications.montag.modules.pydb_functions import db_str_to_form


def author_link(author_detail_info):
    result = A(author_detail_info['name'],
               _class="author_link",
               _href=URL('default', 'view_author',
               args=[author_detail_info['guid']]))
    return result


def _concat_link_list(link_list):
    if not link_list:
        return ""
    result = link_list[0]
    for link in link_list[1:]:
        result = CAT(result, ", ", link)
    return result


def authors_links(author_link_infos):
    links = [author_link(author_link_info['detail']) for author_link_info in relevant_items(author_link_infos)]
    return _concat_link_list(links)


def author_list(author_link_infos):
    items = [author_link_info['detail']['name'] for author_link_info in relevant_items(author_link_infos)]
    return _concat_link_list(items)


def search_link(text, query, class_="search_link"):
    return A(text, _class=class_, _href=URL('default', 'tomesearch',
                                            vars={'query': db_str_to_form(query),
                                                  '_formname': 'search',
                                                  'principal_language': '',
                                                  'tome_type': 'Z'}))


def tag_link(tag_text):
    search_text = re.sub(" *[0-9]+$", "", tag_text)
    return search_link(tag_text, u'tag:"{}"*'.format(search_text), class_="tag_link")


def title_by_authors_link(title_text, author_link_infos):
    search_title_text = re.sub("Preceded by ", "", title_text)
    search_title_text = re.sub("Followed by ", "", search_title_text)
    search_authors_text = ''.join([u'author:"{}"'.format(author_link_info['detail']['name'])
                                   for author_link_info in relevant_items(author_link_infos)])
    search_text = u'title:"{}"'.format(search_title_text) + " " + search_authors_text
    return search_link(title_text, search_text, class_="tag_link")


def tome_tag_links(tome_info):
    links = []
    for tag in tome_info['tags']:
        if tag['fidelity'] > cfg_tags_minimum_display_fidelity:
            if re.search("Preceded by ", tag['tag_value']) or re.search("Followed by ", tag['tag_value']):
                links.append(title_by_authors_link(tag['tag_value'], tome_info['authors']))
            else:
                links.append( tag_link(tag['tag_value']) )
    return _concat_link_list(links)


def tome_link(tome_info):
    import pydb.title
    title_text=pydb.title.coalesce_title(tome_info['title'], tome_info['subtitle'])

    result=A(title_text, _class="tome_link", _href=URL( 'default', 'view_tome', args=[tome_info['guid']] ))
    return result


def short_synopsis(tome, synopsis):
    synopsis_text = short_synopsis_content(synopsis)
    return A(synopsis_text, _class="synopsis_link", _href=URL( 'default', 'view_tome', args=[tome['guid']], anchor="synopsis" ))


def short_synopsis_content(synopsis):
    synopsis_text = synopsis['content'][:100]+" ..." if len( synopsis['content'] ) > 100 else synopsis['content']
    return synopsis_text


def human_readble_time(unixtime): 
# <!--2014-01-18T12:34Z-->
    if not unixtime:
        return "Never"
    return time.strftime('%Y-%m-%dT%H:%MZ',time.gmtime(unixtime))


def human_readble_time_elapsed_since(unixtime): 
    if not unixtime:
        return "Never"
    
    dt = time.time()-unixtime
    if dt <2:
        return "Just now"
    if dt < 55:
        return "{} seconds ago".format(int((dt+5)/10)*10)
    
    dt/=60
    if dt < 1.5:
        return "One minute ago"
    if dt < 59.5:
        return "{} minutes ago".format(int(dt+0.5))
    
    dt/=60
    if dt < 1.5:
        return "One hour ago"
    if dt < 59.5:
        return "{} hours ago".format(int(dt+0.5))

    dt/=24
    if dt < 1.5:
        return "One day ago"

    return "{} days ago".format(int(dt+0.5))


def render_synopsis(synopsis):
    c = synopsis['content']

    max_line_length = 100
    min_line_length = 60
    
    lines=[]
    for l in c.split("\n"):
       while len(l) > max_line_length:
            pos = max_line_length-1
            while l[pos] != " " and pos > min_line_length:
                pos -= 1
            if l[pos] != " ":
                pos = max_line_length-1
            k=l[0:pos+1]
            l=l[pos+1:]
            lines.append(k)
       lines.append(l)
    return '\n'.join(lines)

def nice_name(name):
    tn = name.replace("_"," ")
    tn = tn[0].upper() + tn[1:]
    return tn

def nice_name_lcfirst(name):
    tn = name.replace("_"," ")
    return tn
    
def nice_table_name(table_name):
    tn = table_name.replace("_"," ")
    # remove trailing s
    tn = tn[:-1]
    tn = tn[0].upper() + tn[1:]
    return tn

def string_or_empty( text ):
    return unicode(text) if text is not None else ""

def short_hash(full_hash):
    return full_hash[:4]

def generate_download_filename(tome, file):
    return u"{} ({}).{}".format(tome['title'],short_hash(file['hash']), file['file_extension'])


def format_bibliography_dates(author_info):
    result = ""
    if author_info['date_of_birth']:
        result = "Born "+author_info['date_of_birth']
    else:
        result = "No date of birth provided yet"
    
    if author_info['date_of_death']:
        result += ", died "+author_info['date_of_death']
    else:
        if author_info['date_of_birth']:
            result += ', no date of death provided yet.'
        else:
            result += ', nor date of death.'
    
    return result
