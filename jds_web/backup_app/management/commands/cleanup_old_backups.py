import os
import shutil
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError


class Command(BaseCommand):
    help = "Löscht alte Backups (Standard: 5 Tage) – läuft im Cron-Job"

    def handle(self, *args, **options):
        try:
            from backup_app.models import BackupJob, CompanySettings
        except Exception as e:
            self.stderr.write(f"Datenbank-Tabellen nicht verfügbar: {e}")
            return

        try:
            company = CompanySettings.get_settings()
        except (OperationalError, ProgrammingError) as e:
            self.stderr.write(f"Datenbank nicht erreichbar: {e}")
            return
        except Exception as e:
            self.stderr.write(f"Fehler beim Laden der Einstellungen: {e}")
            return

        retention = timedelta(days=company.backup_retention_days)
        cutoff = timezone.now() - retention

        try:
            old_jobs = BackupJob.objects.filter(
                started_at__lt=cutoff
            ).exclude(status="running")
            count = old_jobs.count()
        except Exception as e:
            self.stderr.write(f"Fehler bei Datenbank-Abfrage: {e}")
            return

        if count == 0:
            self.stdout.write("Keine alten Backups zum Löschen.")
            return

        self.stdout.write(
            f"Lösche {count} alte Backup-Jobs "
            f"(älter als {company.backup_retention_days} Tage)..."
        )

        deleted = 0
        for job in old_jobs:
            try:
                job_dir = os.path.join(
                    settings.MEDIA_ROOT, "backups",
                    str(job.client_id), str(job.id)
                )
                if os.path.exists(job_dir):
                    shutil.rmtree(job_dir)
                job.delete()
                deleted += 1
            except Exception as e:
                self.stderr.write(f"Fehler bei Job #{job.id}: {e}")
                continue

        self.stdout.write(self.style.SUCCESS(
            f"{deleted} alte Backups gelöscht "
            f"(Aufbewahrung: max. {company.backup_retention_days} Tage)"
        ))
