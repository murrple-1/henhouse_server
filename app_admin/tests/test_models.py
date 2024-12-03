from django.test import TestCase

from app_admin.models import Token, User


class UserTestCase(TestCase):
    def test_create_user(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", "password")

    def test_create_superuser(self):
        User.objects.create_superuser("test@test.com", "password")

        with self.assertRaises(ValueError):
            User.objects.create_superuser("test1@test.com", "password", is_staff=False)

        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                "test2@test.com", "password", is_superuser=False
            )


class TokenTestCase(TestCase):
    def test_save(self):
        user = User.objects.create_user("test@test.com", None)
        token = Token(user=user)
        token.save()

        token = Token(user=user, key=None)
        token.save()

    def test_str(self):
        user = User.objects.create_user("test@test.com", None)
        token = Token(user=user)

        self.assertEqual(str(token), token.key)
