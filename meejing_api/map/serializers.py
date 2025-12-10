from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.serializers import UserPublicSerializer
from .models import Place, Post

User = get_user_model()


class PlaceSerializer(serializers.ModelSerializer):
    created_by = UserPublicSerializer(read_only=True)

    class Meta:
        model = Place
        fields = [
            "id",
            "uuid",
            "name",
            "description",
            "latitude",
            "longitude",
            "visibility",
            "created_by",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_by", "created_at", "updated_at"]


class PostSerializer(serializers.ModelSerializer):
    author = UserPublicSerializer(read_only=True)
    place = PlaceSerializer(read_only=True)
    place_id = serializers.PrimaryKeyRelatedField(
        queryset=Place.objects.all(),
        source="place",
        write_only=True,
    )
    photo = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "uuid",
            "place",
            "place_id",
            "author",
            "title",
            "body",
            "visibility",
            "created_at",
            "updated_at",
            "photo",
            "like_count",
            "dislike_count",
        ]
        read_only_fields = [
            "id",
            "uuid",
            "author",
            "place",
            "created_at",
            "updated_at",
            "like_count",
            "dislike_count",
        ]
