from __future__ import annotations

from django.db.models import Q
from rest_framework import decorators, permissions, response, viewsets

from core.models import VisibilityChoices
from .models import Place, Post
from .permissions import IsOwnerOrReadOnly, IsPostOwnerOrReadOnly
from .serializers import PlaceSerializer, PostSerializer


class PlaceViewSet(viewsets.ModelViewSet):
    """CRUD operations for map places."""

    serializer_class = PlaceSerializer
    permission_classes = [IsOwnerOrReadOnly]

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
        url_path=r"by-place/(?P<place_uuid>[0-9a-f-]+)",
        permission_classes=[permissions.AllowAny],
    )
    def by_place(self, request, place_uuid=None, *args, **kwargs):
        """Return posts related to a specific place."""

        queryset = self.get_queryset().filter(place__uuid=place_uuid)
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @decorators.action(
        detail=False,
        methods=["get"],
        url_path=r"by-user/(?P<user_uuid>[0-9a-f-]+)",
        permission_classes=[permissions.AllowAny],
    )
    def by_user(self, request, user_uuid=None, *args, **kwargs):
        """Return posts authored by a specific user."""

        queryset = self.get_queryset().filter(author__uuid=user_uuid)
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

