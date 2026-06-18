import os
import shutil
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings

from backup_app.models import BackupJob, BackupFile, CompanySettings


class Command(BaseCommand):
    help = "Löscht alte Backups basierend auf den Aufbewahrungseinstellungen (Standard 5 Tage)"

    def handle(self, *args, **options):
        company = CompanySettings.get_settings()
        retention = timedelta(days=company.backup_retention_days)
        cutoff = timezone.now() - retention

        old_jobs = BackupJob.objects.filter(
            started_at__lt=cutoff
        ).exclude(status="running")

        count = old_jobs.count()
        self.stdout.write(
            f"Lösche {count} alte Backup-Jobs "
            f"(älter als {company.backup_retention_days} Tage)..."
        )

        for job in old_jobs:
            job_dir = os.path.join(
                settings.MEDIA_ROOT, "backups",
                str(job.client_id), str(job.id)
            )
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir)
            job.delete()

        self.stdout.write(self.style.SUCCESS(
            f"{count} alte Backups gelöscht "
            f"(Aufbewahrung: max. {company.backup_retention_days} Tage)"
        ))
