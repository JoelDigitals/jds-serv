import sys
from django.apps import AppConfig


class BackupAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backup_app"
    verbose_name = "JDS Backup Verwaltung"

    def ready(self):
        if "runserver" not in sys.argv and "gunicorn" not in sys.argv[0]:
            return
        try:
            from .scheduler import start_scheduler
            start_scheduler()
        except Exception:
            pass
