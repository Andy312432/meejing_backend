from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

from map.models import Place, Post

User = get_user_model()


class SearchEndpointTests(APITestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="seeker",
            email="seeker@example.com",
            password="search-pass",
        )
        self.client.force_authenticate(self.user)

        self.place = Place.objects.create(
            created_by=self.user,
            name="Coffee Lab",
            description="Artisan coffee shop",
            latitude=25.04,
            longitude=121.56,
            visibility="public",
        )
        self.post = Post.objects.create(
            place=self.place,
            author=self.user,
            title="Exploring Coffee Lab",
            body="Tasting new brews.",
            visibility="public",
        )

    def test_search_returns_places_and_posts(self):
        url = reverse("core:search")
        response = self.client.get(url, {"q": "coffee"})
        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        self.assertTrue(
            any(place["id"] == self.place.id for place in results["places"])
        )
        self.assertTrue(any(post["id"] == self.post.id for post in results["posts"]))

