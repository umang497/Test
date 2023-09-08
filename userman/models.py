from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import (
    PermissionsMixin,
    UserManager,
)
from django.db import models
from reversion import revisions as reversion

from utils.models import BaseUUIDModel
from utils.validators import validate_spaced_alphanumeric, validate_alphanumeric


class UserLevel(models.TextChoices):
    REGULAR = ("REGULAR", "REGULAR")
    ADMIN = ("ADMIN", "ADMIN")
    BANNED = ("BANNED", "BANNED")


class User(BaseUUIDModel, AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['phone_number', 'name', 'email']

    username = models.CharField(max_length=20, unique=True, validators=[validate_alphanumeric])

    # We can add verified flag to check if phone number is OTP verified or not.
    phone_number = models.CharField(max_length=10)
    email = models.EmailField(null=True, blank=True)
    name = models.CharField(max_length=64, validators=[validate_spaced_alphanumeric])

    user_level = models.CharField(max_length=20, choices=UserLevel.choices, default=UserLevel.REGULAR)

    # Just for admin access
    is_staff = models.BooleanField(default=False)


reversion.register(User)
