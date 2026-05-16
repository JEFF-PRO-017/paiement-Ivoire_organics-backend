from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """Seuls les utilisateurs avec role='admin' peuvent accéder."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated
                    and request.user.role == 'admin')

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user and request.user.is_authenticated
        return request.user and request.user.role == 'admin'
