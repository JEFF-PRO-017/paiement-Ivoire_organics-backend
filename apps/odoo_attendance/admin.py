from django.contrib import admin
from .models import Attendance

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display  = ('employee_id','employee_name', 'action', 'name', 'worked_hours')
    list_filter   = ('name',)
    search_fields = ('employee_id',)