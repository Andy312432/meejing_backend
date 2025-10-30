from __future__ import annotations

from typing import List, Optional

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserPublicSerializer
from core.models import VisibilityChoices
from journals.models import JournalEntry
from social.services import are_users_connected, ensure_default_collection
from .models import Collection, CollectionEntry, Comment, Follow, Like


class FollowSerializer(serializers.ModelSerializer):
    follower = UserPublicSerializer(read_only=True)
    following = UserPublicSerializer(read_only=True)

    class Meta:
        model = Follow
        fields = [
            "id",
            "follower",
            "following",
            "status",
            "created_at",
            "updated_at",
            "note",
        ]
        read_only_fields = fields


class FollowCreateSerializer(serializers.ModelSerializer):
    following_id = serializers.PrimaryKeyRelatedField(
        queryset=Follow._meta.get_field("following").remote_field.model.objects.all(),
        source="following",
    )

    class Meta:
        model = Follow
        fields = ["following_id", "note"]

    def validate(self, attrs):
        follower = self.context["request"].user
        following = attrs["following"]
        if follower == following:
            raise serializers.ValidationError("You cannot follow yourself.")
        return attrs

    def create(self, validated_data):
        follower = self.context["request"].user
        follow, _ = Follow.objects.update_or_create(
            follower=follower,
            following=validated_data["following"],
            defaults={"status": Follow.Status.ACCEPTED, "note": validated_data.get("note", "")},
        )
        return follow


class LikeSerializer(serializers.ModelSerializer):
    entry_id = serializers.PrimaryKeyRelatedField(
        queryset=JournalEntry.objects.all(),
        source="entry",
    )

    class Meta:
        model = Like
        fields = ["entry_id"]

    def create(self, validated_data):
        user = self.context["request"].user
        like, _ = Like.objects.get_or_create(user=user, entry=validated_data["entry"])
        return like


class CommentSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    entry_id = serializers.PrimaryKeyRelatedField(
        queryset=JournalEntry.objects.all(),
        source="entry",
    )
    parent_id = serializers.PrimaryKeyRelatedField(
        queryset=Comment.objects.all(),
        source="parent",
        required=False,
        allow_null=True,
    )
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "uuid",
            "entry_id",
            "author",
            "body",
            "parent_id",
            "is_deleted",
            "edited_at",
            "created_at",
            "updated_at",
            "replies",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "author",
            "is_deleted",
            "edited_at",
            "created_at",
            "updated_at",
            "replies",
        ]

    def get_replies(self, obj: Comment) -> List[dict]:
        depth = self.context.get("depth", 1)
        if depth <= 0:
            return []
        serializer = CommentSerializer(
            obj.replies.order_by("created_at"),
            many=True,
            context={**self.context, "depth": depth - 1},
        )
        return serializer.data

    def create(self, validated_data):
        user = self.context["request"].user
        comment = Comment.objects.create(author=user, **validated_data)
        return comment

    def update(self, instance, validated_data):
        if "body" in validated_data:
            instance.body = validated_data["body"]
            instance.edited_at = timezone.now()
        instance.save(update_fields=["body", "edited_at", "updated_at"])
        return instance


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["body"]


class CollectionSerializer(serializers.ModelSerializer):
    owner = UserPublicSerializer(read_only=True)
    entries_count = serializers.IntegerField(source="collection_entries.count", read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id",
            "uuid",
            "name",
            "description",
            "is_default",
            "owner",
            "entries_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "owner", "entries_count", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        if validated_data.get("is_default"):
            ensure_default_collection(user)
            raise serializers.ValidationError("Default collection already exists.")
        return Collection.objects.create(owner=user, **validated_data)


class CollectionEntrySerializer(serializers.ModelSerializer):
    entry_id = serializers.PrimaryKeyRelatedField(
        queryset=JournalEntry.objects.all(),
        source="entry",
    )

    class Meta:
        model = CollectionEntry
        fields = ["id", "entry_id", "note", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        collection: Collection = self.context["collection"]
        entry = validated_data["entry"]
        note = validated_data.get("note", "")
        request = self.context.get("request")

        if request:
            user = request.user
            if entry.visibility == VisibilityChoices.PRIVATE and entry.author != user:
                raise serializers.ValidationError("Private entries can only be saved by the author.")
            if entry.visibility == VisibilityChoices.FRIENDS and not are_users_connected(user, entry.author):
                raise serializers.ValidationError("Friends-only entry cannot be saved without a connection.")

        collection_entry, _ = CollectionEntry.objects.get_or_create(
            collection=collection,
            entry=entry,
            defaults={"note": note},
        )
        if note and collection_entry.note != note:
            collection_entry.note = note
            collection_entry.save(update_fields=["note", "updated_at"])
        return collection_entry
