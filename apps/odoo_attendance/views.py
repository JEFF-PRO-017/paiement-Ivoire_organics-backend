from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

from core.response import ApiResponse
from apps.odoo_attendance.odoo_service import get_all_employees, get_last_days_attendances
from apps.odoo_attendance.services import update_or_create_employees, save_attendances


@api_view(["POST"])
@permission_classes([IsAdminUser])
def load_all_employees(request):
    # les exceptions Odoo (OdooConnectionError, OdooAuthError, OdooDataError)
    # remontent naturellement et sont gérées par custom_exception_handler
    records = get_all_employees()
    update_or_create_employees(records)
    return ApiResponse.success(message=f"{len(records)} employé(s) chargé(s) avec succès.")


@api_view(["POST"])
@permission_classes([IsAdminUser])
def load_all_attendances(request):
    days = request.data.get("days_initial_attendance", 1)

    if not isinstance(days, int) or days <= 0:
        return ApiResponse.error(
            message="Le nombre de jours doit être un entier positif.",
            errors={"days_initial_attendance": ["Doit être un entier positif."]},
            status_code=400,
            code="INVALID_DAYS",
        )

    records = get_last_days_attendances(days_initial_attendance=days)
    save_attendances(records)
    return ApiResponse.success(message=f"{len(records)} présence(s) chargée(s) avec succès.")