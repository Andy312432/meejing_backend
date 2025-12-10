from django.contrib import admin

from .models import Place, Post


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "visibility", "created_at")
    list_filter = ("visibility",)
    search_fields = ("name", "description")
    readonly_fields = ("uuid",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "place", "author", "visibility", "created_at")
    list_filter = ("visibility",)
    search_fields = ("title", "body", "place__name", "author__username")
    readonly_fields = ("uuid",)
