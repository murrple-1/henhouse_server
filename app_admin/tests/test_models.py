from django.test import TestCase

from app_admin.models import Token, User


class UserTestCase(TestCase):
    def test_create_user(self):
        with self.assertRaises(ValueError):
            User.objects.create_user("", "test@test.com", "password")

        with self.assertRaises(ValueError):
            User.objects.create_user("user1", "", "password")

        User.objects.create_user("user1", "test@test.com", "password")

    async def test_acreate_user(self):
        with self.assertRaises(ValueError):
            await User.objects.acreate_user("", "test@test.com", "password")

        with self.assertRaises(ValueError):
            await User.objects.acreate_user("user1", "", "password")

        await User.objects.acreate_user("user1", "test@test.com", "password")

    def test_create_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                "user1", "test1@test.com", "password", is_staff=False
            )

        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                "user1", "test2@test.com", "password", is_superuser=False
            )

        User.objects.create_superuser("user1", "test@test.com", "password")

    async def test_acreate_superuser(self):
        with self.assertRaises(ValueError):
            await User.objects.acreate_superuser(
                "user1", "test1@test.com", "password", is_staff=False
            )

        with self.assertRaises(ValueError):
            await User.objects.acreate_superuser(
                "user1", "test2@test.com", "password", is_superuser=False
            )

        await User.objects.acreate_superuser("user1", "test@test.com", "password")


class TokenTestCase(TestCase):
    def test_save(self):
        user = User.objects.create_user("user1", "test@test.com", None)
        token = Token(user=user)
        token.save()

        token = Token(user=user, key=None)
        token.save()

    def test_str(self):
        user = User.objects.create_user("user1", "test@test.com", None)
        token = Token(user=user)

        self.assertEqual(str(token), token.key)
