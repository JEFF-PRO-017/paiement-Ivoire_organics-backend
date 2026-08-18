from django.contrib import admin
from .models import Parametre 

@admin.register(Parametre)
class ParametreAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'site', 'zoom','mode',)
    search_fields = ('user', 'site',)
    list_filter = ('site', 'mode',)
    ordering = ('user',)