from django.urls import include, path

from .views import SearchView

app_name = "core"

urlpatterns = [
    path("auth/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("journals/", include(("journals.urls", "journals"), namespace="journals")),
    path("social/", include(("social.urls", "social"), namespace="social")),
    path("search/", SearchView.as_view(), name="search"),
]
