import datetime
import unittest
import uuid

from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestAsyncClient
from ninja.testing.client import NinjaResponse

from app_admin.models import User
from art.api import router
from art.models import Chapter, Story, Tag
from art.schemas import (
    ChapterInSchema,
    ChapterPatchInSchema,
    StoryInSchema,
    StoryPatchInSchema,
)


class ApiTest(TestCase):
    @unittest.skip(
        "skip until https://github.com/vitalik/django-ninja/pull/1340 is resolved"
    )
    async def test_list_stories(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.get('/story?search=title:"test"')

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"items": [], "count": 0})

        story = await Story.objects.acreate(title="Test Story", creator=user)

        response = await test_client.get("/story")

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "items": [],
                "count": 0,
            },
        )

        response = await test_client.get("/story", user=user)
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

    async def test_story_details(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        response = await test_client.get(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/story/{story.uuid}", user=user)
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
                "creator": str(user.uuid),
            },
        )

        await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=timezone.now(),
        )

        response = await test_client.get(f"/story/{story.uuid}")
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
                "creator": str(user.uuid),
            },
        )

    async def test_create_story(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        input_data = StoryInSchema(title="Test Story 1", tags=[])
        response = await test_client.post("/story", json=input_data.dict(), user=user)
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

        tag = await Tag.objects.acreate(name="test")
        input_data = StoryInSchema(title="Test Story 2", tags=[str(tag.uuid)])
        response = await test_client.post("/story", json=input_data.dict(), user=user)
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

    async def test_create_story_tagsnotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        input_data = StoryInSchema(title="Test Story", tags=[str(uuid.UUID(int=0))])
        response = await test_client.post("/story", json=input_data.dict(), user=user)
        self.assertEqual(response.status_code, 404, response.content)

    async def test_create_story_invalidtitle(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.post(
            "/story", json={"title": "", "tags": []}, user=user
        )
        self.assertEqual(response.status_code, 422, response.content)

    async def test_create_story_notauthorized(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.post(
            "/story", json={"title": "Test Story", "tags": []}
        )
        self.assertEqual(response.status_code, 401, response.content)

    async def test_patch_story(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        input_data = StoryPatchInSchema()
        response = await test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(
            response.json(),
            {
                "title": "Test Story",
                "uuid": str(story.uuid),
            },
        )
        await story.arefresh_from_db(fields=("title",))
        self.assertEqual(story.title, "Test Story")

        input_data = StoryPatchInSchema(title="New Story Title")
        response = await test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "title": "New Story Title",
                "uuid": str(story.uuid),
            },
        )
        await story.arefresh_from_db(fields=("title",))
        self.assertEqual(story.title, "New Story Title")
        self.assertEqual(await story.tags.acount(), 0)

        tag = await Tag.objects.acreate(name="test")
        input_data = StoryPatchInSchema(tags=[str(tag.uuid)])
        response = await test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 200, response.content)

        self.assertEqual(
            response.json(),
            {
                "title": "New Story Title",
                "uuid": str(story.uuid),
            },
        )
        await story.arefresh_from_db(fields=("title",))
        self.assertEqual(story.title, "New Story Title")
        self.assertEqual(await story.tags.acount(), 1)

    async def test_patch_story_storynotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        input_data = StoryPatchInSchema()
        response = await test_client.patch(
            f"/story/{uuid.UUID(int=0)}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_patch_story_tagnotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        input_data = StoryPatchInSchema(tags=[str(uuid.UUID(int=0))])
        response = await test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_patch_story_notauthorized(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        input_data = StoryPatchInSchema()
        response = await test_client.patch(
            f"/story/{story.uuid}", json=input_data.dict()
        )
        self.assertEqual(response.status_code, 401, response.content)

    async def test_delete_story(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        response = await test_client.delete(f"/story/{story.uuid}", user=user)
        self.assertEqual(response.status_code, 204, response.content)

    async def test_delete_story_notfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.delete(f"/story/{uuid.UUID(int=0)}", user=user)
        self.assertEqual(response.status_code, 404, response.content)

    async def test_delete_story_notauthorized(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        response = await test_client.delete(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 401, response.content)

    @unittest.skip(
        "skip until https://github.com/vitalik/django-ninja/pull/1340 is resolved"
    )
    async def test_list_chapters(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        def assert_empty_response(response: NinjaResponse):
            self.assertEqual(response.status_code, 200, response.content)
            json_ = response.json()
            self.assertIsInstance(json_, dict)
            assert isinstance(json_, dict)
            self.assertEqual(
                json_,
                {
                    "count": 0,
                    "items": [],
                },
            )

        response = await test_client.get(f"/story/{story.uuid}/chapter")
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/story/{story.uuid}/chapter", user=alt_user)
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/story/{story.uuid}/chapter", user=user)
        assert_empty_response(response)

        chapter1 = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        def assert_single_entry_response(response: NinjaResponse):
            json_ = response.json()

            self.assertEqual(
                json_,
                {
                    "count": 1,
                    "items": [
                        {
                            "uuid": str(chapter1.uuid),
                            "index": chapter1.index,
                            "name": chapter1.name,
                        }
                    ],
                },
            )

        response = await test_client.get(f"/story/{story.uuid}/chapter")
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/story/{story.uuid}/chapter", user=alt_user)
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/story/{story.uuid}/chapter", user=user)
        self.assertEqual(response.status_code, 200, response.content)

        assert_single_entry_response(response)

        chapter1.published_at = timezone.now()
        await chapter1.asave(update_fields=("published_at",))

        response = await test_client.get(f"/story/{story.uuid}/chapter")
        self.assertEqual(response.status_code, 200, response.content)

        assert_single_entry_response(response)

        response = await test_client.get(f"/story/{story.uuid}/chapter", user=alt_user)
        self.assertEqual(response.status_code, 200, response.content)

        assert_single_entry_response(response)

        response = await test_client.get(f"/story/{story.uuid}/chapter", user=user)
        self.assertEqual(response.status_code, 200, response.content)

        assert_single_entry_response(response)

    async def test_list_chapters_notfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.get(f"/story/{uuid.UUID(int=0)}/chapter")
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(
            f"/story/{uuid.UUID(int=0)}/chapter", user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_chapter_details(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        chapter1 = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        def assert_valid_response(response: NinjaResponse):
            json_ = response.json()
            self.assertIsInstance(json_, dict)
            assert isinstance(json_, dict)
            self.assertIn("created_at", json_)
            self.assertIsInstance(json_["created_at"], str)
            datetime.datetime.fromisoformat(json_["created_at"])
            json_.pop("created_at")
            self.assertIn("published_at", json_)
            if (pa := json_["published_at"]) is None:
                pass
            elif isinstance(pa, str):
                datetime.datetime.fromisoformat(pa)
            else:
                raise AssertionError("published_at is not null nor string")
            json_.pop("published_at")
            self.assertEqual(
                json_,
                {
                    "uuid": str(chapter1.uuid),
                    "index": chapter1.index,
                    "name": chapter1.name,
                    "markdown": chapter1.markdown,
                    "story": str(story.uuid),
                },
            )

        response = await test_client.get(f"/chapter/{chapter1.uuid}")
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/chapter/{chapter1.uuid}", user=alt_user)
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/chapter/{chapter1.uuid}", user=user)
        self.assertEqual(response.status_code, 200, response.content)

        assert_valid_response(response)

        chapter1.published_at = timezone.now()
        await chapter1.asave(update_fields=("published_at",))

        response = await test_client.get(f"/chapter/{chapter1.uuid}")
        self.assertEqual(response.status_code, 200, response.content)

        assert_valid_response(response)

        response = await test_client.get(f"/chapter/{chapter1.uuid}", user=alt_user)
        self.assertEqual(response.status_code, 200, response.content)

        assert_valid_response(response)

        response = await test_client.get(f"/chapter/{chapter1.uuid}", user=user)
        self.assertEqual(response.status_code, 200, response.content)

        assert_valid_response(response)

    async def test_create_chapter(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        input_data = ChapterInSchema(name="Chapter 1", markdown="Chapter Text")
        response = await test_client.post(
            f"/story/{story.uuid}/chapter", json=input_data.dict(), user=user
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
                "name": "Chapter 1",
                "index": 0,
            },
        )

    async def test_create_chapter_notfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        input_data = ChapterInSchema(name="Chapter 1", markdown="Chapter Text")

        response = await test_client.post(
            f"/story/{story.uuid}/chapter", json=input_data.dict(), user=alt_user
        )
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.post(
            f"/story/{uuid.UUID(int=0)}/chapter", json=input_data.dict(), user=alt_user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_patch_chapter(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        input_data = ChapterPatchInSchema()
        response = await test_client.patch(
            f"/chapter/{chapter.uuid}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Chapter 1",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown"))
        self.assertEqual(chapter.name, "Chapter 1")
        self.assertEqual(chapter.markdown, "Chapter Text")

        input_data = ChapterPatchInSchema(name="Introduction")
        response = await test_client.patch(
            f"/chapter/{chapter.uuid}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Introduction",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown"))
        self.assertEqual(chapter.name, "Introduction")
        self.assertEqual(chapter.markdown, "Chapter Text")

        input_data = ChapterPatchInSchema(markdown="Introduction Text")
        response = await test_client.patch(
            f"/chapter/{chapter.uuid}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Introduction",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown"))
        self.assertEqual(chapter.name, "Introduction")
        self.assertEqual(chapter.markdown, "Introduction Text")

    async def test_patch_chapter_notfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        input_data = ChapterPatchInSchema()
        response = await test_client.patch(
            f"/chapter/{chapter.uuid}", json=input_data.dict(), user=alt_user
        )
        self.assertEqual(response.status_code, 404, response.content)
        response = await test_client.patch(
            f"/chapter/{uuid.UUID(int=0)}", json=input_data.dict(), user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_delete_chapter(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        response = await test_client.delete(f"/chapter/{chapter.uuid}", user=user)
        self.assertEqual(response.status_code, 204, response.content)

    async def test_delete_chapter_notfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        story = await Story.objects.acreate(title="Test Story", creator=user)

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        response = await test_client.delete(f"/chapter/{chapter.uuid}", user=alt_user)
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.delete(
            f"/chapter/{uuid.UUID(int=0)}", user=alt_user
        )
        self.assertEqual(response.status_code, 404, response.content)

    @unittest.skip(
        "skip until https://github.com/vitalik/django-ninja/pull/1340 is resolved"
    )
    async def test_list_tags(self):
        test_client = TestAsyncClient(router)

        response = await test_client.get("/tag")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"count": 0, "items": []})

        await Tag.objects.acreate(name="test")

        response = await test_client.get("/tag")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"count": 1, "items": []})
