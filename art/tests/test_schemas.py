import datetime
from unittest.mock import Mock

from django.http import HttpRequest
from django.test import SimpleTestCase, TestCase
from pydantic import ValidationError
from django.db.models import Q, F

from art.schemas import (
    ChapterInSchema,
    ChapterPatchInSchema,
    ListInSchema,
    StoryInSchema,
    StoryOutDetailsSchema,
    StoryOutSchema,
    StoryPatchInSchema,
)
from art.models import Chapter, Story
from app_admin.models import User


class SchemasTestCase(SimpleTestCase):
    def test_ListInSchema__get_filter_by_args(self):
        self.assertEqual(ListInSchema().get_filter_args("story", Mock(HttpRequest)), [])
        self.assertEqual(
            ListInSchema(search='title_exact:"test"').get_filter_args(
                "story", Mock(HttpRequest)
            ),
            [Q(title__iexact="test")],
        )

    def test_ListInSchema__get_order_by_args(self):
        self.assertEqual(ListInSchema().get_order_by_args("story"), [F("uuid").asc()])
        self.assertEqual(
            ListInSchema(sort="title:DESC").get_order_by_args("story"),
            [F("title").desc(), F("uuid").asc()],
        )

    def test_ListInSchema_default_sort_enabled(self):
        list_schema = ListInSchema.model_validate({})
        self.assertTrue(list_schema.default_sort_enabled)

        list_schema = ListInSchema.model_validate(
            {
                "defaultSortEnabled": False,
            }
        )
        self.assertFalse(list_schema.default_sort_enabled)

        list_schema = ListInSchema.model_validate(
            {
                "default_sort_enabled": False,
            }
        )
        self.assertTrue(list_schema.default_sort_enabled)

    def test_StoryInSchema(self):
        StoryInSchema(title="Title", synopsis="Synopsis", tags=[])
        StoryInSchema(title="Title", synopsis="Synopsis", tags=["tag"])

        with self.assertRaises(ValidationError):
            StoryInSchema(title="", synopsis="Synopsis", tags=["tag"])

        with self.assertRaises(ValidationError):
            StoryInSchema(title="Title", synopsis="", tags=["tag"])

    def test_StoryPatchInSchema(self):
        StoryPatchInSchema(title="Title", synopsis="Synopsis", tags=[])
        StoryPatchInSchema(title="Title", synopsis="Synopsis", tags=["tag"])

        with self.assertRaises(ValidationError):
            StoryPatchInSchema(title="")

        with self.assertRaises(ValidationError):
            StoryPatchInSchema(synopsis="")

    def test_ChapterInSchema(self):
        ChapterInSchema(name="Name", markdown="Markdown", synopsis="Synopsis")

        with self.assertRaises(ValidationError):
            ChapterInSchema(name="", markdown="Markdown", synopsis="Synopsis")

        with self.assertRaises(ValidationError):
            ChapterInSchema(name="Name", markdown="", synopsis="Synopsis")

    def test_ChapterPatchInSchema(self):
        ChapterPatchInSchema(name="Name", markdown="Markdown", synopsis="Synopsis")

        with self.assertRaises(ValidationError):
            ChapterPatchInSchema(name="")

        with self.assertRaises(ValidationError):
            ChapterPatchInSchema(markdown="")

    def test_StoryOutSchema_setattr_for_schema(self):
        story = Story(title="Test Story", synopsis="Test Story Synopsis")
        StoryOutSchema.setattr_for_schema(story)

    def test_StoryOutDetailsSchema_setattr_for_schema(self):
        story = Story(title="Test Story", synopsis="Test Story Synopsis")
        StoryOutDetailsSchema.setattr_for_schema(story)


class SchemasDBTestCase(TestCase):
    def test_StoryOutSchema_annotate_for_schema(self):
        user = User.objects.create_user("user1", "test@test.com", None)

        story = Story.objects.create(
            title="Test Story", synopsis="Test Story Synopsis", creator=user
        )

        self.assertIsNone(
            StoryOutSchema.annotate_for_schema(Story.objects.all())
            .get(uuid=story.uuid)
            .published_at
        )

        chapter = Chapter.objects.create(
            story=story,
            name="Chapter 1",
            synopsis="",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        self.assertIsNone(
            StoryOutSchema.annotate_for_schema(Story.objects.all())
            .get(uuid=story.uuid)
            .published_at
        )

        chapter.published_at = datetime.datetime(
            2000, 1, 1, 9, 0, tzinfo=datetime.timezone.utc
        )
        chapter.save(update_fields=("published_at",))

        self.assertIsNotNone(
            StoryOutSchema.annotate_for_schema(Story.objects.all())
            .get(uuid=story.uuid)
            .published_at
        )

    def test_StoryOutDetailsSchema_annotate_for_schema(self):
        user = User.objects.create_user("user1", "test@test.com", None)

        story = Story.objects.create(
            title="Test Story", synopsis="Test Story Synopsis", creator=user
        )

        self.assertIsNone(
            StoryOutDetailsSchema.annotate_for_schema(Story.objects.all())
            .get(uuid=story.uuid)
            .published_at
        )

        chapter = Chapter.objects.create(
            story=story,
            name="Chapter 1",
            synopsis="",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        self.assertIsNone(
            StoryOutDetailsSchema.annotate_for_schema(Story.objects.all())
            .get(uuid=story.uuid)
            .published_at
        )

        chapter.published_at = datetime.datetime(
            2000, 1, 1, 9, 0, tzinfo=datetime.timezone.utc
        )
        chapter.save(update_fields=("published_at",))

        self.assertIsNotNone(
            StoryOutDetailsSchema.annotate_for_schema(Story.objects.all())
            .get(uuid=story.uuid)
            .published_at
        )
