import datetime
import unittest
import uuid

from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestAsyncClient
from ninja.testing.client import NinjaResponse

from app_admin.models import User
from art.api import router
from art.models import Category, Chapter, Story, Tag


class ApiTestCase(TestCase):
    @unittest.skip(
        "skip until https://github.com/vitalik/django-ninja/pull/1340 is resolved"
    )
    async def test_list_stories(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.get('/story?search=title:"test"')

        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"items": [], "count": 0})

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

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

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.get(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.get(f"/story/{story.uuid}", user=user)
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        self.assertIsInstance(json_, dict)
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "Test Story",
                "synopsis": "Test Story Synopsis",
                "uuid": str(story.uuid),
                "tags": [],
                "creator": str(user.uuid),
                "category": category.name,
            },
        )

        await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            synopsis="",
            index=0,
            markdown="Chapter Text",
            published_at=timezone.now(),
        )

        response = await test_client.get(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        self.assertIsInstance(json_, dict)
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        datetime.datetime.fromisoformat(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "Test Story",
                "synopsis": "Test Story Synopsis",
                "uuid": str(story.uuid),
                "tags": [],
                "creator": str(user.uuid),
                "category": category.name,
            },
        )

    async def test_create_story(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        response = await test_client.post(
            "/story",
            json={
                "title": "Test Story 1",
                "synopsis": "Test Story 1 Synopsis",
                "category": category.name,
                "tags": [],
            },
            user=user,
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        uuid.UUID(json_.pop("uuid"))
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "Test Story 1",
                "synopsis": "Test Story 1 Synopsis",
                "category": category.name,
                "creator": str(user.uuid),
            },
        )

        tag = await Tag.objects.acreate(name="test", pretty_name="Test")
        response = await test_client.post(
            "/story",
            json={
                "title": "Test Story 2",
                "synopsis": "Test Story 2 Synopsis",
                "category": category.name,
                "tags": [str(tag.name)],
            },
            user=user,
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        uuid.UUID(json_.pop("uuid"))
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "Test Story 2",
                "synopsis": "Test Story 2 Synopsis",
                "category": category.name,
                "creator": str(user.uuid),
            },
        )

    async def test_create_story_categorynotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.post(
            "/story",
            json={
                "title": "Test Story",
                "synopsis": "Test Story Synopsis",
                "category": "notfound",
                "tags": [],
            },
            user=user,
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_create_story_tagsnotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        response = await test_client.post(
            "/story",
            json={
                "title": "Test Story",
                "synopsis": "Test Story Synopsis",
                "category": category.name,
                "tags": ["notfound"],
            },
            user=user,
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_create_story_invalidtitle(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        response = await test_client.post(
            "/story",
            json={
                "title": "",
                "synopsis": "Synopsis",
                "category": category.name,
                "tags": [],
            },
            user=user,
        )
        self.assertEqual(response.status_code, 422, response.content)

    async def test_create_story_notauthorized(self):
        test_client = TestAsyncClient(router)

        await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        response = await test_client.post(
            "/story",
            json={
                "title": "Test Story",
                "synopsis": "Synopsis",
                "category": category.name,
                "tags": [],
            },
        )
        self.assertEqual(response.status_code, 401, response.content)

    async def test_patch_story(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.patch(f"/story/{story.uuid}", json={}, user=user)
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "Test Story",
                "synopsis": "Test Story Synopsis",
                "uuid": str(story.uuid),
                "creator": str(user.uuid),
                "category": category.name,
            },
        )
        await story.arefresh_from_db(fields=("title", "synopsis", "category_id"))
        self.assertEqual(story.title, "Test Story")
        self.assertEqual(story.synopsis, "Test Story Synopsis")
        self.assertEqual(story.category_id, category.name)
        self.assertEqual(await story.tags.acount(), 0)

        response = await test_client.patch(
            f"/story/{story.uuid}", json={"title": "New Story Title"}, user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "New Story Title",
                "synopsis": "Test Story Synopsis",
                "uuid": str(story.uuid),
                "creator": str(user.uuid),
                "category": category.name,
            },
        )
        await story.arefresh_from_db(fields=("title", "synopsis", "category_id"))
        self.assertEqual(story.title, "New Story Title")
        self.assertEqual(story.synopsis, "Test Story Synopsis")
        self.assertEqual(story.category_id, category.name)
        self.assertEqual(await story.tags.acount(), 0)

        tag = await Tag.objects.acreate(name="test", pretty_name="Test")
        response = await test_client.patch(
            f"/story/{story.uuid}", json={"tags": [str(tag.name)]}, user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "New Story Title",
                "synopsis": "Test Story Synopsis",
                "uuid": str(story.uuid),
                "creator": str(user.uuid),
                "category": category.name,
            },
        )
        await story.arefresh_from_db(fields=("title", "synopsis", "category_id"))
        self.assertEqual(story.title, "New Story Title")
        self.assertEqual(story.synopsis, "Test Story Synopsis")
        self.assertEqual(story.category_id, category.name)
        self.assertEqual(await story.tags.acount(), 1)

        response = await test_client.patch(
            f"/story/{story.uuid}", json={"synopsis": "New Story Synopsis"}, user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "New Story Title",
                "synopsis": "New Story Synopsis",
                "uuid": str(story.uuid),
                "creator": str(user.uuid),
                "category": category.name,
            },
        )
        await story.arefresh_from_db(fields=("title", "synopsis", "category_id"))
        self.assertEqual(story.title, "New Story Title")
        self.assertEqual(story.synopsis, "New Story Synopsis")
        self.assertEqual(story.category_id, category.name)
        self.assertEqual(await story.tags.acount(), 1)

        new_category = await Category.objects.acreate(
            name="test2", pretty_name="Test2", description="Description 2", sort_key=1
        )

        response = await test_client.patch(
            f"/story/{story.uuid}", json={"category": new_category.name}, user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        json_ = response.json()
        datetime.datetime.fromisoformat(json_.pop("createdAt"))
        self.assertIsNone(json_.pop("publishedAt"))
        self.assertEqual(
            json_,
            {
                "title": "New Story Title",
                "synopsis": "New Story Synopsis",
                "uuid": str(story.uuid),
                "creator": str(user.uuid),
                "category": new_category.name,
            },
        )
        await story.arefresh_from_db(fields=("title", "synopsis", "category_id"))
        self.assertEqual(story.title, "New Story Title")
        self.assertEqual(story.synopsis, "New Story Synopsis")
        self.assertEqual(story.category_id, new_category.name)
        self.assertEqual(await story.tags.acount(), 1)

    async def test_patch_story_storynotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        response = await test_client.patch(
            f"/story/{uuid.UUID(int=0)}", json={}, user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_patch_story_categorynotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.patch(
            f"/story/{story.uuid}", json={"category": "notfound"}, user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_patch_story_tagsnotfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.patch(
            f"/story/{story.uuid}", json={"tags": ["notfound"]}, user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_patch_story_notauthorized(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.patch(f"/story/{story.uuid}", json={})
        self.assertEqual(response.status_code, 401, response.content)

    async def test_delete_story(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

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

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.delete(f"/story/{story.uuid}")
        self.assertEqual(response.status_code, 401, response.content)

    @unittest.skip(
        "skip until https://github.com/vitalik/django-ninja/pull/1340 is resolved"
    )
    async def test_list_chapters(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

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
            synopsis="",
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

    @unittest.skip(
        "skip until https://github.com/vitalik/django-ninja/pull/1340 is resolved"
    )
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

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        chapter1 = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            synopsis="",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        def assert_valid_response(response: NinjaResponse):
            json_ = response.json()
            self.assertIsInstance(json_, dict)
            assert isinstance(json_, dict)
            self.assertIn("createdAt", json_)
            self.assertIsInstance(json_["createdAt"], str)
            datetime.datetime.fromisoformat(json_["createdAt"])
            json_.pop("createdAt")
            self.assertIn("publishedAt", json_)
            if (pa := json_["publishedAt"]) is None:
                pass
            elif isinstance(pa, str):
                datetime.datetime.fromisoformat(pa)
            else:
                raise AssertionError("publishedAt is not null nor string")
            json_.pop("publishedAt")
            self.assertEqual(
                json_,
                {
                    "uuid": str(chapter1.uuid),
                    "index": chapter1.index,
                    "name": chapter1.name,
                    "markdown": chapter1.markdown,
                    "synopsis": chapter1.synopsis,
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

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.post(
            f"/story/{story.uuid}/chapter",
            json={
                "name": "Chapter 1",
                "synopsis": "Synopsis",
                "markdown": "Chapter Text",
            },
            user=user,
        )
        self.assertEqual(response.status_code, 200, response.content)

        json_ = response.json()
        uuid.UUID(json_.pop("uuid"))
        self.assertEqual(
            json_,
            {
                "name": "Chapter 1",
                "synopsis": "Synopsis",
                "index": 0,
            },
        )

    async def test_create_chapter_invalid(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        response = await test_client.post(
            f"/story/{story.uuid}/chapter",
            json={"name": "", "markdown": "Chapter Text", "synopsis": "Synopsis"},
            user=user,
        )
        self.assertEqual(response.status_code, 422, response.content)

        response = await test_client.post(
            f"/story/{story.uuid}/chapter",
            json={"name": "Chapter 1", "markdown": "", "synopsis": "Synopsis"},
            user=user,
        )
        self.assertEqual(response.status_code, 422, response.content)

    async def test_create_chapter_notfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        input_json = {
            "name": "Chapter 1",
            "markdown": "Chapter Text",
            "synopsis": "Synopsis",
        }
        response = await test_client.post(
            f"/story/{story.uuid}/chapter", json=input_json, user=alt_user
        )
        self.assertEqual(response.status_code, 404, response.content)

        response = await test_client.post(
            f"/story/{uuid.UUID(int=0)}/chapter", json=input_json, user=alt_user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_patch_chapter(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            synopsis="",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        response = await test_client.patch(
            f"/chapter/{chapter.uuid}", json={}, user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Chapter 1",
                "synopsis": "",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown", "synopsis"))
        self.assertEqual(chapter.name, "Chapter 1")
        self.assertEqual(chapter.markdown, "Chapter Text")
        self.assertEqual(chapter.synopsis, "")

        response = await test_client.patch(
            f"/chapter/{chapter.uuid}", json={"name": "Introduction"}, user=user
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Introduction",
                "synopsis": "",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown", "synopsis"))
        self.assertEqual(chapter.name, "Introduction")
        self.assertEqual(chapter.markdown, "Chapter Text")
        self.assertEqual(chapter.synopsis, "")

        response = await test_client.patch(
            f"/chapter/{chapter.uuid}",
            json={"markdown": "Introduction Text"},
            user=user,
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Introduction",
                "synopsis": "",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown", "synopsis"))
        self.assertEqual(chapter.name, "Introduction")
        self.assertEqual(chapter.markdown, "Introduction Text")
        self.assertEqual(chapter.synopsis, "")

        response = await test_client.patch(
            f"/chapter/{chapter.uuid}",
            json={"synopsis": "Synopsis"},
            user=user,
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Introduction",
                "synopsis": "Synopsis",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown", "synopsis"))
        self.assertEqual(chapter.name, "Introduction")
        self.assertEqual(chapter.markdown, "Introduction Text")
        self.assertEqual(chapter.synopsis, "Synopsis")

        response = await test_client.patch(
            f"/chapter/{chapter.uuid}",
            json={"synopsis": ""},
            user=user,
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "index": 0,
                "name": "Introduction",
                "synopsis": "",
                "uuid": str(chapter.uuid),
            },
        )
        await chapter.arefresh_from_db(fields=("name", "markdown", "synopsis"))
        self.assertEqual(chapter.name, "Introduction")
        self.assertEqual(chapter.markdown, "Introduction Text")
        self.assertEqual(chapter.synopsis, "")

    async def test_patch_chapter_notfound(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)
        alt_user = await User.objects.acreate_user("user2", "test2@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            synopsis="",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        input_json = {}
        response = await test_client.patch(
            f"/chapter/{chapter.uuid}", json=input_json, user=alt_user
        )
        self.assertEqual(response.status_code, 404, response.content)
        response = await test_client.patch(
            f"/chapter/{uuid.UUID(int=0)}", json=input_json, user=user
        )
        self.assertEqual(response.status_code, 404, response.content)

    async def test_delete_chapter(self):
        test_client = TestAsyncClient(router)

        user = await User.objects.acreate_user("user1", "test@test.com", None)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            synopsis="",
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

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = await Story.objects.acreate(
            title="Test Story",
            synopsis="Test Story Synopsis",
            creator=user,
            category=category,
        )

        chapter = await Chapter.objects.acreate(
            story=story,
            name="Chapter 1",
            synopsis="",
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
    async def test_list_categories(self):
        test_client = TestAsyncClient(router)

        response = await test_client.get("/category")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"count": 0, "items": []})

        await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        response = await test_client.get("/category")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"count": 1, "items": []})

    async def test_category_details(self):
        test_client = TestAsyncClient(router)

        category = await Category.objects.acreate(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        response = await test_client.get(f"/category/{category.name}")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "prettyName": category.pretty_name,
                "name": category.name,
                "description": "Description",
            },
        )

    async def test_category_details_notfound(self):
        test_client = TestAsyncClient(router)

        response = await test_client.get("/category/notfound")
        self.assertEqual(response.status_code, 404, response.content)

    @unittest.skip(
        "skip until https://github.com/vitalik/django-ninja/pull/1340 is resolved"
    )
    async def test_list_tags(self):
        test_client = TestAsyncClient(router)

        response = await test_client.get("/tag")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"count": 0, "items": []})

        await Tag.objects.acreate(name="test", pretty_name="Test")

        response = await test_client.get("/tag")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json(), {"count": 1, "items": []})

    async def test_tag_details(self):
        test_client = TestAsyncClient(router)

        tag = await Tag.objects.acreate(name="test", pretty_name="Test")

        response = await test_client.get(f"/tag/{tag.name}")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(
            response.json(),
            {
                "prettyName": tag.pretty_name,
                "name": tag.name,
            },
        )

    async def test_tag_details_notfound(self):
        test_client = TestAsyncClient(router)

        response = await test_client.get("/tag/notfound")
        self.assertEqual(response.status_code, 404, response.content)
