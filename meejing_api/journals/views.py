from __future__ import annotations

from django.db.models import QuerySet
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import JournalEntry, JournalTag, Location
from .permissions import IsAuthorOrViewerAllowed
from .serializers import (
    JournalEntryMapSerializer,
    JournalEntrySerializer,
    JournalEntrySummarySerializer,
    JournalTagSerializer,
    LocationSerializer,
)


class LocationViewSet(viewsets.ModelViewSet):
    """Manage user-curated map locations."""

    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["country_code", "administrative_area"]
    search_fields = ["name", "formatted_address", "description"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet[Location]:
        if getattr(self, "swagger_fake_view", False):
            return Location.objects.none()
        user = self.request.user
        if not user or not user.is_authenticated:
            return Location.objects.none()
        return Location.objects.filter(created_by=user)


class JournalTagViewSet(viewsets.ModelViewSet):
    """Expose journal tags for discoverability."""

    serializer_class = JournalTagSerializer
    queryset = JournalTag.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def perform_create(self, serializer) -> None:
        serializer.save(created_by=self.request.user)


class JournalEntryViewSet(viewsets.ModelViewSet):
    """CRUD for journal entries with map-friendly endpoints."""

    serializer_class = JournalEntrySerializer
    permission_classes = [IsAuthorOrViewerAllowed]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["visibility", "mood", "tags__slug", "location__place_id"]
    search_fields = ["title", "summary", "body", "location__name", "location__formatted_address"]
    ordering_fields = ["created_at", "published_at", "visit_started_at", "visit_ended_at"]
    ordering = ["-created_at"]

    def get_queryset(self) -> QuerySet[JournalEntry]:
        qs = (
            JournalEntry.objects.select_related("author", "location")
            .prefetch_related("tags", "media")
        )
        qs = qs.visible_to(self.request.user)

        author_id = self.request.query_params.get("author")
        if author_id:
            qs = qs.filter(author_id=author_id)

        tag_slugs = self.request.query_params.getlist("tag")
        if tag_slugs:
            qs = qs.filter(tags__slug__in=tag_slugs).distinct()

        return qs

    def get_serializer_class(self):
        if getattr(self, "action", None) == "map":
            return JournalEntryMapSerializer
        if getattr(self, "action", None) in {"list", "summary"}:
            return JournalEntrySummarySerializer
        return super().get_serializer_class()

    def perform_create(self, serializer) -> None:
        serializer.save()

    def perform_update(self, serializer) -> None:
        serializer.save()

    @decorators.action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="mine",
    )
    def mine(self, request, *args, **kwargs):
        """Return authenticated user's own entries (including drafts)."""
        queryset = (
            JournalEntry.objects.filter(author=request.user)
            .select_related("author", "location")
            .prefetch_related("tags", "media")
        )
        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    @decorators.action(detail=False, methods=["get"], url_path="map")
    def map(self, request, *args, **kwargs):
        """Lightweight payload for plotting entries on the map."""
        queryset = self.filter_queryset(self.get_queryset())

        lat_min = request.query_params.get("lat_min")
        lat_max = request.query_params.get("lat_max")
        lon_min = request.query_params.get("lon_min")
        lon_max = request.query_params.get("lon_max")

        if all([lat_min, lat_max, lon_min, lon_max]):
            queryset = queryset.filter(
                latitude__gte=lat_min,
                latitude__lte=lat_max,
                longitude__gte=lon_min,
                longitude__lte=lon_max,
            )

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    @decorators.action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request, *args, **kwargs):
        """Return a condensed list for feed previews."""
        queryset = self.filter_queryset(self.get_queryset().only(
            "id",
            "uuid",
            "title",
            "summary",
            "visibility",
            "author",
            "published_at",
            "created_at",
        ))
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return response.Response(serializer.data)

    @decorators.action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        url_path="publish",
    )
    def publish(self, request, pk=None, *args, **kwargs):
        """Mark a draft as published and set timestamps."""
        entry = self.get_object()
        if entry.author != request.user:
            return response.Response(status=status.HTTP_403_FORBIDDEN)

        entry.is_draft = False
        entry.published_at = entry.published_at or timezone.now()
        entry.save(update_fields=["is_draft", "published_at", "updated_at"])
        serializer = self.get_serializer(entry)
        return response.Response(serializer.data)
