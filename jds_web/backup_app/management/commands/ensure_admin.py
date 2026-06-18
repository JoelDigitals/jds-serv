from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Erstellt einen Superuser falls noch keiner existiert"

    def handle(self, *args, **options):
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Superuser existiert bereits.")
            return

        User.objects.create_superuser(
            username="admin",
            email="admin@jds-serv.local",
            password="admin123"
        )
        self.stdout.write(self.style.SUCCESS(
            "Superuser erstellt: admin / admin123"
        ))
        self.stdout.write(self.style.WARNING(
            "BITTE SOFORT DAS PASSWORT ÄNDERN! -> /admin/"
        ))
