import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class VisibilityChoices(models.TextChoices):
    PRIVATE = "private", _("Private")
    FRIENDS = "friends", _("Friends")
    PUBLIC = "public", _("Public")


class TimeStampedModel(models.Model):
    """Abstract model that tracks creation and update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class UUIDModel(models.Model):
    """Abstract model that adds a UUID primary identifier alongside numeric IDs."""

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        abstract = True


class TimeStampedUUIDModel(TimeStampedModel, UUIDModel):
    """Convenience mixin pairing timestamps and UUIDs."""

    class Meta:
        abstract = True
