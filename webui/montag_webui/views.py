import re

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import redirect, reverse
from django.template import loader

from pydb import pyrosetup, documents
from webui.montag_webui.forms import SearchForm

ITEMS_PER_PAGE = 20

def timeline(request):
    pdb = pyrosetup.pydbserver()

    page_number = int(request.GET.get("page", "1"))
    page_start = (page_number -1 )  * ITEMS_PER_PAGE
    page_end = page_number * ITEMS_PER_PAGE
    number_results_total = pdb.get_tome_document_timeline_size()

    changed_tome_guids = pdb.get_tome_document_timeline(ITEMS_PER_PAGE, page_start)

    tome_documents = []
    for tome_index, tome_guid in enumerate(changed_tome_guids):
        tome = pdb.get_tome_document_by_guid(tome_guid, keep_id=True, include_local_file_info=True,
                                             include_author_detail=True, hide_private_tags=False)
        if 'title' in tome:
            tome['index'] = tome_index + 1
            # @fixme: re-add
          #  documents.remove_detail_tags(tome)
            tome_documents.append(tome)

    context = {
        'tome_info': tome_documents,
        'title': 'Timeline',
        'page': page_number,
        'page_start': page_start,
        'page_end': page_end,
        'number_results_total': number_results_total,
        'pdb': pdb
    }

    template = loader.get_template("montag_webui/timeline.html")
    return HttpResponse(template.render(context, request))

def _is_tome_or_author_guid(string):
    return re.match("[0-9a-z]{32}", string)

def _is_file_hash(string):
    return re.match("[0-9a-z]{64}", string)

def get_query_page(pdb, query, start_offset, end_offset):
    index_server = pyrosetup.indexserver()
    result_tome_ids = index_server.search_tomes(query)

    tome_documents = []
    for tome_id in result_tome_ids[start_offset:end_offset]:
        merge_tome = pdb.get_tome(tome_id)
        if merge_tome is not None:
            tome = pdb.get_tome_document_by_guid(merge_tome['guid'], keep_id=True,
                                                 include_local_file_info=True, include_author_detail=True,
                                                 hide_private_tags=False)
            documents.remove_detail_tags(tome)
            tome_documents.append(tome)

    def tome_key(t):
        if not t['authors']:
            return ""
        return t['authors'][0]['detail']['name']
    tome_documents.sort(key=tome_key)

    return len(result_tome_ids), tome_documents

def search(request):
    pdb = pyrosetup.pydbserver()

    form = SearchForm(request.GET, pdb=pdb)
    query = ""
    page_number = 0
    page_start = 0
    page_end = 0
    total_count = 0
    tomes = None

    if form.is_valid():
        query = form.cleaned_data.get('query').strip()
        if _is_tome_or_author_guid(query):
            tome = pdb.get_tome_by_guid(query)
            if tome is not None:
                return redirect(reverse('view_tome', args=[query]))

            author = pdb.get_author_by_guid(query)
            if author is not None:
                return redirect(reverse('view_author', args=[query]))

        if _is_file_hash(query):
            tome_files = pdb.get_tome_files_by_hash(query)
            for tome_file in tome_files:
                tome_id = tome_file['tome_id']
                tome = pdb.get_tome(tome_id)
                if tome is not None:
                    return redirect(reverse('view_tome', args=[tome['guid']]))

        search_query = form.build_search_query()
        page_number = int(request.GET.get("page", "1"))
        page_start = (page_number-1) * ITEMS_PER_PAGE
        page_end = page_number * ITEMS_PER_PAGE

        total_count, tomes = get_query_page(pdb, search_query, page_start, page_end)
        page_end = page_start + len(tomes)

    context = {"form": form,
               'page': page_number,
               'page_start': page_start,
               'page_end': page_end,
               'number_results_total': total_count,
               'tome_info': tomes,
               'query': query}
    template = loader.get_template("montag_webui/search.html")
    return HttpResponse(template.render(context, request))


def view_tome(request, tome_guid):
    pdb = pyrosetup.pydbserver()

    tome = pdb.get_tome_document_by_guid(tome_guid, keep_id=True,
                                         include_local_file_info=True, include_author_detail=True,
                                         hide_private_tags=False)
    if 'title' not in tome:
        tome_guid = pdb.get_tome_fusion_target_guid(tome_guid)
        if tome_guid:
            return redirect(reverse('view_tome', args=[tome_guid]))


    context = {"tome": tome}
    template = loader.get_template("montag_webui/view_tome.html")
    return HttpResponse(template.render(context, request))

def edit_tome(request, tome_guid):
    return HttpResponse("NYI")

def view_author(request, author_guid):
    return HttpResponse("NYI")

def upload_file(request):
    return HttpResponse("NYI")

def import_overview(request):
    return HttpResponse("NYI")

def list_friends(request):
    return HttpResponse("NYI")

def more_actions(request):
    return HttpResponse("NYI")
