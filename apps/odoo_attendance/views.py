from apps.odoo_attendance.scheduler import _task_load_all_employees, _task_load_all_attendances
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

from core.response import ApiResponse


@api_view(["POST"])
@permission_classes([IsAdminUser])
def load_all_employees(request):
    # les exceptions sont maintenant interceptées par custom_exception_handler
    _task_load_all_employees()
    return ApiResponse.success(message="Employés chargés avec succès.")


@api_view(["POST"])
@permission_classes([IsAdminUser])
def load_all_attendances(request):
    days = request.data.get("days_initial_attendance", 1)

    if not isinstance(days, int) or days <= 0:
        return ApiResponse.error(
            message="Le nombre de jours doit être un entier positif.",
            errors={"days_initial_attendance": ["Doit être un entier positif."]},
            status_code=400,
            code="INVALID_DAYS"
        )

    _task_load_all_attendances(days_initial_attendance=days)
    return ApiResponse.success(message="Présences chargées avec succès.")