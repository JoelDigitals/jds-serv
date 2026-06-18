from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.register_client, name="api_register"),
    path("status/", views.client_status, name="api_status"),
    path("backup/start/", views.start_backup, name="api_start_backup"),
    path("backup/<int:job_id>/update/", views.update_backup, name="api_update_backup"),
    path("backup/<int:job_id>/upload/", views.upload_file, name="api_upload_file"),
    path("log/", views.log_event, name="api_log"),
    path("actions/", views.pending_actions, name="api_actions"),
    path("login/", views.api_login, name="api_login"),
    path("clients/", views.api_list_clients, name="api_list_clients"),
    path("metadata/export/", views.export_metadata, name="api_export_metadata"),
]
