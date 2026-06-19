import os
import django
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jds_web.settings")
django.setup()

from django.core.management import call_command
from django.db.utils import OperationalError

try:
    call_command("migrate", "--noinput", verbosity=0)
except Exception:
    pass

try:
    call_command("ensure_admin", verbosity=0)
except Exception:
    pass

application = get_wsgi_application()
