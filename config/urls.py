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
    path('api/auth/',          include('apps.accounts.urls')),
    path('api/paiements/',      include('apps.paiements.urls')),
    path('api/odoo_attendance/',include('apps.odoo_attendance.urls')),
    path('api/front_settings/',include('apps.front_settings.urls'))
]