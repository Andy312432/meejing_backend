from __future__ import annotations

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, response

from core.models import VisibilityChoices
from map.models import Place, Post
from map.serializers import PlaceSerializer, PostSerializer
from .serializers import SearchResultsSerializer


@extend_schema(
    tags=["Discovery"],
    summary="Global search across places and posts",
    parameters=[
        OpenApiParameter(
            name="q",
            required=True,
            type=str,
            location=OpenApiParameter.QUERY,
            description="Search term (minimum 2 characters).",
        )
    ],
    responses={200: SearchResultsSerializer},
)
class SearchView(generics.GenericAPIView):
    """Unified search endpoint for places and posts."""

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    serializer_class = SearchResultsSerializer

    def get(self, request, *args, **kwargs):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return response.Response(
                {"detail": "Query must be at least 2 characters.", "results": {}},
                status=400,
            )

        user = request.user if request.user.is_authenticated else None

        place_filters = Q(name__icontains=query) | Q(description__icontains=query)
        place_qs = Place.objects.filter(place_filters)
        if not user:
            place_qs = place_qs.filter(visibility=VisibilityChoices.PUBLIC)
        else:
            place_qs = place_qs.filter(
                Q(visibility=VisibilityChoices.PUBLIC) | Q(created_by=user)
            )

        post_filters = Q(title__icontains=query) | Q(body__icontains=query)
        post_qs = Post.objects.select_related("author", "place").filter(post_filters)
        if not user:
            post_qs = post_qs.filter(
                visibility=VisibilityChoices.PUBLIC,
                place__visibility=VisibilityChoices.PUBLIC,
            )
        else:
            post_qs = post_qs.filter(
                Q(visibility=VisibilityChoices.PUBLIC)
                | Q(author=user)
                | Q(place__created_by=user)
            )

        places = PlaceSerializer(place_qs[:20], many=True).data
        posts = PostSerializer(post_qs[:20], many=True).data

        serializer = self.get_serializer({"places": places, "posts": posts})
        return response.Response({"results": serializer.data})
