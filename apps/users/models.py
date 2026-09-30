from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Password is stored as a hash by AbstractUser (set_password / check_password).
    `date_joined` from AbstractUser plays the role of created_at.
    """

    class Role(models.TextChoices):
        CUSTOMER = 'customer', 'Customer'
        ADMIN = 'admin', 'Admin'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.CUSTOMER)

    objects = UserManager()

    def __str__(self):
        return self.username

    @property
    def is_business_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN
