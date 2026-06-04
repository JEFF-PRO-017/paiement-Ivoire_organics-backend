import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Site(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'sites'

    def __str__(self):
        return self.nom


class CustomUser(AbstractUser):
    ROLE_CHOICES = [('admin', 'Admin'), ('user', 'Utilisateur')]

    email          = models.EmailField(unique=True)
    role           = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email_verified = models.BooleanField(default=False)
    sites          = models.ManyToManyField(Site, blank=True, related_name='users')

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email
