from datetime import datetime, timezone

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken

from core.response import ApiResponse
from .serializers import CustomUserSerializer, LoginSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        return ApiResponse.success(
            data=CustomUserSerializer(user).data,
            message="Connexion réussie"
        )


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('refreshToken')
        if not token:
            return ApiResponse.error(
                message="refreshToken requis",
                errors={"refreshToken": ["Ce champ est requis."]},
                status_code=400,
                code="MISSING_REFRESH_TOKEN"
            )

        # TokenError levée ici est automatiquement interceptée par custom_exception_handler
        refresh = RefreshToken(token)
        access  = refresh.access_token
        exp_dt  = datetime.fromtimestamp(access['exp'], tz=timezone.utc)

        return ApiResponse.success(data={
            'accessToken':    str(access),
            'expirationTime': exp_dt.isoformat(),
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refreshToken')
        if not refresh_token:
            return ApiResponse.error(
                message="refreshToken requis",
                status_code=400,
                code="MISSING_REFRESH_TOKEN"
            )

        token = RefreshToken(refresh_token)
        token.blacklist()

        return ApiResponse.success(message="Déconnexion réussie")