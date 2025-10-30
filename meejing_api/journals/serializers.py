from __future__ import annotations

from typing import Iterable, List, Optional

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserPublicSerializer
from .models import JournalEntry, JournalMedia, JournalTag, Location


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = [
            "id",
            "uuid",
            "name",
            "description",
            "formatted_address",
            "latitude",
            "longitude",
            "country_code",
            "administrative_area",
            "locality",
            "place_id",
            "is_verified",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "is_verified", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context["request"]
        return Location.objects.create(created_by=request.user, **validated_data)


class JournalTagSerializer(serializers.ModelSerializer):
    created_by = UserPublicSerializer(read_only=True)

    class Meta:
        model = JournalTag
        fields = ["id", "uuid", "name", "slug", "description", "created_at", "created_by"]
        read_only_fields = ["id", "uuid", "slug", "created_at", "created_by"]


class JournalMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = JournalMedia
        fields = [
            "id",
            "uuid",
            "file",
            "media_type",
            "caption",
            "position",
            "created_at",
        ]
        read_only_fields = ["id", "uuid", "created_at"]


class JournalEntryMapSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    tags = JournalTagSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "uuid",
            "title",
            "summary",
            "latitude",
            "longitude",
            "visibility",
            "author",
            "tags",
            "published_at",
        ]


class JournalEntrySerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="location",
        write_only=True,
        allow_null=True,
        required=False,
    )
    media = JournalMediaSerializer(many=True, required=False)
    tags = JournalTagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=60),
        required=False,
        write_only=True,
    )

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "uuid",
            "author",
            "title",
            "summary",
            "body",
            "location",
            "location_id",
            "latitude",
            "longitude",
            "visit_started_at",
            "visit_ended_at",
            "visibility",
            "mood",
            "mood_custom",
            "allow_comments",
            "is_draft",
            "published_at",
            "cover_image",
            "metadata",
            "tags",
            "tag_names",
            "media",
            "like_count",
            "comment_count",
            "bookmark_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "author",
            "like_count",
            "comment_count",
            "bookmark_count",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        mood = attrs.get("mood", getattr(self.instance, "mood", ""))
        mood_custom = attrs.get("mood_custom")
        if mood == JournalEntry.Mood.CUSTOM and not mood_custom:
            raise serializers.ValidationError(
                {"mood_custom": "Custom mood entries must include a mood_custom label."}
            )
        return attrs

    def _sync_tags(self, entry: JournalEntry, tag_names: Iterable[str]) -> None:
        clean_names = {
            name.strip() for name in tag_names if name and name.strip()
        }
        if not clean_names:
            entry.tags.clear()
            return

        tags: List[JournalTag] = []
        request_user = self.context["request"].user
        for name in clean_names:
            tag, _created = JournalTag.objects.get_or_create(
                name=name,
                defaults={"created_by": request_user},
            )
            tags.append(tag)
        entry.tags.set(tags)

    def _sync_media(self, entry: JournalEntry, media_payload: Optional[List[dict]]) -> None:
        if media_payload is None:
            return
        entry.media.all().delete()
        media_objects = [
            JournalMedia(entry=entry, **item) for item in media_payload
        ]
        JournalMedia.objects.bulk_create(media_objects)

    @transaction.atomic
    def create(self, validated_data):
        media_payload = validated_data.pop("media", [])
        tag_names = validated_data.pop("tag_names", [])
        request = self.context["request"]

        if not validated_data.get("is_draft") and not validated_data.get("published_at"):
            validated_data["published_at"] = timezone.now()

        entry = JournalEntry.objects.create(author=request.user, **validated_data)
        if tag_names:
            self._sync_tags(entry, tag_names)
        if media_payload:
            self._sync_media(entry, media_payload)
        return entry

    @transaction.atomic
    def update(self, instance, validated_data):
        media_payload = validated_data.pop("media", None)
        tag_names = validated_data.pop("tag_names", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if not instance.is_draft and not instance.published_at:
            instance.published_at = timezone.now()

        instance.save()

        if tag_names is not None:
            self._sync_tags(instance, tag_names)
        if media_payload is not None:
            self._sync_media(instance, media_payload)
        return instance


class JournalEntrySummarySerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    tags = JournalTagSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = [
            "id",
            "uuid",
            "title",
            "summary",
            "visibility",
            "author",
            "tags",
            "published_at",
            "created_at",
        ]
