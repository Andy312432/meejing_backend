from django.contrib import admin

from .models import JournalEntry, JournalMedia, JournalTag, Location


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "latitude", "longitude", "is_verified")
    list_filter = ("is_verified", "country_code")
    search_fields = ("name", "formatted_address", "place_id", "created_by__username")
    autocomplete_fields = ("created_by",)


@admin.register(JournalTag)
class JournalTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_by", "created_at")
    search_fields = ("name", "slug")
    autocomplete_fields = ("created_by",)


class JournalMediaInline(admin.TabularInline):
    model = JournalMedia
    extra = 0


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "visibility",
        "created_at",
        "published_at",
        "like_count",
        "comment_count",
    )
    list_filter = ("visibility", "mood", "tags")
    search_fields = ("title", "summary", "body", "author__username")
    autocomplete_fields = ("author", "location", "tags")
    inlines = [JournalMediaInline]
