from django.urls import path

from . import views

app_name = "matches"

urlpatterns = [
    path("", views.match_dashboard, name="dashboard"),
    path("json/", views.api_matches_json, name="api_matches_json"),
    path("get/", views.get_match, name="get_match"),
    path("get/<uuid:match_id>", views.get_match, name="get_match"),
    path("create/", views.create_match, name="create_match"),
    path("delete/", views.delete_match, name="delete_match"),
    path("delete/<uuid:match_id>", views.delete_match, name="delete_match"),
    path("<uuid:match_id>/book/", views.book_match, name="book_match"),
]
