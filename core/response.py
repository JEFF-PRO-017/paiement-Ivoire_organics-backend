from rest_framework.response import Response


class ApiResponse:
    @staticmethod
    def success(data=None, message="Succès", status_code=200):
        return Response({
            "success": True,
            "message": message,
            "data": data,
            "errors": None
        }, status=status_code)

    @staticmethod
    def success_paginated(results, pagination_info, message="Succès", status_code=200, extra=None):
        data = {
            "results": results,
            "pagination": pagination_info
        }
        if extra:
            data.update(extra)  # ex: stats globales dans HistoriqueView

        return Response({
            "success": True,
            "message": message,
            "data": data,
            "errors": None
        }, status=status_code)

    @staticmethod
    def error(message="Erreur", errors=None, status_code=400, code=None):
        return Response({
            "success": False,
            "message": message,
            "data": None,
            "errors": errors,
            "code": code
        }, status=status_code)