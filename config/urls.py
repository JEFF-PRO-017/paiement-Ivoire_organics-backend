from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # ── Reset password (vues Django intégrées) ────────────────────────────────
    path('admin/password_reset/',
         auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('admin/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('admin/password_reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('admin/password_reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    # ── APIs ──────────────────────────────────────────────────────────────────
    path('auth/',          include('apps.accounts.urls')),
    path('employes/',      include('apps.employes.urls')),
    path('portefeuilles/', include('apps.portefeuilles.urls')),
    path('paiement/',      include('apps.dashboard.urls')),
    path('empreinte/',     include('apps.empreinte.urls')),
]