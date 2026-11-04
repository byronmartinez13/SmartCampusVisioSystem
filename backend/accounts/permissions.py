from rest_framework.permissions import BasePermission
from .models import User


class IsAdministrator(BasePermission):
    message = "Solo un administrador puede acceder a esta función."

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and
                    (request.user.is_superuser or request.user.role == User.Role.ADMIN))
