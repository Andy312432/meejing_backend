from rest_framework.routers import DefaultRouter

from .views import PlaceViewSet, PostViewSet

app_name = "map"

router = DefaultRouter()
router.register("places", PlaceViewSet, basename="place")
router.register("posts", PostViewSet, basename="post")

urlpatterns = router.urls
