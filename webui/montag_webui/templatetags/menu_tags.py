from django import template
from django.urls import reverse

import pydb
import pydb.config
from pydb.montag_auth import MontagAuth

register = template.Library()


@register.inclusion_tag('montag_webui/partials/menu.html', takes_context=True)
def render_menu(context):
    request = context['request']
    auth = MontagAuth(request)

    menu_items = []

    def add_menu_item(name, url):
        menu_items.append({
            "name": name,
            "url": url
        })

    if auth.has_privilege("data_view"):
        add_menu_item("Search",   reverse("search"))
        add_menu_item("Timeline", reverse("timeline"))

    if auth.has_privilege("data_edit"):
        add_menu_item("Add Tome",   reverse("upload_file"))
        add_menu_item("Bulk Import",   reverse("import_overview"))

    if auth.has_privilege("friends_view"):
        add_menu_item("Friends",   reverse("list_friends"))

    if auth.has_privilege("friends_view") or auth.has_privilege("statistics_view") or auth.has_privilege("data_view"):
        add_menu_item("More...",   reverse("more_actions"))

    if pydb.config.enable_web_auth():
        if auth.is_user_logged_in():
            add_menu_item("Logout", reverse("user", args="logout"))
        else:
            add_menu_item("Log In", reverse("user"))

    return {"menu_items": menu_items}