from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings

from .models import CustomUser, Site


# ── Action : envoyer un lien de reset password ────────────────────────────────

@admin.action(description='🔑 Envoyer un lien de réinitialisation du mot de passe')
def envoyer_reset_password(modeladmin, request, queryset):
    nb_ok  = 0
    nb_err = 0

    for user in queryset:
        if not user.email:
            nb_err += 1
            continue
        try:
            uid   = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            reset_url = (
                f"{request.scheme}://{request.get_host()}"
                f"/admin/password_reset/confirm/{uid}/{token}/"
            )

            send_mail(
                subject='Réinitialisation de votre mot de passe',
                message=(
                    f"Bonjour {user.first_name or user.username},\n\n"
                    f"Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :\n\n"
                    f"{reset_url}\n\n"
                    f"Ce lien est valable 24 heures.\n\n"
                    f"Si vous n'avez pas demandé cette réinitialisation, ignorez cet email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            nb_ok += 1

        except Exception as e:
            modeladmin.message_user(
                request,
                f"Échec pour {user.email} : {e}",
                level=messages.ERROR,
            )
            nb_err += 1

    if nb_ok:
        modeladmin.message_user(
            request,
            f"✅ Lien envoyé à {nb_ok} utilisateur(s).",
            level=messages.SUCCESS,
        )
    if nb_err:
        modeladmin.message_user(
            request,
            f"⚠️ {nb_err} utilisateur(s) ignoré(s) (email manquant ou erreur SMTP).",
            level=messages.WARNING,
        )


# ── Admin CustomUser ──────────────────────────────────────────────────────────

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display  = ('email', 'username', 'role', 'email_verified', 'is_active')
    list_filter   = ('role', 'email_verified', 'is_active')
    ordering      = ('email',)
    actions       = [envoyer_reset_password]

    fieldsets = UserAdmin.fieldsets + (
        ('Rôle & Sites', {'fields': ('role', 'email_verified', 'sites')}),
    )


# ── Admin Site ────────────────────────────────────────────────────────────────

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom',)