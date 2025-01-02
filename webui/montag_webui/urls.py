from django.urls import path

from . import views

urlpatterns = [
    path("", views.timeline, name="timeline"),
    path("search", views.search, name="search"),
    path("upload_file", views.upload_file, name="upload_file"),
    path("view_tome/<str:tome_guid>", views.view_tome, name="view_tome"),
    path("edit_tome/<str:tome_guid>", views.edit_tome, name="edit_tome"),
    path("view_author/<str:author_guid>", views.view_author, name="view_author"),
    path("import_overview", views.import_overview, name="import_overview"),
    path("list_friends", views.list_friends, name="list_friends"),
    path("more_actions", views.more_actions, name="more_actions"),
]
