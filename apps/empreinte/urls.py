from django.urls import path
from .views import verify_view

urlpatterns = [
    path('verify/', verify_view, name='empreinte-verify'),
]
