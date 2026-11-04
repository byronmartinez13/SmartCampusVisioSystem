from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from . import serializers, services
from .models import User
from .permissions import IsAdministrator


@method_decorator(csrf_protect, name="dispatch")
class CsrfProtectedView(APIView):
    """Protect anonymous POST endpoints too, not only authenticated sessions."""


class CsrfView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class RegisterView(CsrfProtectedView):
    permission_classes = [AllowAny]
    throttle_scope = "register"

    def post(self, request):
        serializer = serializers.RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register_user(serializer.validated_data)
        login(request, user)
        return Response(serializers.UserSerializer(user).data, status=201)


class LoginView(CsrfProtectedView):
    permission_classes = [AllowAny]
    throttle_scope = "login"

    def post(self, request):
        serializer = serializers.LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = authenticate(request, email=data["email"].strip().lower(), password=data["password"])
        if user is None:
            return Response({"detail": "Correo o contraseña incorrectos."}, status=400)
        login(request, user)
        return Response(serializers.UserSerializer(user).data)


class LogoutView(CsrfProtectedView):
    def post(self, request):
        logout(request)
        return Response(status=204)


class MeView(CsrfProtectedView):
    def get(self, request):
        return Response(serializers.UserSerializer(request.user).data)

    def patch(self, request):
        serializer = serializers.ProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.name = serializer.validated_data["name"]
        request.user.save(update_fields=["name"])
        return Response(serializers.UserSerializer(request.user).data)


class RecoveryView(CsrfProtectedView):
    permission_classes = [AllowAny]
    throttle_scope = "recovery"

    def post(self, request):
        serializer = serializers.RecoverySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.request_password_reset(serializer.validated_data["email"])
        return Response({"detail": "Si existe una cuenta con ese correo, recibirás un enlace de recuperación."})


class ResetView(CsrfProtectedView):
    permission_classes = [AllowAny]
    throttle_scope = "recovery"

    def post(self, request):
        serializer = serializers.ResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.reset_password(serializer.validated_data)
        return Response({"detail": "Contraseña actualizada. Ya puedes iniciar sesión."})


class ChangePasswordView(CsrfProtectedView):
    def post(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if not request.user.check_password(data["current_password"]):
            return Response({"current_password": ["La contraseña actual no es correcta."]}, status=400)
        serializers.check_password(data["password"], request.user)
        request.user.set_password(data["password"])
        request.user.save(update_fields=["password"])
        update_session_auth_hash(request, request.user)
        return Response({"detail": "Contraseña actualizada."})


class UserListView(APIView):
    permission_classes = [IsAdministrator]

    def get(self, request):
        return Response(serializers.UserSerializer(User.objects.order_by("id"), many=True).data)


class UserAccessView(APIView):
    permission_classes = [IsAdministrator]

    def patch(self, request, pk):
        from django.db import transaction
        from django.shortcuts import get_object_or_404
        from rest_framework import serializers as drf
        from campus.models import AdministrativeEvent
        from campus.scheduling_services import lock_schedule
        class Access(drf.Serializer):
            role = drf.ChoiceField(choices=User.Role.choices)
            is_active = drf.BooleanField()
            note = drf.CharField(min_length=5, max_length=500)
        data = Access(data=request.data)
        data.is_valid(raise_exception=True)
        with transaction.atomic():
            lock_schedule()
            target = get_object_or_404(User, pk=pk)
            if target.pk == request.user.pk:
                raise drf.ValidationError('Otro administrador debe cambiar tus permisos; no puedes modificar tu propio acceso.')
            if target.is_superuser:
                raise drf.ValidationError('Las cuentas superusuario se administran mediante las herramientas de Django.')
            before = {'role': target.role, 'is_active': target.is_active}
            target.role = data.validated_data['role']
            target.is_active = data.validated_data['is_active']
            target.save(update_fields=['role', 'is_active'])
            AdministrativeEvent.objects.create(actor=request.user, action='user.access', target=str(target.pk), before=before,
                after={'role': target.role, 'is_active': target.is_active, 'note': data.validated_data['note']})
        return Response(serializers.UserSerializer(target).data)
