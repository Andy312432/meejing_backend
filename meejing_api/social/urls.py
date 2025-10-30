from rest_framework.routers import DefaultRouter

from .views import CollectionViewSet, CommentViewSet, FollowViewSet, LikeViewSet

app_name = "social"

router = DefaultRouter()
router.register("follows", FollowViewSet, basename="follow")
router.register("likes", LikeViewSet, basename="like")
router.register("comments", CommentViewSet, basename="comment")
router.register("collections", CollectionViewSet, basename="collection")

urlpatterns = router.urls
