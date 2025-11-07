from django.urls import include, path

from .views import SearchView

app_name = "core"

urlpatterns = [
    path("auth/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("map/", include(("map.urls", "map"), namespace="map")),
    path("search/", SearchView.as_view(), name="search"),
]
