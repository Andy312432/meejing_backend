from __future__ import annotations

from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter

from core.models import VisibilityChoices
from map.models import Post
from .serializers import (
    UserDetailSerializer,
    UserPublicSerializer,
    UserRegistrationSerializer,
    UserStatsSerializer,
)

User = get_user_model()


@extend_schema_view(
    list=extend_schema(
        tags=["Accounts"],
        summary="List public user profiles",
        responses=UserPublicSerializer,
    ),
    retrieve=extend_schema(
        tags=["Accounts"],
        summary="Retrieve a user profile",
        responses=UserPublicSerializer,
    ),
)
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """Public directory of users with search and stats endpoints."""

    queryset = User.objects.all()
    serializer_class = UserPublicSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "display_name", "email"]
    ordering_fields = ["username", "date_joined"]
    ordering = ["username"]

    def get_queryset(self):
        qs = super().get_queryset()
        viewer = self.request.user
        if not viewer.is_authenticated:
            qs = qs.filter(profile_visibility=VisibilityChoices.PUBLIC)
        return qs

    @extend_schema(
        tags=["Accounts"],
        summary="User stats overview",
        responses=UserStatsSerializer,
    )
    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        """Return aggregate counts for the requested user."""

        user = self.get_object()
        data = {
            "posts": Post.objects.filter(author=user).count(),
        }
        serializer = UserStatsSerializer(data)
        return response.Response(serializer.data)


@extend_schema_view(
    get=extend_schema(
        tags=["Accounts"],
        summary="Fetch current user profile",
        responses=UserDetailSerializer,
    ),
    patch=extend_schema(
        tags=["Accounts"],
        summary="Update current user profile",
        responses=UserDetailSerializer,
    ),
)
class MeView(generics.GenericAPIView):
    """Retrieve or update the authenticated user's profile."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserDetailSerializer
    queryset = User.objects.none()

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return response.Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.data)

 
@extend_schema_view(
    post=extend_schema(
        tags=["Accounts"],
        summary="Register a new user",
        responses={201: UserDetailSerializer},
    )
)
class RegisterView(generics.GenericAPIView):
    """Create a new account."""

    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer
    queryset = User.objects.none()

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = UserDetailSerializer(user)
        return response.Response(output.data, status=status.HTTP_201_CREATED)
