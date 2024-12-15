from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='employee')

    manager_type = models.TextField(
        null=True,
        blank=True,
        help_text="Specify the manager type (e.g., Human Resources, Finance, etc.) if the role is 'manager'."
    )

    # Make email unique
    email = models.EmailField(unique=True)

    class Meta:
        db_table = 'users'

    def clean(self):
        super().clean()

        if self.role == 'manager' and not self.manager_type:
            raise ValidationError("Manager type must be specified for users with the 'manager' role.")

        if self.role != 'manager' and self.manager_type:
            raise ValidationError("Only users with the 'manager' role can have a manager type.")

    def __str__(self):
        return self.username
