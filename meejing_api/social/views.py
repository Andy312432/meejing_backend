from __future__ import annotations

from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter

from journals.models import JournalEntry
from journals.serializers import JournalEntrySummarySerializer
from social.services import ensure_default_collection
from .models import Collection, CollectionEntry, Comment, Follow, Like
from .serializers import (
    CollectionEntrySerializer,
    CollectionSerializer,
    CommentSerializer,
    FollowCreateSerializer,
    FollowSerializer,
    LikeSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Social"],
        summary="List users the current user follows",
        responses=FollowSerializer(many=True),
    ),
    create=extend_schema(
        tags=["Social"],
        summary="Follow a user",
        responses=FollowSerializer,
    ),
    destroy=extend_schema(
        tags=["Social"],
        summary="Unfollow by follow relationship ID",
        responses={204: None},
    ),
)
class FollowViewSet(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Handle follow/unfollow interactions."""

    permission_classes = [permissions.IsAuthenticated]
    queryset = Follow.objects.select_related("follower", "following")

    def get_serializer_class(self):
        if self.action == "create":
            return FollowCreateSerializer
        return FollowSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Follow.objects.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return Follow.objects.none()
        return self.queryset.filter(follower=user)

    def destroy(self, request, *args, **kwargs):
        follow = get_object_or_404(
            Follow,
            pk=kwargs.get("pk"),
            follower=request.user,
        )
        follow.delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Social"],
        summary="List users following the current user",
        responses=FollowSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="followers")
    def followers(self, request, *args, **kwargs):
        qs = Follow.objects.select_related("follower").filter(
            following=request.user,
            status=Follow.Status.ACCEPTED,
        )
        serializer = FollowSerializer(qs, many=True)
        return response.Response(serializer.data)

    @extend_schema(
        tags=["Social"],
        parameters=[
            OpenApiParameter(
                "user_id",
                int,
                OpenApiParameter.PATH,
                description="ID of the user to unfollow",
            )
        ],
        responses={204: None, 404: None},
    )
    @action(detail=False, methods=["delete"], url_path="to/(?P<user_id>[^/.]+)")
    def unfollow_user(self, request, user_id=None, *args, **kwargs):
        deleted, _ = Follow.objects.filter(
            follower=request.user,
            following_id=user_id,
        ).delete()
        if not deleted:
            return response.Response(status=status.HTTP_404_NOT_FOUND)
        return response.Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        tags=["Social"],
        summary="List liked journal entries",
        responses=LikeSerializer(many=True),
    ),
    create=extend_schema(
        tags=["Social"],
        summary="Like a journal entry",
        responses=LikeSerializer,
    ),
    destroy=extend_schema(
        tags=["Social"],
        summary="Remove a like from an entry",
        responses={204: None},
    ),
)
class LikeViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Create/list likes for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LikeSerializer

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Like.objects.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return Like.objects.none()
        qs = Like.objects.filter(user=user).select_related("entry", "entry__author")
        entry_id = self.request.query_params.get("entry")
        if entry_id:
            qs = qs.filter(entry_id=entry_id)
        return qs

    def destroy(self, request, *args, **kwargs):
        entry_id = kwargs.get("pk")
        Like.objects.filter(user=request.user, entry_id=entry_id).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        tags=["Social"],
        summary="List comments",
        responses=CommentSerializer(many=True),
    ),
    retrieve=extend_schema(
        tags=["Social"],
        summary="Retrieve a comment",
        responses=CommentSerializer,
    ),
    create=extend_schema(
        tags=["Social"],
        summary="Create a comment",
        responses=CommentSerializer,
    ),
    update=extend_schema(
        tags=["Social"],
        summary="Update a comment",
        responses=CommentSerializer,
    ),
    partial_update=extend_schema(
        tags=["Social"],
        summary="Partially update a comment",
        responses=CommentSerializer,
    ),
    destroy=extend_schema(
        tags=["Social"],
        summary="Soft delete a comment",
        responses={204: None},
    ),
)
class CommentViewSet(viewsets.ModelViewSet):
    """Manage comments on journal entries."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = CommentSerializer
    filter_backends = [OrderingFilter]
    ordering = ["created_at"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        queryset = Comment.objects.select_related("author", "entry", "parent").prefetch_related("replies")
        entry_id = self.request.query_params.get("entry")
        if entry_id:
            queryset = queryset.filter(entry_id=entry_id, parent__isnull=True)
        return queryset

    def perform_create(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user and comment.entry.author != request.user:
            return response.Response(status=status.HTTP_403_FORBIDDEN)

        comment.is_deleted = True
        comment.body = ""
        comment.edited_at = timezone.now()
        comment.save(update_fields=["is_deleted", "body", "edited_at", "updated_at"])
        return response.Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    list=extend_schema(
        tags=["Social"],
        summary="List collections",
        responses=CollectionSerializer(many=True),
    ),
    retrieve=extend_schema(
        tags=["Social"],
        summary="Retrieve a collection",
        responses=CollectionSerializer,
    ),
    create=extend_schema(
        tags=["Social"],
        summary="Create a collection",
        responses=CollectionSerializer,
    ),
    update=extend_schema(
        tags=["Social"],
        summary="Update a collection",
        responses=CollectionSerializer,
    ),
    partial_update=extend_schema(
        tags=["Social"],
        summary="Partially update a collection",
        responses=CollectionSerializer,
    ),
    destroy=extend_schema(
        tags=["Social"],
        summary="Delete a collection",
        responses={204: None},
    ),
)
class CollectionViewSet(viewsets.ModelViewSet):
    """CRUD for user collections and helper endpoints to manage items."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CollectionSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]
    ordering = ["name"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Collection.objects.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return Collection.objects.none()
        return (
            Collection.objects.filter(owner=user)
            .annotate(entries_count=Count("collection_entries"))
            .prefetch_related("collection_entries")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @extend_schema(
        tags=["Social"],
        summary="Return or create the default Favorites collection",
        responses=CollectionSerializer,
    )
    @action(detail=False, methods=["get"], url_path="favorites")
    def favorites(self, request, *args, **kwargs):
        collection = ensure_default_collection(request.user)
        serializer = self.get_serializer(collection)
        return response.Response(serializer.data)

    @extend_schema(
        tags=["Social"],
        summary="Add an entry to the collection",
        responses=CollectionEntrySerializer,
    )
    @action(detail=True, methods=["post"], url_path="entries")
    def add_entry(self, request, pk=None, *args, **kwargs):
        collection = self.get_object()
        serializer = CollectionEntrySerializer(
            data=request.data,
            context={"collection": collection, "request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Social"],
        parameters=[
            OpenApiParameter(
                "entry_pk",
                int,
                OpenApiParameter.PATH,
                description="ID of the journal entry to remove from the collection",
            )
        ],
        responses={204: None},
    )
    @action(detail=True, methods=["delete"], url_path="entries/(?P<entry_pk>[^/.]+)")
    def remove_entry(self, request, pk=None, entry_pk=None, *args, **kwargs):
        collection = self.get_object()
        CollectionEntry.objects.filter(collection=collection, entry_id=entry_pk).delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Social"],
        summary="List entries saved in the collection",
        responses=JournalEntrySummarySerializer(many=True),
    )
    @action(detail=True, methods=["get"], url_path="entries")
    def list_entries(self, request, pk=None, *args, **kwargs):
        collection = self.get_object()
        entries = (
            JournalEntry.objects.visible_to(request.user)
            .filter(saved_in_collections__collection=collection)
            .select_related("author", "location")
            .prefetch_related("tags")
        )
        serializer = JournalEntrySummarySerializer(entries, many=True)
        return response.Response(serializer.data)
