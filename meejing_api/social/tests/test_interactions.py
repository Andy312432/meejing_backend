from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import VisibilityChoices
from journals.models import JournalEntry

User = get_user_model()


class SocialInteractionTests(APITestCase):
    def setUp(self) -> None:
        self.author = User.objects.create_user(
            username="author",
            email="author@example.com",
            password="safe-pass-123",
        )
        self.viewer = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="safe-pass-123",
        )
        self.entry = JournalEntry.objects.create(
            author=self.author,
            title="Hidden Gem",
            summary="A secret coffee shop.",
            body="Tucked away behind the alley.",
            latitude=25.032969,
            longitude=121.565414,
            visibility=VisibilityChoices.FRIENDS,
        )
        self.entry.refresh_from_db()

    def authenticate(self, user: User) -> None:
        self.client.force_authenticate(user)

    def test_follow_allows_access_to_friends_entries(self):
        self.authenticate(self.viewer)
        # Before follow, entry should not appear
        list_url = reverse("core:journals:journal-entry-list")
        response = self.client.get(list_url)
        self.assertEqual(response.data["count"], 0)

        follow_url = reverse("core:social:follow-list")
        response = self.client.post(follow_url, {"following_id": self.author.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        response = self.client.get(list_url)
        self.assertEqual(response.data["count"], 1)

    def test_like_and_unlike_updates_counts(self):
        self.authenticate(self.viewer)
        like_url = reverse("core:social:like-list")
        response = self.client.post(like_url, {"entry_id": self.entry.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.like_count, 1)

        unlike_url = reverse("core:social:like-detail", kwargs={"pk": self.entry.id})
        response = self.client.delete(unlike_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.like_count, 0)

    def test_comments_increment_count_and_soft_delete(self):
        self.authenticate(self.viewer)
        comment_url = reverse("core:social:comment-list")
        response = self.client.post(
            comment_url, {"entry_id": self.entry.id, "body": "Love this!"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.comment_count, 1)

        comment_id = response.data["id"]
        detail_url = reverse("core:social:comment-detail", kwargs={"pk": comment_id})
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.comment_count, 0)

    def test_save_entry_to_collection_updates_bookmark_count(self):
        self.authenticate(self.viewer)
        # follow so viewer can see the entry
        self.client.post(reverse("core:social:follow-list"), {"following_id": self.author.id})

        favorites_url = reverse("core:social:collection-favorites")
        response = self.client.get(favorites_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        collection_id = response.data["id"]

        add_url = reverse("core:social:collection-add-entry", kwargs={"pk": collection_id})
        response = self.client.post(add_url, {"entry_id": self.entry.id})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)

        self.entry.refresh_from_db()
        self.assertEqual(self.entry.bookmark_count, 1)
