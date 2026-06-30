from django.urls import path
from .views import load_all_employees, load_all_attendances

urlpatterns = [
    path("load-employees/", load_all_employees, name="load-employees"),
    path("load-attendances/", load_all_attendances, name="load-attendances"),
]