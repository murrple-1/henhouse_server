import datetime
import uuid
from time import timezone
from typing import ClassVar

from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestClient

from app_admin.models import User
from art.api import router
from art.models import Chapter, Story, Tag
from art.schemas import StoryInSchema, StoryPatchInSchema


class ApiTest(TestCase):
    user: ClassVar[User]
    test_client: ClassVar[TestClient]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.test_client = TestClient(router)

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = User.objects.create_user("test@test.com", None)

    def test_list_stories(self):
        response = self.test_client.get('/story?search=title:"test"')

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"items": [], "count": 0})

        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        response = self.test_client.get("/story")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "items": [],
                "count": 0,
            },
        )

        response = self.test_client.get("/story", user=ApiTest.user)
        self.assertEqual(response.status_code, 200, response.content)
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

    def test_story_details(self):
        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        response = self.test_client.get(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 404, response.content)

        response = self.test_client.get(f"/story/{story.uuid}", user=ApiTest.user)
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        self.assertIsInstance(json_, dict)
        assert isinstance(json_, dict)
        self.assertIn("created_at", json_)
        self.assertIsInstance(json_["created_at"], str)
        datetime.datetime.fromisoformat(json_["created_at"])
        json_.pop("created_at")
        self.assertEqual(
            json_,
            {
                "title": "Test Story",
                "uuid": str(story.uuid),
                "tags": [],
                "creator": str(ApiTest.user.uuid),
            },
        )

        Chapter.objects.create(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=timezone.now(),
        )

        response = self.test_client.get(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        self.assertIsInstance(json_, dict)
        assert isinstance(json_, dict)
        self.assertIn("created_at", json_)
        self.assertIsInstance(json_["created_at"], str)
        datetime.datetime.fromisoformat(json_["created_at"])
        json_.pop("created_at")
        self.assertEqual(
            json_,
            {
                "title": "Test Story",
                "uuid": str(story.uuid),
                "tags": [],
                "creator": str(ApiTest.user.uuid),
            },
        )

    def test_create_story(self):
        input_data = StoryInSchema(title="Test Story 1", tags=[])
        response = self.test_client.post(
            "/story", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        self.assertIsInstance(json_, dict)
        assert isinstance(json_, dict)
        self.assertIn("uuid", json_)
        self.assertIsInstance(json_["uuid"], str)
        uuid.UUID(json_["uuid"])
        json_.pop("uuid")
        self.assertEqual(
            json_,
            {
                "title": "Test Story 1",
            },
        )

        tag = Tag.objects.create(name="test")
        input_data = StoryInSchema(title="Test Story 2", tags=[str(tag.uuid)])
        response = self.test_client.post(
            "/story", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        self.assertIsInstance(json_, dict)
        assert isinstance(json_, dict)
        self.assertIn("uuid", json_)
        self.assertIsInstance(json_["uuid"], str)
        uuid.UUID(json_["uuid"])
        json_.pop("uuid")
        self.assertEqual(
            json_,
            {
                "title": "Test Story 2",
            },
        )

    def test_create_story_tagsnotfound(self):
        input_data = StoryInSchema(title="Test Story", tags=[str(uuid.UUID(int=0))])
        response = self.test_client.post(
            "/story", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 404, response.content)

    def test_create_story_invalidtitle(self):
        response = self.test_client.post(
            "/story", json={"title": "", "tags": []}, user=ApiTest.user
        )
        self.assertEqual(response.status_code, 422, response.content)

    def test_create_story_notauthorized(self):
        response = self.test_client.post(
            "/story", json={"title": "Test Story", "tags": []}
        )
        self.assertEqual(response.status_code, 401, response.content)

    def test_patch_story(self):
        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        input_data = StoryPatchInSchema()
        response = self.test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(
            response.json(),
            {
                "title": "Test Story",
                "uuid": str(story.uuid),
            },
        )

        input_data = StoryPatchInSchema(title="New Story Title")
        response = self.test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(
            response.json(),
            {
                "title": "New Story Title",
                "uuid": str(story.uuid),
            },
        )

        input_data = StoryPatchInSchema(title="New Story Title")
        response = self.test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(
            response.json(),
            {
                "title": "New Story Title",
                "uuid": str(story.uuid),
            },
        )

        tag = Tag.objects.create(name="test")
        input_data = StoryPatchInSchema(tags=[str(tag.uuid)])
        response = self.test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(
            response.json(),
            {
                "title": "New Story Title",
                "uuid": str(story.uuid),
            },
        )

    def test_patch_story_storynotfound(self):
        input_data = StoryPatchInSchema()
        response = self.test_client.patch(
            f"/story/{uuid.UUID(int=0)}", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 404, response.content)

    def test_patch_story_tagnotfound(self):
        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        input_data = StoryPatchInSchema(tags=[str(uuid.UUID(int=0))])
        response = self.test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=ApiTest.user
        )
        self.assertEqual(response.status_code, 404, response.content)

    def test_patch_story_notauthorized(self):
        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        input_data = StoryPatchInSchema()
        response = self.test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict()
        )
        self.assertEqual(response.status_code, 401, response.content)

    def test_delete_story(self):
        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        response = self.test_client.delete(f"/story/{story.uuid}", user=ApiTest.user)
        self.assertEqual(response.status_code, 204, response.content)

    def test_delete_story_notfound(self):
        response = self.test_client.delete(
            f"/story/{uuid.UUID(int=0)}", user=ApiTest.user
        )
        self.assertEqual(response.status_code, 404, response.content)

    def test_delete_story_notauthorized(self):
        story = Story.objects.create(title="Test Story", creator=ApiTest.user)

        response = self.test_client.delete(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 401, response.content)
