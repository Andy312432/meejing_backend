from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from .models import Place, Post

User = get_user_model()


class MapApiTests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            email="owner@example.com",
            password="pass1234",
        )
        self.viewer = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="pass1234",
        )

        self.place = Place.objects.create(
            name="Hidden Cafe",
            description="Cozy spot.",
            latitude=25.03,
            longitude=121.56,
            visibility="friends",
            created_by=self.owner,
        )
        self.public_place = Place.objects.create(
            name="Central Park",
            description="Open area.",
            latitude=40.78,
            longitude=-73.96,
            visibility="public",
            created_by=self.owner,
        )
        self.post = Post.objects.create(
            place=self.place,
            author=self.owner,
            title="New discovery",
            body="Great beans here.",
            visibility="friends",
        )

    def test_public_places_endpoint(self):
        url = reverse("core:map:place-public-places")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Central Park")

    def test_posts_by_place(self):
        url = reverse("core:map:post-by-place", kwargs={"place_uuid": str(self.place.uuid)})
        self.client.force_authenticate(self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["title"], self.post.title)

    def test_edit_place_requires_owner(self):
        url = reverse("core:map:place-detail", kwargs={"pk": self.place.pk})
        self.client.force_authenticate(self.viewer)
        response = self.client.patch(url, {"name": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.owner)
        response = self.client.patch(url, {"name": "Updated"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name, "Updated")

    def test_posts_by_user(self):
        url = reverse("core:map:post-by-user", kwargs={"user_uuid": str(self.owner.uuid)})
        self.client.force_authenticate(self.owner)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_post(self):
        url = reverse("core:map:post-detail", kwargs={"pk": self.post.pk})
        self.client.force_authenticate(self.viewer)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.owner)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())
