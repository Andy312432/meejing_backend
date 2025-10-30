from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, response, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.views import APIView

from core.models import VisibilityChoices
from social.models import Follow
from .serializers import (
    UserDetailSerializer,
    UserPublicSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


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

    @action(detail=True, methods=["get"], url_path="stats")
    def stats(self, request, pk=None):
        user = self.get_object()
        data = {
            "entries": user.journal_entries.filter(is_draft=False).count(),
            "followers": user.followers.filter(status=Follow.Status.ACCEPTED).count(),
            "following": user.following.filter(status=Follow.Status.ACCEPTED).count(),
        }
        return response.Response(data)


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
