from django.urls import path
from .views import EmployeListView, EmployeDetailView

urlpatterns = [
    path('',      EmployeListView.as_view(),   name='employe-list'),
    path('<int:pk>/', EmployeDetailView.as_view(), name='employe-detail'),
]
