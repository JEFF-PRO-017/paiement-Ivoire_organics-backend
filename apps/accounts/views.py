from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import CustomUserSerializer, LoginSerializer
from datetime import datetime, timezone
from rest_framework.throttling import AnonRateThrottle 


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        return Response(
            CustomUserSerializer(user).data,
            status=status.HTTP_200_OK,
        )

class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('refreshToken')
        print('token',token)
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
        try:
            refresh_token = request.data.get('refreshToken')
            if not refresh_token:
                return Response({'detail': 'refreshToken requis'}, status=status.HTTP_400_BAD_REQUEST)
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError as e:
            return Response({'detail': 'Token invalide'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'Déconnexion réussie'}, status=status.HTTP_200_OK)




# Intègre ce système d'authentification JWT dans mon app [React/Vue/Angular].

# Endpoints backend :
# - POST /api/auth/login/ → body {email, password} → retourne {accessToken, refreshToken, expirationTime, ...userData}
# - POST /api/auth/refresh/ → body {refreshToken} → retourne {accessToken, expirationTime}
# - POST /api/auth/logout/ → header Authorization: Bearer <access_token>, body {refreshToken}

# Contraintes de sécurité à respecter :
# 1. accessToken : garder en mémoire uniquement (state JS / store), jamais en localStorage/sessionStorage
# 2. refreshToken : stocker en cookie HttpOnly + Secure + SameSite=Strict (nécessite que le backend le pose via Set-Cookie, pas dans le body JSON — signale-moi si je dois adapter le backend pour ça)
# 3. Intercepteur HTTP (axios/fetch wrapper) qui :
#    - ajoute automatiquement le header Authorization sur les requêtes protégées
#    - détecte une 401, tente un refresh silencieux, puis rejoue la requête originale
#    - si le refresh échoue aussi, déconnecte l'utilisateur et redirige vers /login
# 4. Pas de token décodé/lu côté client pour des décisions de sécurité (juste pour affichage UX éventuel)

# Donne-moi le code de l'intercepteur + un hook/context d'auth (useAuth) + la logique de redirection.