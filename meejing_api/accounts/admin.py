from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Expose the custom user model with additional profile fields."""

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _("Profile"),
            {
                "fields": (
                    "uuid",
                    "display_name",
                    "avatar",
                    "profile_visibility",
                )
            },
        ),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            _("Profile"),
            {
                "fields": (
                    "display_name",
                    "profile_visibility",
                )
            },
        ),
    )
    list_display = (
        "username",
        "email",
        "display_name",
        "profile_visibility",
        "is_active",
    )
    list_filter = BaseUserAdmin.list_filter + ("profile_visibility",)
    search_fields = ("username", "email", "display_name")
    readonly_fields = BaseUserAdmin.readonly_fields + ("uuid",)
