from __future__ import annotations

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import CollectionEntry, Comment, Like
from .services import refresh_entry_engagement


@receiver([post_save, post_delete], sender=Like)
def update_entry_likes(sender, instance: Like, **kwargs):
    refresh_entry_engagement(instance.entry_id)


@receiver([post_save, post_delete], sender=CollectionEntry)
def update_entry_bookmarks(sender, instance: CollectionEntry, **kwargs):
    refresh_entry_engagement(instance.entry_id)


@receiver([post_save, post_delete], sender=Comment)
def update_entry_comments(sender, instance: Comment, **kwargs):
    refresh_entry_engagement(instance.entry_id)

