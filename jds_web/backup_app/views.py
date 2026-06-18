import os
import uuid
import hashlib
from datetime import datetime

from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate
from django.utils import timezone
from django.db.models import Count, Sum, Q, Max
from django.core.paginator import Paginator

from rest_framework import viewsets, status, generics
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Company, UserProfile, Client, BackupJob, BackupFile, BackupLog, BackupSchedule, CompanySettings
from .serializers import (
    ClientSerializer, ClientRegisterSerializer, BackupJobSerializer,
    BackupFileSerializer, BackupLogSerializer, BackupScheduleSerializer,
    CompanySettingsSerializer,
)
from .auth import TokenAuth


def get_client_from_request(request):
    token = request.auth
    if token:
        return Client.objects.get(api_token=token)
    return None


def dashboard(request):
    total_clients = Client.objects.count()
    active_clients = Client.objects.filter(is_active=True).count()
    total_backups = BackupJob.objects.count()
    successful_backups = BackupJob.objects.filter(status="completed").count()
    failed_backups = BackupJob.objects.filter(status="failed").count()
    total_size = BackupJob.objects.aggregate(s=Sum("total_size"))["s"] or 0
    recent_jobs = BackupJob.objects.select_related("client").order_by("-started_at")[:20]
    clients = Client.objects.annotate(
        job_count=Count("backup_jobs"),
        last_backup=Max("backup_jobs__started_at")
    ).order_by("-last_seen")

    context = {
        "total_clients": total_clients,
        "active_clients": active_clients,
        "total_backups": total_backups,
        "successful_backups": successful_backups,
        "failed_backups": failed_backups,
        "total_size_gb": round(total_size / (1024**3), 2),
        "recent_jobs": recent_jobs,
        "clients": clients,
    }
    return render(request, "backup_app/dashboard.html", context)


