from django import template
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from pydb import FileType
from pydb import network_params
from pydb import title

from montag_webui import html_helpers

register = template.Library()

def short_synopsis_content(synopsis):
    synopsis_text = synopsis['content'][:100]+" ..." if len(synopsis['content']) > 100 else synopsis['content']
    return synopsis_text

def short_synopsis(tome, synopsis):
    synopsis_text = short_synopsis_content(synopsis)
    return synopsis_text
    # @fixme: migrate return A(synopsis_text, _class="synopsis_link", _href=URL('default', 'view_tome', args=[tome['guid']],
    #                                                              anchor="synopsis"))

_friend_name_cache = {0: 'You'}

def lookup_friend_name(pdb, friend_id):
    if friend_id not in _friend_name_cache:
        friend = pdb.get_friend(friend_id)
        _friend_name_cache[friend_id] = friend['name']

    return _friend_name_cache[friend_id]


@register.inclusion_tag('montag_webui/tome_info_block.html')
def tome_info_block(pdb, tome, *args, **kwargs):
    include_change_info=kwargs.get("include_change_info", False)
    show_edit_button=kwargs.get("show_edit_button", True)
    show_file_edit_button=kwargs.get("show_file_edit_button", True)
    additional_tome_button_html=kwargs.get("additional_tome_button_html", None)

    relevant_synopses = list(network_params.relevant_items(tome['synopses']))
    if relevant_synopses:
        best_synopsis = sorted(relevant_synopses, key=lambda x: x['fidelity'], reverse=True)[0]
        best_synopsis_short = short_synopsis(tome, best_synopsis)
    else:
        best_synopsis = None
        best_synopsis_short = None

    relevant_files = filter( lambda f: f['file_type'] == FileType.Content and network_params.is_relevant(f), tome['files'])

    if include_change_info:
        change_info = pdb.get_latest_tome_related_change(tome['guid'])
        friend = lookup_friend_name(pdb, change_info['friend_id'])
    else:
        change_info = None
        friend = None

    context = {
        'tome': tome,
        'show_edit_button': show_edit_button,
        'show_file_edit_button': show_file_edit_button,
        'additional_tome_button_html': additional_tome_button_html,
        'relevant_synopses': relevant_synopses,
        'best_synopsis': best_synopsis,
        'best_synopsis_short': best_synopsis_short,
        'relevant_files': relevant_files,
        'change_info': change_info,
        'friend': friend,
    }

    return context


@register.simple_tag
def tome_link(tome_info):
    title_text = title.coalesce_title(tome_info['title'], tome_info['subtitle'])

    url = reverse('view_tome', args=[tome_info['guid']])

    return format_html('<a href="{}" class="tome_link">{}</a>', url, title_text)

@register.simple_tag
def tome_edit_link(tome_info):
    url = reverse('edit_tome', args=[tome_info['guid']])

    return format_html('<a href="{}" class="tome_link">edit</a>', url)

@register.simple_tag
def author_link(author_detail_info):

    url = reverse('view_author', args=[author_detail_info['guid']])
    return format_html('<a href="{}" class="author_link">{}</a>', url, author_detail_info['name'])

@register.simple_tag
def authors_links(author_link_infos):
    links = [author_link(author_link_info['detail'])
             for author_link_info in network_params.relevant_items(author_link_infos)]
    return mark_safe(", ".join(links))

@register.simple_tag
def formatted_synopsis(synopsis):
    return html_helpers.wrap_lines(synopsis['content'], min_line_length=60, max_line_length=100)

