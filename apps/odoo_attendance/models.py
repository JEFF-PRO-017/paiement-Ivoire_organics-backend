from django.db import models

class Attendance(models.Model):
    employee_id = models.CharField(max_length=20)
    employee_name = models.CharField(max_length=150, null=True, blank=True)  # Optionnel, pour affichage dans l'admin
    action      = models.CharField(max_length=10)  # sign_in / sign_out
    name        = models.DateTimeField()           # timestamp de l'action
    worked_hours = models.FloatField(null=True)    # durée du shift (calculé par Odoo)
    oodo_attendance_id = models.CharField(max_length=50, unique=True,null=True,blank=True)  # ID d'Odoo pour éviter les doublons


    class Meta:
        db_table = 'odoo_attendance'

    def __str__(self):
        return f"Attendance {self.employee_id} - {self.action} at {self.name}"