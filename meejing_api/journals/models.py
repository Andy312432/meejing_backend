from __future__ import annotations

from typing import Iterable, Optional

from django.conf import settings
from django.db import models
from django.db.models import Exists, OuterRef, Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedUUIDModel, VisibilityChoices

User = settings.AUTH_USER_MODEL


def journal_media_upload_to(instance: "JournalMedia", filename: str) -> str:
    """Deterministic upload path per journal entry."""
    entry_uuid = instance.entry.uuid if instance.entry_id else "unassigned"
    return f"journals/{entry_uuid}/media/{filename}"


def journal_cover_upload_to(instance: "JournalEntry", filename: str) -> str:
    """Upload path for journal cover images."""
    return f"journals/{instance.uuid}/cover/{filename}"


class Location(TimeStampedUUIDModel):
    """Represents a point of interest or custom location on the map."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    formatted_address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    country_code = models.CharField(max_length=3, blank=True)
    administrative_area = models.CharField(max_length=120, blank=True)
    locality = models.CharField(max_length=120, blank=True)
    place_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_("External provider identifier (such as Apple Maps or Google)."),
    )
    created_by = models.ForeignKey(
        User,
        related_name="locations",
        on_delete=models.CASCADE,
    )
    is_verified = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=("latitude", "longitude"), name="location_lat_lon_idx"),
            models.Index(fields=("created_by",)),
        ]
        unique_together = (
            "created_by",
            "name",
            "latitude",
            "longitude",
        )
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    def __str__(self) -> str:
        return f"{self.name} ({self.latitude}, {self.longitude})"


class JournalTag(TimeStampedUUIDModel):
    """User-defined tag to group journal entries by theme or activity."""

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    description = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="created_tags",
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ("name",)

    def save(self, *args, **kwargs) -> None:  # type: ignore[override]
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class JournalEntryQuerySet(models.QuerySet):
    def visible_to(self, user: Optional["User"]) -> "JournalEntryQuerySet":
        """Limit entries so the viewer only receives content they can access."""
        if not user or not getattr(user, "is_authenticated", False):
            return self.filter(visibility=VisibilityChoices.PUBLIC)

        from social.models import Follow  # late import to avoid circular dependency

        friend_qs = Follow.objects.filter(
            follower=user,
            following=OuterRef("author"),
            status=Follow.Status.ACCEPTED,
        )

        return self.filter(
            Q(author=user)
            | Q(visibility=VisibilityChoices.PUBLIC)
            | (Q(visibility=VisibilityChoices.FRIENDS) & Exists(friend_qs))
        )

    def for_author(self, user: "User") -> "JournalEntryQuerySet":
        return self.filter(author=user)

    def with_tags(self, tags: Iterable[str]) -> "JournalEntryQuerySet":
        if not tags:
            return self
        return self.filter(tags__slug__in=tags).distinct()


class JournalEntry(TimeStampedUUIDModel):
    """Primary content unit representing a story pinned to a map location."""

    class Mood(models.TextChoices):
        HAPPY = "happy", _("Happy")
        RELAXED = "relaxed", _("Relaxed")
        ADVENTUROUS = "adventurous", _("Adventurous")
        ROMANTIC = "romantic", _("Romantic")
        CALM = "calm", _("Calm")
        REFLECTIVE = "reflective", _("Reflective")
        MIXED = "mixed", _("Mixed")
        CUSTOM = "custom", _("Custom")

    author = models.ForeignKey(
        User,
        related_name="journal_entries",
        on_delete=models.CASCADE,
    )
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    location = models.ForeignKey(
        Location,
        related_name="entries",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text=_("Latitude snapshot for quick map rendering."),
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        help_text=_("Longitude snapshot for quick map rendering."),
    )
    visit_started_at = models.DateTimeField(null=True, blank=True)
    visit_ended_at = models.DateTimeField(null=True, blank=True)
    visibility = models.CharField(
        max_length=16,
        choices=VisibilityChoices.choices,
        default=VisibilityChoices.PRIVATE,
    )
    mood = models.CharField(
        max_length=20,
        choices=Mood.choices,
        blank=True,
    )
    mood_custom = models.CharField(max_length=60, blank=True)
    allow_comments = models.BooleanField(default=True)
    is_draft = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    cover_image = models.ImageField(upload_to=journal_cover_upload_to, blank=True, null=True)
    tags = models.ManyToManyField(JournalTag, blank=True, related_name="entries")
    metadata = models.JSONField(
        blank=True,
        default=dict,
        help_text=_("Arbitrary structured data (weather, companions, expenses, etc.)."),
    )
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)
    bookmark_count = models.PositiveIntegerField(default=0)

    objects = JournalEntryQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=("author", "visibility"), name="entry_author_visibility_idx"),
            models.Index(fields=("latitude", "longitude"), name="entry_lat_lon_idx"),
            models.Index(fields=("published_at",)),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.title} @ {self.latitude}, {self.longitude}"

    @property
    def mood_label(self) -> str:
        if self.mood == self.Mood.CUSTOM and self.mood_custom:
            return self.mood_custom
        return self.get_mood_display()


class JournalMedia(TimeStampedUUIDModel):
    """Additional media attached to a journal entry (photos, videos, audio)."""

    class MediaType(models.TextChoices):
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        AUDIO = "audio", _("Audio")

    entry = models.ForeignKey(
        JournalEntry,
        related_name="media",
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to=journal_media_upload_to)
    media_type = models.CharField(
        max_length=10,
        choices=MediaType.choices,
        default=MediaType.IMAGE,
    )
    caption = models.CharField(max_length=255, blank=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("position", "created_at")

    def __str__(self) -> str:
        return f"{self.media_type} for {self.entry_id}"
