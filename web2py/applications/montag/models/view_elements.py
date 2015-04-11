# coding: utf8
if False:
    from web2py.applications.montag.models.ide_fake import *

import re
from pydb_helpers import html_helpers
from pydb import title


def author_link(author_detail_info):
    result = A(author_detail_info['name'],
               _class="author_link",
               _href=URL('default', 'view_author',
               args=[author_detail_info['guid']]))
    return result


def authors_links(author_link_infos):
    links = [author_link(author_link_info['detail'])
             for author_link_info in network_params.relevant_items(author_link_infos)]
    return html_helpers.concat_link_list(links)


def author_list(author_link_infos):
    items = [author_link_info['detail']['name']
             for author_link_info in network_params.relevant_items(author_link_infos)]
    return html_helpers.concat_link_list(items)


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
                                   for author_link_info in network_params.relevant_items(author_link_infos)])
    search_text = u'title:"{}"'.format(search_title_text) + " " + search_authors_text
    return search_link(title_text, search_text, class_="tag_link")


def tome_tag_links(tome_info):
    links = []
    for tag in tome_info['tags']:

        if network_params.is_relevant(tag):
            if re.search("Preceded by ", tag['tag_value']) or re.search("Followed by ", tag['tag_value']):
                links.append(title_by_authors_link(tag['tag_value'], tome_info['authors']))
            else:
                links.append(tag_link(tag['tag_value']))
    return html_helpers.concat_link_list(links)


def tome_link(tome_info):
    title_text = title.coalesce_title(tome_info['title'], tome_info['subtitle'])

    result = A(title_text, _class="tome_link", _href=URL('default', 'view_tome', args=[tome_info['guid']]))
    return result


def short_synopsis(tome, synopsis):
    synopsis_text = short_synopsis_content(synopsis)
    return A(synopsis_text, _class="synopsis_link", _href=URL('default', 'view_tome', args=[tome['guid']],
                                                              anchor="synopsis"))

def short_synopsis_content(synopsis):
    synopsis_text = synopsis['content'][:100]+" ..." if len(synopsis['content']) > 100 else synopsis['content']
    return synopsis_text


def format_synopsis(synopsis):
    return html_helpers.wrap_lines(synopsis['content'], min_line_length=60, max_line_length=100)


def format_bibliography_dates(author_info):
    if author_info['date_of_birth']:
        result = "Born " + author_info['date_of_birth']
    else:
        result = "No date of birth provided yet"

    if author_info['date_of_death']:
        result += ", died " + author_info['date_of_death']
    else:
        if author_info['date_of_birth']:
            result += ', no date of death provided yet.'
        else:
            result += ', nor date of death.'

    return result


def TOOLTIP(text):
    tip = A(IMG(_src=URL('static', 'images/clker/grey_question_mark.png')), _class="tooltip_trigger", _title=text)
    return tip


def create_error_page(message):
    response.view = 'error/error.html'
    return {'message': message}