from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]

    # Ensure role is required and defaults to 'employee'
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username
