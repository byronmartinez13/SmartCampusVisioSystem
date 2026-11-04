from rest_framework.permissions import SAFE_METHODS
from accounts.permissions import IsAdministrator


class ReadOrAdmin(IsAdministrator):
    """All signed-in roles may consult; only administrators manage master data."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user.is_authenticated)
        return super().has_permission(request, view)
