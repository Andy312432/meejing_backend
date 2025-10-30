from typing import Dict, List

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from journals.models import JournalEntry, Location


User = get_user_model()


class JournalApiTests(APITestCase):
    def setUp(self) -> None:
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="strong-password",
        )
        self.viewer = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="strong-password",
        )

    def _authenticate(self, user: User) -> None:
        self.client.force_authenticate(user)

    def _create_location(self, user: User) -> Location:
        self._authenticate(user)
        url = reverse("core:journals:location-list")
        payload: Dict[str, str] = {
            "name": "Taipei 101",
            "description": "Landmark skyscraper",
            "formatted_address": "Taipei 101, Taipei",
            "latitude": "25.033964",
            "longitude": "121.564468",
            "country_code": "TW",
            "administrative_area": "Taipei",
            "locality": "Xinyi District",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        return Location.objects.get(pk=response.data["id"])

    def test_user_can_create_location(self):
        location = self._create_location(self.author)

        self.assertEqual(location.name, "Taipei 101")
        list_url = reverse("core:journals:location-list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_create_journal_entry_with_tags(self):
        location = self._create_location(self.author)
        self._authenticate(self.author)
        url = reverse("core:journals:journal-entry-list")

        data = {
            "title": "Evening at Taipei 101",
            "summary": "Beautiful city lights.",
            "body": "Captured the city skyline during blue hour.",
            "location_id": str(location.id),
            "latitude": "25.033964",
            "longitude": "121.564468",
            "visibility": "public",
            "tag_names": ["cityscape", "taipei"],
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        entry = JournalEntry.objects.get(pk=response.data["id"])
        tags: List[str] = list(entry.tags.values_list("name", flat=True))
        self.assertIn("cityscape", tags)
        self.assertIn("taipei", tags)

        self.assertEqual(entry.media.count(), 0)

    def test_visibility_rules_hide_private_entries(self):
        location = self._create_location(self.author)
        self._authenticate(self.author)
        create_url = reverse("core:journals:journal-entry-list")

        entry_payload = {
            "title": "Secret Spot",
            "summary": "Hidden cafe.",
            "body": "A peaceful afternoon.",
            "location_id": str(location.id),
            "latitude": "25.04",
            "longitude": "121.56",
            "visibility": "private",
        }
        response = self.client.post(create_url, entry_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.client.force_authenticate(self.viewer)
        list_url = reverse("core:journals:journal-entry-list")
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

        self.client.force_authenticate(self.author)
        response = self.client.get(list_url)
        self.assertEqual(response.data["count"], 1)
