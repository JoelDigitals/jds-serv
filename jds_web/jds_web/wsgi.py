import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jds_web.settings")
django.setup()

from django.core.management import call_command

print("JDS: Führe migrate aus...", flush=True)
try:
    call_command("migrate", "--noinput", verbosity=1)
    print("JDS: migrate abgeschlossen.", flush=True)
except Exception as e:
    print(f"JDS: migrate FEHLER: {e}", flush=True)

print("JDS: Prüfe Admin-User...", flush=True)
try:
    call_command("ensure_admin", verbosity=1)
    print("JDS: Admin-Prüfung abgeschlossen.", flush=True)
except Exception as e:
    print(f"JDS: ensure_admin FEHLER: {e}", flush=True)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
