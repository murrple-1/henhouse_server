import binascii
import os
from typing import Any

# TODO replace with regular `uuid` module when finalized in Python
import uuid_extensions
from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager["User"]):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    uuid = models.UUIDField(primary_key=True, default=uuid_extensions.uuid7)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=64, unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    attributes = models.JSONField(null=False, blank=True, default=dict)

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()


def generate_token_key() -> str:
    return binascii.hexlify(os.urandom(20)).decode()


class Token(models.Model):
    key = models.CharField(primary_key=True, max_length=64, default=generate_token_key)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="tokens", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args: Any, **kwargs: Any):
        if not self.key:
            self.key = generate_token_key()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.key