old_code = """
{{
from pydb import FileType
from pydb_helpers import html_helpers
from pydb import network_params

}}
{{ tome_block_id = 1 }}
{{ tome_synopsis_id = 1 }}
{{ def next_tome_block_id():
    global tome_block_id
    tome_block_id+=1
    return tome_block_id-1
}}
{{ def next_tome_synopsis_id():
    global tome_synopsis_id
    tome_synopsis_id += 1
    return tome_synopsis_id-1
}}
{{ from operator import itemgetter }}
{{
def show_file_operation_links(tome, file):
    =A(html_helpers.generate_download_filename(tome, file), _href=URL( 'default', 'getfile',args=[tome['id'],file['hash']]))
    if pydb.config.has_ebook_convert():
        =' '
        =A('MOBI', _href=URL( 'default', 'getfile_as_mobi',args=[tome['id'],file['hash']] ))
    pass
    =' '
    if file['file_extension']=='epub':
        =A('VIEW', _href=URL( c='viewfile', a='viewer',args=[tome['id'],file['hash']] ))
    elif file['file_extension']=='pdf':
        =A('VIEW', _href=URL( c='viewpdf', a='viewer',args=[tome['id'],file['hash']] ))
    elif pydb.config.has_ebook_convert():
        =A('VIEW*', _href=URL( c='viewfile', a='viewer',args=[tome['id'],file['hash']] ))
    pass
pass
}}

{{def show_tome_file_block(tome, show_edit_button=True):}}
    <ul class="files" id="tome_file_block_{{=next_tome_block_id()}}" >
      {{
        relevant_files = filter(lambda f: f['file_type']==pydb.FileType.Content and network_params.is_relevant(f), tome['files'])
        for file in relevant_files:}}
      <li>
      {{if 'has_local_copy' in file and file['has_local_copy']:
        show_file_operation_links(tome, file)
      else:
      = tome['title']+"."+file['file_extension']
      pass}}
      {{=int(file['fidelity']) }}/100
          {{ if show_edit_button and auth.has_privilege('data_edit'): }}
          <span class="edit"> {{ =A("edit link", _href=URL( 'edit_tome_file_link',args=[tome['id'],file['hash']], ))}}  </span>
          {{pass}}
        </li>
    {{pass}}
    </ul>
{{return}}

{{def hide_all_files():}}
<script>
jQuery(document).ready(function(){
   jQuery('.files').hide();
});
</script>
{{return}}

{{def hide_all_synopses():}}
<script>
jQuery(document).ready(function(){
   jQuery('.synopsis_full').hide();
});
</script>
{{return}}

{{def _show_tome_edition_line(tome):
    edition_info_line = html_helpers.string_or_empty(tome['edition']) + " " + html_helpers.string_or_empty(tome['publication_year'])
    edition_info_line = edition_info_line.strip()
    if edition_info_line: }}
        <span>
        {{=edition_info_line}}
        </span><br>
    {{pass}}
{{return}}

{{ def show_tome_tag_line(tome_doc): }}
    {{  tag_info = tome_tag_links(tome_doc) }}
    {{ if tag_info: }} —
        {{ =tag_info }}
    {{pass}}
{{ return }}

{{ def show_tome_edition_tags_block(tome_doc): }}
{{ _show_tome_edition_line(tome_doc) }}
    {{=tome_doc['principal_language']}} {{=pydb.tome_type_text(tome_doc['type'])}} — {{=int(tome_doc['fidelity'])}}/100
    {{show_tome_tag_line(tome_doc)}}<br>
{{ return }}

{{ def show_short_tome_info_block(tome): }}
<li class="tome">
    <div class="tome_info_paragraph">
    <span class="tome_info_block"> {{=tome_link(tome)}} by {{=authors_links(tome['authors'])}}
    </span><br>

    {{show_tome_edition_tags_block(tome)}}

    </div>
    <div class="clearfix"></div>
</li>
{{ return}}





{{def show_tome_synopses_block(tome):}}

    <ul class="synopses" >
      {{
        syn_idx=0
        for synopsis in tome['synopses']:}}
      <li> <span class="synopsis">
      {{
        = short_synopsis_content(synopsis)
      }}  </span>
      {{=int(synopsis['fidelity']) }}/100
          <br>
          <span class='hide_show_button' onclick="jQuery('#tome_synopsis_block_{{=tome_synopsis_id}}').slideToggle(100)"> Show / edit full synopsis </span>
          {{if synopsis['content']:}}
              <span class="synopsis_full" id="tome_synopsis_block_{{=next_tome_synopsis_id()}}" > {{ =synforms[syn_idx] }} </span>
          {{else:}}
              <span class="synopsis_empty" id="tome_synopsis_block_{{=next_tome_synopsis_id()}}" > {{ =synforms[syn_idx] }} </span>
          {{pass}}
      </li>
        {{syn_idx+=1}}
    {{pass}}
    </ul>

{{return}}


{{def show_author_info_block(author_info, allow_edit=False, additional_author_button_html=None, first_on_page=False):
    class_string = ''
    if first_on_page:
        class_string=' class='+XML("first_on_page")
    pass
}}

    <h1 {{=class_string}}>{{=author_link(author_info) }}
        {{ if allow_edit and auth.has_privilege('data_edit'):
        =A("edit", _class='edit_author', _href=URL( 'edit_author',args=[author_info['guid']] ))
        pass}}
    {{ if additional_author_button_html is not None: }}
        {{=additional_author_button_html}}
    {{pass}}

    </h1>

    {{ = format_bibliography_dates(author_info) }}
    <br/>
    Fidelity = {{=int(author_info['fidelity']) }}/100
{{return}}
"""