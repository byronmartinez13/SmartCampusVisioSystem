from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "role", "role_label", "is_active"]
        read_only_fields = fields


def check_password(password, user=None):
    try:
        validate_password(password, user)
    except DjangoValidationError as exc:
        raise serializers.ValidationError({"password": list(exc.messages)}) from exc


class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)

    def validate(self, attrs):
        attrs["email"] = attrs["email"].strip().lower()
        if User.objects.filter(email__iexact=attrs["email"]).exists():
            raise serializers.ValidationError({"email": "Ya existe una cuenta con este correo."})
        check_password(attrs["password"], User(email=attrs["email"], name=attrs["name"]))
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False, max_length=128)


class RecoverySerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=100)
    token = serializers.CharField(max_length=200)
    password = serializers.CharField(trim_whitespace=False, max_length=128)


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(trim_whitespace=False, max_length=128)
    password = serializers.CharField(trim_whitespace=False, max_length=128)


class ProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=150)
