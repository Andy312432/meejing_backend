import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import VisibilityChoices


def user_avatar_upload_to(instance: "User", filename: str) -> str:
    """Generate a stable upload path for user avatars."""
    return f"avatars/{instance.uuid}/{filename}"


class User(AbstractUser):
    """Custom user model enriched with profile metadata and visibility flags."""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(_("email address"), unique=True)
    display_name = models.CharField(
        max_length=150,
        blank=True,
        help_text=_("Optional name shown on maps and shared journals."),
    )
    avatar = models.ImageField(upload_to=user_avatar_upload_to, blank=True, null=True)
    profile_visibility = models.CharField(
        max_length=16,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PUBLIC,
    )

    def __str__(self) -> str:
        return self.display_name or self.username or self.email
