from django.contrib import admin
from .models import Company, UserProfile, Client, BackupJob, BackupFile, BackupLog, BackupSchedule, CompanySettings


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "company"]
    list_filter = ["company"]
    search_fields = ["user__username", "company__name"]


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "machine_id", "is_active", "last_seen", "created_at"]
    list_filter = ["company", "is_active", "created_at"]
    search_fields = ["name", "machine_id", "notes"]
    readonly_fields = ["api_token", "created_at"]
    actions = ["deactivate_clients", "activate_clients"]

    def deactivate_clients(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_clients.short_description = "Ausgewählte Clients deaktivieren"

    def activate_clients(self, request, queryset):
        queryset.update(is_active=True)
    activate_clients.short_description = "Ausgewählte Clients aktivieren"


class BackupFileInline(admin.TabularInline):
    model = BackupFile
    extra = 0
    readonly_fields = ["file_name", "file_size", "file_hash", "created_at"]
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BackupJob)
class BackupJobAdmin(admin.ModelAdmin):
    list_display = ["client", "status", "total_files", "total_size_display", "started_at", "completed_at"]
    list_filter = ["status", "started_at"]
    search_fields = ["client__name", "error_message"]
    readonly_fields = ["started_at", "completed_at"]
    inlines = [BackupFileInline]

    def total_size_display(self, obj):
        if obj.total_size > 1073741824:
            return f"{obj.total_size / 1073741824:.1f} GB"
        elif obj.total_size > 1048576:
            return f"{obj.total_size / 1048576:.1f} MB"
        elif obj.total_size > 1024:
            return f"{obj.total_size / 1024:.1f} KB"
        return f"{obj.total_size} B"
    total_size_display.short_description = "Größe"


@admin.register(BackupFile)
class BackupFileAdmin(admin.ModelAdmin):
    list_display = ["file_name", "backup_job", "file_size", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["file_name", "file_path"]
    readonly_fields = ["file_hash", "storage_path"]


@admin.register(BackupLog)
class BackupLogAdmin(admin.ModelAdmin):
    list_display = ["client", "level", "short_message", "created_at"]
    list_filter = ["level", "created_at"]
    search_fields = ["client__name", "message"]

    def short_message(self, obj):
        return obj.message[:80]
    short_message.short_description = "Nachricht"


@admin.register(BackupSchedule)
class BackupScheduleAdmin(admin.ModelAdmin):
    list_display = ["client", "interval_minutes", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["client__name"]


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ["company_name", "backup_retention_days", "storage_limit_gb"]

    def has_add_permission(self, request):
        if CompanySettings.objects.exists():
            return False
        return True
