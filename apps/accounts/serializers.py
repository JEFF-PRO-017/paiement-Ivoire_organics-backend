from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser


class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Identifiants incorrects')
        if not user.is_active:
            raise serializers.ValidationError('Compte désactivé')
        data['user'] = user
        return data


class AuthUserSerializer(serializers.ModelSerializer):
    sites           = serializers.StringRelatedField(many=True)
    accessToken     = serializers.SerializerMethodField()
    refreshToken    = serializers.SerializerMethodField()
    expirationTime  = serializers.SerializerMethodField()
    first_name      = serializers.CharField()
    last_name       = serializers.CharField()

    class Meta:
        model  = CustomUser
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'email_verified', 'role', 'sites',
            'accessToken', 'refreshToken', 'expirationTime',
        ]

    def get_accessToken(self, obj):
        return str(self._tokens(obj).access_token)

    def get_refreshToken(self, obj):
        return str(self._tokens(obj))

    def get_expirationTime(self, obj):
        from datetime import datetime, timezone
        token = self._tokens(obj).access_token
        return datetime.fromtimestamp(token['exp'], tz=timezone.utc).isoformat()

    def _tokens(self, obj):
        if not hasattr(self, '_refresh'):
            self._refresh = RefreshToken.for_user(obj)
        return self._refresh
