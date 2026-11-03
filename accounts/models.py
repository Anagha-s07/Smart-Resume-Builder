from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    ROLE_CHOICES = (
        ('user', 'User'),
        ('company', 'Company'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    company_name = models.CharField(
        max_length=150,
        blank=True
    )

    company_description = models.TextField(
        blank=True
    )

    def __str__(self):
        return self.user.username