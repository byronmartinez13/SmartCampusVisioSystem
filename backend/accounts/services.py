import logging
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError
from .models import User
from .serializers import check_password

logger = logging.getLogger(__name__)


def register_user(data):
    try:
        with transaction.atomic():
            return User.objects.create_user(**data)
    except IntegrityError as exc:
        raise ValidationError({"email": "Ya existe una cuenta con este correo."}) from exc


def request_password_reset(email):
    user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if user is None:
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    url = f"{settings.FRONTEND_URL}/restablecer?uid={uid}&token={token}"
    try:
        send_mail(
            "Restablecer contraseña · Smart Campus Vision",
            f"Para crear una nueva contraseña, abre este enlace:\n\n{url}\n\n"
            "El enlace caduca en una hora y solo puede usarse una vez.\n"
            "Si no solicitaste este cambio, puedes ignorar este mensaje.",
            settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False,
        )
    except Exception:
        # Do not disclose whether the account exists, or include tokens in logs.
        logger.error("No se pudo enviar un correo de recuperación.")


@transaction.atomic
def reset_password(data):
    try:
        user_id = force_str(urlsafe_base64_decode(data["uid"]))
        user = User.objects.select_for_update().get(pk=user_id, is_active=True)
    except (ValueError, TypeError, OverflowError, UnicodeDecodeError, User.DoesNotExist):
        raise ValidationError({"detail": "El enlace no es válido o ha caducado."})
    if not default_token_generator.check_token(user, data["token"]):
        raise ValidationError({"detail": "El enlace no es válido o ha caducado."})
    check_password(data["password"], user)
    user.set_password(data["password"])
    user.save(update_fields=["password"])
