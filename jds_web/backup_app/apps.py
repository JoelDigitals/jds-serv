import sys
from django.apps import AppConfig


class BackupAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "backup_app"
    verbose_name = "JDS Backup Verwaltung"

    def ready(self):
        if len(sys.argv) > 1 and sys.argv[1] in (
            "migrate", "makemigrations", "collectstatic",
            "createsuperuser", "shell", "ensure_admin",
            "cleanup_old_backups",
        ):
            return
        try:
            from .scheduler import start_scheduler
            start_scheduler()
        except Exception:
            pass
