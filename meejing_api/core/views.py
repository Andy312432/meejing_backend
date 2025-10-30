from __future__ import annotations

from django.db.models import Q
from rest_framework import generics, permissions, response

from journals.models import JournalEntry, JournalTag, Location
from journals.serializers import (
    JournalEntrySummarySerializer,
    JournalTagSerializer,
    LocationSerializer,
)
from .serializers import SearchResultsSerializer


class SearchView(generics.GenericAPIView):
    """Unified search endpoint for entries, locations, and tags."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = SearchResultsSerializer
    queryset = JournalEntry.objects.none()

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return response.Response(
                {"detail": "Query must be at least 2 characters.", "results": {}},
                status=400,
            )

        entry_qs = (
            JournalEntry.objects.visible_to(request.user)
            .filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(body__icontains=query)
                | Q(tags__name__icontains=query)
            )
            .distinct()
            .select_related("author", "location")
            .prefetch_related("tags")
        )[:20]
        location_qs = (
            Location.objects.filter(
                Q(name__icontains=query) | Q(formatted_address__icontains=query)
            )
            .select_related("created_by")
            .order_by("-created_at")[:20]
        )
        tag_qs = JournalTag.objects.filter(name__icontains=query)[:10]

        results = {
            "entries": JournalEntrySummarySerializer(entry_qs, many=True).data,
            "locations": LocationSerializer(location_qs, many=True).data,
            "tags": JournalTagSerializer(tag_qs, many=True).data,
        }
        serializer = self.get_serializer(results)
        return response.Response({"results": serializer.data})
