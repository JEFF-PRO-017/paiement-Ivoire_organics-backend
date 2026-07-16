from django.urls import path
from .views import ParametreUpdateView

app_name = 'front_settings'

urlpatterns = [
    path('settings/', ParametreUpdateView.as_view(), name='parametre-update'),
]