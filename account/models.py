from uuid6 import uuid7
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager
)


class UserManager(BaseUserManager):
    def create_user(self, github_id, username, email=None, **extra_fields):
        if not github_id:
            raise ValueError("GitHub ID is required")

        email = self.normalize_email(email) if email else None

        user = self.model(
            github_id=github_id,
            username=username,
            email=email,
            **extra_fields
        )
        if not extra_fields.get('password'):
            user.set_unusable_password()
        else:
            user.set_password(extra_fields.get('password'))

        user.save(using=self._db)
        return user

    def create_superuser(self, github_id, username, email=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(github_id, username, email, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        ANALYST = "analyst", "Analyst"

    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)

    github_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    email = models.EmailField(null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ANALYST)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "github_id"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.username or str(self.github_id)