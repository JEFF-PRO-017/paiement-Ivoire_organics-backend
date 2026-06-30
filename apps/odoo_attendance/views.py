from apps.odoo_attendance.scheduler import _task_load_all_employees,_task_load_all_attendances
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

# adapte l'import selon l'emplacement réel de ces fonctions


@api_view(["POST"])  # cette vue accepte seulement les requêtes POST
@permission_classes([IsAdminUser])
def load_all_employees(request):
    try:
        _task_load_all_employees()  # on appelle la fonction qui charge les employés
        return Response({"message": "Employés chargés avec succès."}, status=status.HTTP_200_OK)
    except Exception as e:
        # si une erreur survient, on la renvoie au front
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def load_all_attendances(request):
    try:
        _task_load_all_attendances()  # on appelle la fonction qui charge les présences
        return Response({"message": "Présences chargées avec succès."}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)