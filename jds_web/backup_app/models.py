import uuid
from django.db import models
from django.conf import settings


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True, verbose_name="Unternehmen")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Unternehmen"
        verbose_name_plural = "Unternehmen"

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="users", verbose_name="Unternehmen")

    class Meta:
        verbose_name = "Nutzer-Profil"
        verbose_name_plural = "Nutzer-Profile"

    def __str__(self):
        return f"{self.user.username} ({self.company.name})"


class Client(models.Model):
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name="clients", verbose_name="Unternehmen")
    name = models.CharField(max_length=255, verbose_name="Client-Name")
    machine_id = models.CharField(max_length=255, unique=True, verbose_name="Maschinen-ID")
    api_token = models.CharField(max_length=255, unique=True, verbose_name="API-Token")
    operating_system = models.CharField(max_length=100, blank=True, verbose_name="Betriebssystem")
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name="Zuletzt gesehen")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    max_backups = models.IntegerField(default=30, verbose_name="Max. Backups")
    notes = models.TextField(blank=True, verbose_name="Notizen")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt am")

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.machine_id})"


class BackupJob(models.Model):
    STATUS_CHOICES = [
        ("pending", "Ausstehend"),
        ("running", "Läuft"),
        ("completed", "Abgeschlossen"),
        ("failed", "Fehlgeschlagen"),
        ("cancelled", "Abgebrochen"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="backup_jobs", verbose_name="Client")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name="Status")
    total_files = models.IntegerField(default=0, verbose_name="Dateien gesamt")
    total_size = models.BigIntegerField(default=0, verbose_name="Größe gesamt (Bytes)")
    transferred_size = models.BigIntegerField(default=0, verbose_name="Übertragen (Bytes)")
    error_message = models.TextField(blank=True, verbose_name="Fehlermeldung")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Gestartet")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Abgeschlossen")

    class Meta:
        verbose_name = "Backup-Job"
        verbose_name_plural = "Backup-Jobs"
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.client.name} - {self.get_status_display()} ({self.started_at.strftime('%d.%m.%Y %H:%M')})"


class BackupFile(models.Model):
    backup_job = models.ForeignKey(BackupJob, on_delete=models.CASCADE, related_name="files", verbose_name="Backup-Job")
    file_path = models.CharField(max_length=1024, verbose_name="Dateipfad")
    file_name = models.CharField(max_length=512, verbose_name="Dateiname")
    file_size = models.BigIntegerField(default=0, verbose_name="Dateigröße")
    file_hash = models.CharField(max_length=64, verbose_name="SHA-256 Hash")
    storage_path = models.CharField(max_length=1024, verbose_name="Speicherpfad")
    is_directory = models.BooleanField(default=False, verbose_name="Verzeichnis")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt")

    class Meta:
        verbose_name = "Backup-Datei"
        verbose_name_plural = "Backup-Dateien"

    def __str__(self):
        return self.file_name


class BackupLog(models.Model):
    LEVEL_CHOICES = [
        ("info", "Info"),
        ("warning", "Warnung"),
        ("error", "Fehler"),
        ("debug", "Debug"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="logs", verbose_name="Client")
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default="info", verbose_name="Level")
    message = models.TextField(verbose_name="Nachricht")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Erstellt")

    class Meta:
        verbose_name = "Log-Eintrag"
        verbose_name_plural = "Log-Einträge"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_level_display()}] {self.client.name}: {self.message[:50]}"


class BackupSchedule(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="schedules", verbose_name="Client")
    interval_minutes = models.IntegerField(default=60, verbose_name="Intervall (Minuten)")
    paths = models.TextField(default="C:\\Users", verbose_name="Zu sichernde Pfade")
    exclude_patterns = models.TextField(blank=True, verbose_name="Ausgeschlossene Muster")
    is_active = models.BooleanField(default=True, verbose_name="Aktiv")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Backup-Plan"
        verbose_name_plural = "Backup-Pläne"

    def __str__(self):
        return f"Plan: {self.client.name} (alle {self.interval_minutes} Min)"


class CompanySettings(models.Model):
    company_name = models.CharField(max_length=255, default="Mein Unternehmen", verbose_name="Firmenname")
    backup_retention_days = models.IntegerField(default=5, verbose_name="Aufbewahrungsdauer (Tage)")
    max_file_size_mb = models.IntegerField(default=500, verbose_name="Max. Dateigröße (MB)")
    notify_on_failure = models.BooleanField(default=True, verbose_name="Bei Fehlern benachrichtigen")
    notification_email = models.EmailField(blank=True, verbose_name="Benachrichtigungs-E-Mail")
    storage_limit_gb = models.IntegerField(default=10, verbose_name="Speicherlimit (GB)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Unternehmenseinstellung"
        verbose_name_plural = "Unternehmenseinstellungen"

    def __str__(self):
        return f"Einstellungen: {self.company_name}"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
