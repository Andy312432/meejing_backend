from django.conf import settings
from django.db import models

from core.models import TimeStampedUUIDModel, VisibilityChoices

User = settings.AUTH_USER_MODEL


class Place(TimeStampedUUIDModel):
    """Represents a location that can host user posts."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    visibility = models.CharField(
        max_length=16,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PUBLIC,
    )
    created_by = models.ForeignKey(
        User,
        related_name="places",
        on_delete=models.CASCADE,
    )
    metadata = models.JSONField(blank=True, default=dict)

    class Meta:
        indexes = [
            models.Index(fields=("visibility",)),
            models.Index(fields=("created_by",)),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.name} ({self.latitude}, {self.longitude})"


class Post(TimeStampedUUIDModel):
    """Content authored by users and attached to a place."""

    place = models.ForeignKey(
        Place,
        related_name="posts",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name="posts",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    visibility = models.CharField(
        max_length=16,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PUBLIC,
    )

    class Meta:
        indexes = [
            models.Index(fields=("visibility",)),
            models.Index(fields=("place", "visibility")),
            models.Index(fields=("author",)),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} @ {self.place.name}"

