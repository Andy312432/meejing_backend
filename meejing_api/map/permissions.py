from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Allow read-only requests for everyone but restrict writes to owners."""

    owner_attribute = "created_by"

    def has_permission(self, request, view):
        user = request.user
        if user and user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        return user and user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user and user.is_superuser:
            return True
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, self.owner_attribute, None)
        return owner == user


class IsPostOwnerOrReadOnly(IsOwnerOrReadOnly):
    owner_attribute = "author"
