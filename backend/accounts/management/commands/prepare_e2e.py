from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help = "Crea exclusivamente cuentas de pruebas en config.e2e."

    def handle(self, *args, **options):
        if settings.SETTINGS_MODULE != "config.e2e":
            raise CommandError("Este comando solo está permitido con --settings=config.e2e.")
        for role in ("admin", "viewer"):
            user, _ = User.objects.get_or_create(email=f"e2e-{role}@example.edu", defaults={"name": f"E2E {role}"})
            user.role = role
            user.is_active = True
            user.set_password("Only-E2E!92741")
            user.save()
        self.stdout.write("Cuentas aisladas de pruebas preparadas.")
        from campus.models import SystemSettings, AssignmentRule
        SystemSettings.objects.update_or_create(pk=1, defaults={
            'confidence': .5, 'auto_save': False, 'auto_pdf': False, 'record_live': False,
            'alerts_enabled': True, 'alert_threshold': 100, 'date_format': 'dmy', 'version': 0})
        AssignmentRule.objects.update(active=False)
        # Explicit synthetic alert fixture, confined to the isolated test database.
        from campus.models import Classroom, Analysis, Alert
        room, _ = Classroom.objects.get_or_create(name="Alerta sintética E2E", defaults={"capacity": 2})
        analysis, _ = Analysis.objects.get_or_create(classroom=room, people=3, capacity=2)
        alert, _ = Alert.objects.get_or_create(analysis=analysis)
        alert.resolved = False
        alert.in_review = False
        alert.save()
