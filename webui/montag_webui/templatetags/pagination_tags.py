from django import template
from urllib.parse import urlencode

register = template.Library()


@register.inclusion_tag('montag_webui/partials/pagination.html', takes_context=True)
def render_pagination(context, page, page_start, page_end, number_results_total):
    request = context['request']
    query_dict = request.GET.copy()
    query_dict.pop("page", None)

    query_string = urlencode(query_dict)
    query_params = f"&{query_string}" if query_string else ""

    return {
        "query_params": query_params,
        "page": page,
        "previous_page": page-1 if (page > 1) else None,
        "next_page": page + 1 if (page_end < number_results_total) else None,
        "page_start": page_start,
        "page_end": page_end,
        "number_results_total": number_results_total
    }

