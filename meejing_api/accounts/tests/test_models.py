from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    def test_create_user_with_profile_fields(self) -> None:
        user = get_user_model().objects.create_user(
            username="explorer",
            email="explorer@example.com",
            password="testpass123",
            display_name="Explorer",
            profile_visibility="friends",
            latitude=25.032969,
            longitude=121.565414,
        )

        self.assertEqual(user.display_name, "Explorer")
        self.assertEqual(user.profile_visibility, "friends")
        self.assertAlmostEqual(float(user.latitude), 25.032969, places=6)
        self.assertEqual(str(user), "Explorer")

