from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import TimeStampedModel, TimeStampedUUIDModel
from journals.models import JournalEntry

User = settings.AUTH_USER_MODEL


class Follow(TimeStampedModel):
    """Represents following relationship between two users."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        ACCEPTED = "accepted", _("Accepted")
        BLOCKED = "blocked", _("Blocked")

    follower = models.ForeignKey(
        User,
        related_name="following",
        on_delete=models.CASCADE,
    )
    following = models.ForeignKey(
        User,
        related_name="followers",
        on_delete=models.CASCADE,
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.ACCEPTED,
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("follower", "following")
        indexes = [
            models.Index(fields=("follower", "status")),
            models.Index(fields=("following", "status")),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F("following")),
                name="prevent_self_follow",
            )
        ]

    def __str__(self) -> str:
        return f"{self.follower_id} -> {self.following_id} ({self.status})"


class Like(TimeStampedModel):
    """Track which users liked which journal entries."""

    user = models.ForeignKey(
        User,
        related_name="likes",
        on_delete=models.CASCADE,
    )
    entry = models.ForeignKey(
        JournalEntry,
        related_name="likes",
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("user", "entry")
        indexes = [
            models.Index(fields=("entry",)),
            models.Index(fields=("user",)),
        ]

    def __str__(self) -> str:
        return f"Like({self.user_id} -> {self.entry_id})"


class Collection(TimeStampedUUIDModel):
    """A curated list of journal entries created by a user."""

    owner = models.ForeignKey(
        User,
        related_name="collections",
        on_delete=models.CASCADE,
    )
    name = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ("owner", "name")
        ordering = ("name",)

    def __str__(self) -> str:
        return f"{self.name} ({self.owner_id})"


class CollectionEntry(TimeStampedModel):
    """Through table between collections and journal entries."""

    collection = models.ForeignKey(
        Collection,
        related_name="collection_entries",
        on_delete=models.CASCADE,
    )
    entry = models.ForeignKey(
        JournalEntry,
        related_name="saved_in_collections",
        on_delete=models.CASCADE,
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = ("collection", "entry")
        indexes = [
            models.Index(fields=("collection",)),
            models.Index(fields=("entry",)),
        ]

    def __str__(self) -> str:
        return f"{self.collection_id} contains {self.entry_id}"


class Comment(TimeStampedUUIDModel):
    """User comment on a journal entry with optional threading."""

    entry = models.ForeignKey(
        JournalEntry,
        related_name="comments",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name="comments",
        on_delete=models.CASCADE,
    )
    body = models.TextField()
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="replies",
        on_delete=models.CASCADE,
    )
    is_deleted = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [
            models.Index(fields=("entry", "created_at")),
            models.Index(fields=("author", "created_at")),
        ]

    def __str__(self) -> str:
        return f"Comment({self.author_id} on {self.entry_id})"
