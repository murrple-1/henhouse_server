from typing import ClassVar

from django.test import TestCase
from ninja.testing import TestClient

from app_admin.models import User
from art.api import router
from art.models import Story


class ApiTest(TestCase):
    user: ClassVar[User]

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)

        self.test_client = TestClient(router)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = User.objects.create_user("test@test.com", None)

    def test_list_stories(self):
        response = self.test_client.get("/story")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"items": [], "count": 0})

        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        response = self.test_client.get("/story")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "items": [
                    {
                        "title": "Test Story",
                        "uuid": str(story.uuid),
                    }
                ],
                "count": 1,
            },
        )

        response = self.test_client.get("/story", user=ApiTest.user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "items": [
                    {
                        "title": "Test Story",
                        "uuid": str(story.uuid),
                    }
                ],
                "count": 1,
            },
        )
