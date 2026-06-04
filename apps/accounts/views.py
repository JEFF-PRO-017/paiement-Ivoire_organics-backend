from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import LoginSerializer, AuthUserSerializer
from datetime import datetime, timezone


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = s.validated_data['user']
        return Response(AuthUserSerializer(user).data, status=status.HTTP_200_OK)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('refreshToken')
        if not token:
            return Response({'detail': 'refreshToken requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            refresh = RefreshToken(token)
            access  = refresh.access_token
            exp_dt  = datetime.fromtimestamp(access['exp'], tz=timezone.utc)
            return Response({
                'accessToken':    str(access),
                'expirationTime': exp_dt.isoformat(),
            })
        except TokenError as e:
            return Response({'detail': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Côté front : supprimer le token du sessionStorage
        return Response({'detail': 'Déconnexion réussie'}, status=status.HTTP_200_OK)
