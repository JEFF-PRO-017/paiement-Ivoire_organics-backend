from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError, NotFound, PermissionDenied, AuthenticationFailed
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # --- Exceptions gérées nativement par DRF ---
    if response is not None:
        message = "Une erreur est survenue"
        errors = response.data

        if isinstance(exc, ValidationError):
            message = "Erreur de validation"
        elif isinstance(exc, (NotFound, Http404)):
            message = "Ressource introuvable"
            errors = None
        elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
            message = "Permission refusée"
            errors = None
        elif isinstance(exc, AuthenticationFailed):
            message = "Authentification échouée"
            errors = None
        elif isinstance(response.data, dict) and "detail" in response.data:
            message = str(response.data["detail"])
            errors = None

        response.data = {
            "success": False,
            "message": message,
            "data": None,
            "errors": errors,
            "code": exc.__class__.__name__.upper(),
        }
        return response

    # --- Exceptions non gérées par DRF (ValueError, TokenError, bug 500...) ---
    if isinstance(exc, TokenError):
        return Response({
            "success": False,
            "message": "Token invalide ou expiré",
            "data": None,
            "errors": str(exc),
            "code": "TOKEN_ERROR"
        }, status=401)

    if isinstance(exc, ValueError):
        return Response({
            "success": False,
            "message": str(exc),
            "data": None,
            "errors": None,
            "code": "VALUE_ERROR"
        }, status=400)

    # Fallback : erreur 500 générique
    return Response({
        "success": False,
        "message": "Erreur interne du serveur",
        "data": None,
        "errors": str(exc),
        "code": "SERVER_ERROR"
    }, status=500)