from __future__ import annotations

from django.db.models import Q
from rest_framework import decorators, permissions, response, viewsets
from rest_framework import status

from core.models import VisibilityChoices
from .models import Place, Post
from .permissions import IsOwnerOrReadOnly, IsPostOwnerOrReadOnly
from .serializers import PlaceSerializer, PostSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    """CRUD operations for map places."""

    serializer_class = PlaceSerializer
    permission_classes = [IsOwnerOrReadOnly]
    parser_classes = viewsets.ModelViewSet.parser_classes

    def get_queryset(self):
        qs = Place.objects.select_related("created_by")
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs.filter(visibility=VisibilityChoices.PUBLIC)
        return qs.filter(
            Q(visibility=VisibilityChoices.PUBLIC) | Q(created_by=user)
        )

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path="public",
        permission_classes=[permissions.AllowAny],
    )
    def public_places(self, request, *args, **kwargs):
        """Return all places marked as public."""

        queryset = Place.objects.filter(visibility=VisibilityChoices.PUBLIC)
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)


class PostViewSet(viewsets.ModelViewSet):
    """Manage posts that belong to places."""

    serializer_class = PostSerializer
    permission_classes = [IsPostOwnerOrReadOnly]

    def get_queryset(self):
        qs = Post.objects.select_related("author", "place", "place__created_by")
        user = self.request.user
        if not user or not user.is_authenticated:
            return qs.filter(
                visibility=VisibilityChoices.PUBLIC,
                place__visibility=VisibilityChoices.PUBLIC,
            )
        return qs.filter(
            Q(visibility=VisibilityChoices.PUBLIC)
            | Q(author=user)
            | Q(place__created_by=user)
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path=r"by-place/(?P<place_id>[0-9a-f-]+)",
        permission_classes=[permissions.AllowAny],
    )
    def by_place(self, request, place_id=None, *args, **kwargs):
        """Return posts related to a specific place."""

        queryset = self.get_queryset().filter(place__id=place_id)
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path=r"by-user/(?P<user_id>[0-9a-f-]+)",
        permission_classes=[permissions.AllowAny],
    )
    def by_user(self, request, user_id=None, *args, **kwargs):
        """Return posts authored by a specific user."""

        queryset = self.get_queryset().filter(author__id=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @decorators.action(
        detail=True,
        methods=["patch"],
        url_path="reaction",
        permission_classes=[permissions.IsAuthenticated],
    )
    def set_reaction(self, request, pk=None, *args, **kwargs):
        """
        Increment like/dislike counters for a post.

        Accepts {"reaction": "like"} or {"reaction": "dislike"} or {"reaction": "clear"}.
        """

        post = self.get_object()
        reaction = request.data.get("reaction")
        if reaction not in {"like", "dislike", "clear"}:
            return response.Response(
                {"detail": "reaction must be one of: like, dislike, clear"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        #FIXME: should we track user?
        if reaction == "like":
            post.like_count += 1
        elif reaction == "dislike":
            post.dislike_count += 1
        elif reaction == "clear":
            # best-effort decrement without tracking per-user
            if post.like_count > 0:
                post.like_count -= 1
            if post.dislike_count > 0:
                post.dislike_count -= 1

        post.save(update_fields=["like_count", "dislike_count", "updated_at"])
        serializer = self.get_serializer(post)
        return response.Response(serializer.data)
