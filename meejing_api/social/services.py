from __future__ import annotations

from typing import Optional, Tuple

from django.contrib.auth import get_user_model

from journals.models import JournalEntry
from .models import Collection, CollectionEntry, Comment, Follow, Like

User = get_user_model()


def are_users_connected(viewer: Optional[User], owner: Optional[User]) -> bool:
    """
    Determine if `viewer` is allowed to see `owner`'s friends-only content.
    We consider the connection valid when the viewer follows the owner with an
    accepted follow relationship.
    """

    if owner is None or viewer is None:
        return False
    if viewer == owner:
        return True
    if not getattr(viewer, "is_authenticated", False):
        return False

    return Follow.objects.filter(
        follower=viewer,
        following=owner,
        status=Follow.Status.ACCEPTED,
    ).exists()


def refresh_entry_engagement(entry_id: int) -> None:
    """Recalculate the cached engagement counters on a JournalEntry."""

    totals = {
        "like_count": Like.objects.filter(entry_id=entry_id).count(),
        "comment_count": Comment.objects.filter(
            entry_id=entry_id, is_deleted=False
        ).count(),
        "bookmark_count": CollectionEntry.objects.filter(entry_id=entry_id).count(),
    }
    JournalEntry.objects.filter(id=entry_id).update(**totals)


def ensure_default_collection(user: User) -> Collection:
    """Ensure the user has a default Favorites collection."""

    collection, _ = Collection.objects.get_or_create(
        owner=user,
        is_default=True,
        defaults={
            "name": "Favorites",
            "description": "Saved journeys and inspiration.",
        },
    )
    return collection

