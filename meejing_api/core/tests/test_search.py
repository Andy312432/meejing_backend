from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from journals.models import JournalEntry, JournalTag, Location

User = get_user_model()


class SearchEndpointTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="seeker",
            email="seeker@example.com",
            password="search-pass",
        )
        self.client.force_authenticate(self.user)

        self.location = Location.objects.create(
            created_by=self.user,
            name="Coffee Lab",
            description="Artisan coffee shop",
            formatted_address="123 Bean St, Taipei",
            latitude=25.04,
            longitude=121.56,
            country_code="TW",
            administrative_area="Taipei",
            locality="Da'an",
        )

        self.tag = JournalTag.objects.create(name="coffee", created_by=self.user)
        self.entry = JournalEntry.objects.create(
            author=self.user,
            title="Exploring Coffee Lab",
            summary="Tasting new brews.",
            body="Notes on the single-origin pour over.",
            latitude=25.04,
            longitude=121.56,
            visibility="public",
        )
        self.entry.tags.add(self.tag)

    def test_search_returns_entries_locations_and_tags(self):
        url = reverse("core:search")
        response = self.client.get(url, {"q": "coffee"})
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertTrue(any(entry["id"] == self.entry.id for entry in results["entries"]))
        self.assertTrue(any(loc["id"] == self.location.id for loc in results["locations"]))
        self.assertTrue(any(tag["id"] == self.tag.id for tag in results["tags"]))

