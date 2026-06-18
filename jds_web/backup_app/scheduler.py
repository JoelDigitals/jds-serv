import os
import time
import shutil
import threading
import logging
from datetime import timedelta

from django.utils import timezone
from django.conf import settings


logger = logging.getLogger("jds_scheduler")
CLEANUP_INTERVAL = 6 * 3600


def _run_cleanup():
    try:
        from backup_app.models import BackupJob, CompanySettings
    except Exception as e:
        logger.warning("Scheduler: Models nicht verfügbar – %s", e)
        return

    try:
        company = CompanySettings.get_settings()
    except Exception as e:
        logger.warning("Scheduler: Einstellungen nicht lesbar – %s", e)
        return

    retention = timedelta(days=company.backup_retention_days)
    cutoff = timezone.now() - retention

    try:
        old_jobs = list(BackupJob.objects.filter(
            started_at__lt=cutoff
        ).exclude(status="running"))
    except Exception as e:
        logger.warning("Scheduler: DB-Abfrage fehlgeschlagen – %s", e)
        return

    if not old_jobs:
        return

    logger.info("Scheduler: Lösche %d alte Backup-Jobs (älter als %d Tage)...",
                len(old_jobs), company.backup_retention_days)

    for job in old_jobs:
        try:
            job_dir = os.path.join(
                settings.MEDIA_ROOT, "backups",
                str(job.client_id), str(job.id)
            )
            if os.path.exists(job_dir):
                shutil.rmtree(job_dir)
            job.delete()
        except Exception as e:
            logger.warning("Scheduler: Fehler bei Job #%d – %s", job.id, e)

    logger.info("Scheduler: Cleanup abgeschlossen (%d Jobs gelöscht)", len(old_jobs))


def _scheduler_loop():
    logger.info("Scheduler gestartet – Cleanup alle %d Stunden", CLEANUP_INTERVAL // 3600)
    while True:
        try:
            time.sleep(CLEANUP_INTERVAL)
            _run_cleanup()
        except Exception:
            time.sleep(60)


def start_scheduler():
    thread = threading.Thread(target=_scheduler_loop, daemon=True, name="jds-cleanup")
    thread.start()
