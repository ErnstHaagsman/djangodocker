from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.conf import settings
from django.utils.crypto import get_random_string


class Todo(models.Model):
    todo_text = models.CharField(max_length=400)
    created_at = models.DateTimeField(auto_now=True)
    done = models.BooleanField(default=False)
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE)

class TodoUserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('Please supply an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # Superusers shouldn't need to verify their email address
        extra_fields['is_confirmed'] = True

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class TodoUser(AbstractBaseUser, PermissionsMixin):
    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = [ 'display_name' ]

    objects = TodoUserManager()

    is_confirmed = models.BooleanField(
        default=False,
        help_text='Has the user verified their email address?'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Does the user have administrative rights?'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Is the user allowed to log in? Disable this instead of '
                  'deleting the account'
    )
    confirmation_code = models.CharField(
        max_length=50,
        help_text='The random-generated code sent to the user for email'
                  'verification',
        default=get_random_string(50),
        unique=True
    )
    email = models.EmailField(
        unique=True,
        primary_key=True
    )
    display_name = models.CharField(
        max_length=200,
        blank=False,
        help_text='The display name for the user, first name or similar'
    )

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.display_name
