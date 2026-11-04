from django.core.management.base import BaseCommand, CommandError
from accounts.models import User


class Command(BaseCommand):
    help = "Asigna un rol de aplicación a una cuenta existente desde la administración local."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("role", choices=User.Role.values)

    def handle(self, *args, **options):
        try:
            user = User.objects.get(email__iexact=options["email"].strip())
        except User.DoesNotExist as exc:
            raise CommandError("No existe una cuenta con ese correo.") from exc
        user.role = options["role"]
        user.save(update_fields=["role"])
        self.stdout.write(self.style.SUCCESS(f"Rol actualizado: {user.get_role_display()}."))
