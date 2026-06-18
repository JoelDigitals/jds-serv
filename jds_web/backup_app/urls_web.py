from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("client/<int:client_id>/", views.client_detail, name="client_detail"),
    path("client/create/", views.client_create, name="client_create"),
    path("metadata/export/", views.export_metadata, name="export_metadata"),
    path("settings/", views.settings_view, name="settings"),
]