def client_detail(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    jobs = BackupJob.objects.filter(client=client).order_by("-started_at")[:50]
    logs = BackupLog.objects.filter(client=client).order_by("-created_at")[:30]
    stats = {
        "total": jobs.count(),
        "completed": jobs.filter(status="completed").count(),
        "failed": jobs.filter(status="failed").count(),
        "total_size": sum(j.total_size for j in jobs if j.total_size),
    }
    context = {
        "client": client,
        "jobs": jobs,
        "logs": logs,
        "stats": stats,
    }
    return render(request, "backup_app/client_detail.html", context)


@staff_member_required
def settings_view(request):
    settings_obj = CompanySettings.get_settings()
    if request.method == "POST":
        settings_obj.company_name = request.POST.get("company_name", settings_obj.company_name)
        settings_obj.backup_retention_days = int(request.POST.get("backup_retention_days", 90))
        settings_obj.max_file_size_mb = int(request.POST.get("max_file_size_mb", 500))
        settings_obj.notify_on_failure = request.POST.get("notify_on_failure") == "on"
        settings_obj.notification_email = request.POST.get("notification_email", "")
        settings_obj.storage_limit_gb = int(request.POST.get("storage_limit_gb", 10))
        settings_obj.save()
        return redirect("settings")
    return render(request, "backup_app/settings.html", {"settings": settings_obj})


@api_view(["GET"])
@authentication_classes([TokenAuth])
@permission_classes([IsAuthenticated])
def client_status(request):
    client = get_client_from_request(request)
    if not client:
        return Response({"error": "Unauthorized"}, status=401)
    client.last_seen = timezone.now()
    client.save(update_fields=["last_seen"])

    schedule = BackupSchedule.objects.filter(client=client, is_active=True).first()
    return Response({
        "id": client.id,
        "name": client.name,
        "machine_id": client.machine_id,
        "is_active": client.is_active,
        "max_backups": client.max_backups,
        "schedule": {
            "interval_minutes": schedule.interval_minutes if schedule else 60,
            "paths": schedule.paths.split("\n") if schedule else ["C:\\Users"],
            "exclude_patterns": schedule.exclude_patterns.split("\n") if schedule and schedule.exclude_patterns else [],
        } if schedule else None,
        "server_time": timezone.now().isoformat(),
    })


@api_view(["POST"])
@authentication_classes([TokenAuth])
@permission_classes([IsAuthenticated])
def start_backup(request):
    client = get_client_from_request(request)
    if not client:
        return Response({"error": "Unauthorized"}, status=401)

    active = BackupJob.objects.filter(client=client, status="running").count()
    if active > 0:
        return Response({"error": "Es läuft bereits ein Backup"}, status=409)

    job = BackupJob.objects.create(client=client, status="running")
    return Response({"job_id": job.id, "status": "running"}, status=201)


@api_view(["POST"])
@authentication_classes([TokenAuth])
@permission_classes([IsAuthenticated])
def update_backup(request, job_id):
    client = get_client_from_request(request)
    if not client:
        return Response({"error": "Unauthorized"}, status=401)

    try:
        job = BackupJob.objects.get(id=job_id, client=client)
    except BackupJob.DoesNotExist:
        return Response({"error": "Job nicht gefunden"}, status=404)

    status_val = request.data.get("status")
    if status_val:
        job.status = status_val
        if status_val in ("completed", "failed", "cancelled"):
            job.completed_at = timezone.now()

    if "total_files" in request.data:
        job.total_files = request.data["total_files"]
    if "total_size" in request.data:
        job.total_size = request.data["total_size"]
    if "transferred_size" in request.data:
        job.transferred_size = request.data["transferred_size"]
    if "error_message" in request.data:
        job.error_message = request.data["error_message"]

    job.save()
    return Response({"status": job.status})


@api_view(["POST"])
@authentication_classes([TokenAuth])
@permission_classes([IsAuthenticated])
def upload_file(request, job_id):
    client = get_client_from_request(request)
    if not client:
        return Response({"error": "Unauthorized"}, status=401)

    try:
        job = BackupJob.objects.get(id=job_id, client=client)
    except BackupJob.DoesNotExist:
        return Response({"error": "Job nicht gefunden"}, status=404)

    file = request.FILES.get("file")
    if not file:
        return Response({"error": "Keine Datei hochgeladen"}, status=400)

    file_path = request.data.get("file_path", file.name)
    client_dir = os.path.join(settings.MEDIA_ROOT, "backups", str(client.id), str(job_id))
    os.makedirs(client_dir, exist_ok=True)

    safe_name = f"{uuid.uuid4().hex}_{file.name}"
    storage_path = os.path.join(client_dir, safe_name)

    file_hash = hashlib.sha256()
    with open(storage_path, "wb") as f:
        for chunk in file.chunks():
            f.write(chunk)
            file_hash.update(chunk)

    backup_file = BackupFile.objects.create(
        backup_job=job,
        file_path=file_path,
        file_name=file.name,
        file_size=file.size,
        file_hash=file_hash.hexdigest(),
        storage_path=storage_path,
        is_directory=request.data.get("is_directory") == "true",
    )

    return Response({
        "file_id": backup_file.id,
        "hash": backup_file.file_hash,
        "size": file.size,
    }, status=201)


@api_view(["POST"])
@authentication_classes([TokenAuth])
@permission_classes([IsAuthenticated])
def log_event(request):
    client = get_client_from_request(request)
    if not client:
        return Response({"error": "Unauthorized"}, status=401)

    log = BackupLog.objects.create(
        client=client,
        level=request.data.get("level", "info"),
        message=request.data.get("message", ""),
    )
    return Response({"id": log.id}, status=201)


@api_view(["GET"])
@authentication_classes([TokenAuth])
@permission_classes([IsAuthenticated])
def pending_actions(request):
    client = get_client_from_request(request)
    if not client:
        return Response({"error": "Unauthorized"}, status=401)

    return Response({
        "actions": [],
        "server_time": timezone.now().isoformat(),
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def register_client(request):
    serializer = ClientRegisterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    machine_id = serializer.validated_data["machine_id"]
    existing = Client.objects.filter(machine_id=machine_id).first()
    if existing:
        token = existing.api_token
        if not existing.is_active:
            existing.is_active = True
            existing.save(update_fields=["is_active"])
        return Response({
            "client_id": existing.id,
            "api_token": token,
            "message": "Client bereits registriert (reaktiviert)",
        })

    api_token = uuid.uuid4().hex + uuid.uuid4().hex
    client = Client.objects.create(
        name=serializer.validated_data["name"],
        machine_id=machine_id,
        api_token=api_token,
        operating_system=serializer.validated_data.get("operating_system", ""),
    )

    BackupSchedule.objects.create(client=client)

    return Response({
        "client_id": client.id,
        "api_token": api_token,
        "message": "Client erfolgreich registriert",
    }, status=201)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_metadata(request):
    user = request.user
    is_admin = user.is_staff or user.is_superuser
    
    if not is_admin:
        return Response({"error": "Nur Administratoren können Metadaten exportieren"}, status=403)
        
    company_id = request.GET.get("company_id")
    
    clients = Client.objects.all()
    if hasattr(user, "profile"):
        clients = clients.filter(company=user.profile.company)
    elif company_id:
        clients = clients.filter(company_id=company_id)
        
    metadata = {
        "export_date": timezone.now().isoformat(),
        "exported_by": user.username,
        "clients": []
    }
    
    for client in clients:
        client_data = {
            "id": client.id,
            "name": client.name,
            "machine_id": client.machine_id,
            "operating_system": client.operating_system,
            "last_seen": client.last_seen.isoformat() if client.last_seen else None,
            "created_at": client.created_at.isoformat(),
            "notes": client.notes,
            "is_active": client.is_active,
            "backup_jobs": []
        }
        
        jobs = BackupJob.objects.filter(client=client).order_by("-started_at")
        for job in jobs:
            job_data = {
                "id": job.id,
                "status": job.status,
                "total_files": job.total_files,
                "total_size_bytes": job.total_size,
                "transferred_size_bytes": job.transferred_size,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "files": []
            }
            
            files = BackupFile.objects.filter(backup_job=job)
            for file in files:
                job_data["files"].append({
                    "file_path": file.file_path,
                    "file_name": file.file_name,
                    "file_size": file.file_size,
                    "file_hash_sha256": file.file_hash,
                    "backup_date": file.created_at.isoformat()
                })
            
            client_data["backup_jobs"].append(job_data)
            
        metadata["clients"].append(client_data)
        
    response = JsonResponse(metadata, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = 'attachment; filename="jds_backup_metadata.json"'
    return response


@staff_member_required
def client_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        notes = request.POST.get("notes", "")
        if name:
            api_token = uuid.uuid4().hex + uuid.uuid4().hex
            machine_id = "temp_" + uuid.uuid4().hex[:12]
            
            client = Client.objects.create(
                name=name,
                machine_id=machine_id,
                api_token=api_token,
                notes=notes
            )
            
            if hasattr(request.user, "profile"):
                client.company = request.user.profile.company
                client.save()
                
            BackupSchedule.objects.create(client=client)
            return redirect("dashboard")
            
    return render(request, "backup_app/client_create.html")


@api_view(["POST"])
@permission_classes([AllowAny])
def api_login(request):
    username = request.data.get("username", "")
    password = request.data.get("password", "")
    user = authenticate(request, username=username, password=password)
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        company = None
        if hasattr(user, "profile"):
            company = {"id": user.profile.company.id, "name": user.profile.company.name}
        return Response({
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "company": company,
        })
    return Response({"error": "Ungültige Anmeldedaten"}, status=401)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_list_clients(request):
    user = request.user
    clients = Client.objects.all()
    if hasattr(user, "profile") and user.profile.company:
        clients = clients.filter(company=user.profile.company)

    data = []
    for c in clients:
        data.append({
            "id": c.id,
            "name": c.name,
            "machine_id": c.machine_id,
            "os": c.operating_system,
            "is_active": c.is_active,
            "last_seen": c.last_seen.isoformat() if c.last_seen else None,
            "api_token": c.api_token,
        })
    return Response({"clients": data})
