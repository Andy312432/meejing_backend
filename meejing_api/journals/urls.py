from rest_framework.routers import DefaultRouter

from .views import JournalEntryViewSet, JournalTagViewSet, LocationViewSet

app_name = "journals"

router = DefaultRouter()
router.register("locations", LocationViewSet, basename="location")
router.register("tags", JournalTagViewSet, basename="journal-tag")
router.register("entries", JournalEntryViewSet, basename="journal-entry")

urlpatterns = router.urls
