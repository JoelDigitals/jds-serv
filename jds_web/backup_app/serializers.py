from rest_framework import serializers
from .models import Client, BackupJob, BackupFile, BackupLog, BackupSchedule, CompanySettings


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name", "machine_id", "api_token", "operating_system",
                  "last_seen", "is_active", "max_backups", "notes", "created_at"]
        read_only_fields = ["api_token", "created_at"]


class ClientRegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    machine_id = serializers.CharField(max_length=255)
    operating_system = serializers.CharField(max_length=100, required=False, default="")


class BackupJobSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)

    class Meta:
        model = BackupJob
        fields = ["id", "client", "client_name", "status", "total_files",
                  "total_size", "transferred_size", "error_message",
                  "started_at", "completed_at"]


class BackupFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupFile
        fields = ["id", "backup_job", "file_path", "file_name", "file_size",
                  "file_hash", "storage_path", "is_directory", "created_at"]


class BackupLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupLog
        fields = ["id", "client", "level", "message", "created_at"]


class BackupScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BackupSchedule
        fields = ["id", "client", "interval_minutes", "paths",
                  "exclude_patterns", "is_active", "created_at"]


class CompanySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySettings
        fields = "__all__"
