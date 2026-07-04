from datetime import datetime, timezone

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.front_settings.serializers import ParametreSerializer
from .models import CustomUser


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs["email"],
            password=attrs["password"],
        )

        if user is None:
            raise serializers.ValidationError("Identifiants incorrects")

        if not user.is_active:
            raise serializers.ValidationError("Compte désactivé")

        attrs["user"] = user
        return attrs


class AuthUserSerializer(serializers.ModelSerializer):
    sites = serializers.StringRelatedField(many=True)
    accessToken = serializers.SerializerMethodField()
    refreshToken = serializers.SerializerMethodField()
    expirationTime = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "sites",
            "accessToken",
            "refreshToken",
            "expirationTime",
        )

    def _refresh(self, obj):
        if not hasattr(self, "_cached_refresh"):
            self._cached_refresh = RefreshToken.for_user(obj)
        return self._cached_refresh

    def get_accessToken(self, obj):
        return str(self._refresh(obj).access_token)

    def get_refreshToken(self, obj):
        return str(self._refresh(obj))

    def get_expirationTime(self, obj):
        exp = self._refresh(obj).access_token["exp"]
        return datetime.fromtimestamp(exp, tz=timezone.utc).isoformat()


class CustomUserSerializer(serializers.ModelSerializer):
    auth = serializers.SerializerMethodField()
    setting = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "auth",
            "setting",
        )

    def get_auth(self, obj):
        return AuthUserSerializer(obj).data

    def get_setting(self, obj):
        if hasattr(obj, "parametre"):
            return ParametreSerializer(obj.parametre).data
        return None