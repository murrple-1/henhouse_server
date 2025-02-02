import uuid
from typing import Any, Callable, ClassVar, TypedDict
from unittest.mock import Mock

from django.db.models import QuerySet
from django.db.models.manager import BaseManager
from django.http import HttpRequest
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from app_admin.models import User
from art import searches
from art.models import Category, Chapter, Story, Tag


class CustomConvertToTestCase(SimpleTestCase):
    def test_StrList(self):
        self.assertEqual(searches.StrList.convertto(""), [""])
        self.assertEqual(searches.StrList.convertto("test"), ["test"])
        self.assertEqual(searches.StrList.convertto("test1,test2"), ["test1", "test2"])


class AllSearchesTestCase(TestCase):
    user: ClassVar[User]

    class _Trial(TypedDict):
        get_queryset: Callable[[], BaseManager | QuerySet[Any]]
        searches: dict[str, list[Any]]

    TRIALS: dict[str, _Trial] = {
        "story": {
            "get_queryset": lambda: Story.annotate_search_vectors(Story.objects.all()),
            "searches": {
                "uuid": [str(uuid.uuid4())],
                "title": ["test"],
                "title_exact": ["test"],
                "storyText": ["test"],
                "synopsis": ["test"],
                "author": [str(uuid.uuid4())],
                "category": ["test", "test1,test2"],
                "createdAt": ["2018-11-23 00:00:00+0000|2018-11-26 00:00:00+0000"],
                "createdAt_exact": ["2018-11-26 00:00:00+0000"],
                "createdAt_delta": ["older_than:10h"],
                "publishedAt": ["2018-11-23 00:00:00+0000|2018-11-26 00:00:00+0000"],
                "publishedAt_exact": ["2018-11-26 00:00:00+0000"],
                "publishedAt_delta": ["older_than:10h"],
                "isPublished": ["true", "false"],
                "tags": ["disney", "marvel,spongebob"],
                "authorName": ["test"],
            },
        },
        "chapter": {
            "get_queryset": lambda: Chapter.annotate_search_vectors(
                Chapter.objects.all()
            ),
            "searches": {
                "uuid": [str(uuid.uuid4())],
                "story": [str(uuid.uuid4())],
                "name": ["test"],
                "name_exact": ["test"],
                "text": ["test"],
                "synopsis": ["test"],
                "createdAt": ["2018-11-23 00:00:00+0000|2018-11-26 00:00:00+0000"],
                "createdAt_exact": ["2018-11-26 00:00:00+0000"],
                "createdAt_delta": ["older_than:10h"],
                "publishedAt": ["2018-11-23 00:00:00+0000|2018-11-26 00:00:00+0000"],
                "publishedAt_exact": ["2018-11-26 00:00:00+0000"],
                "publishedAt_delta": ["older_than:10h"],
                "isPublished": ["true", "false"],
            },
        },
        "category": {
            "get_queryset": lambda: Category.objects.all(),
            "searches": {
                "name": ["test"],
                "name_exact": ["test"],
                "prettyName": ["test"],
                "prettyName_exact": ["test"],
            },
        },
        "tag": {
            "get_queryset": lambda: Tag.objects.all(),
            "searches": {
                "name": ["test"],
                "name_exact": ["test"],
                "prettyName": ["test"],
                "prettyName_exact": ["test"],
            },
        },
    }

    class MockRequest(Mock):
        def __init__(self):
            super().__init__(HttpRequest)
            self.user = AllSearchesTestCase.user

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.user = User.objects.create_user("user1", "test_searches@test.com", None)

    def test_run(self):
        self.assertEqual(len(AllSearchesTestCase.TRIALS), len(searches.search_fns))

        for key, trial_dict in AllSearchesTestCase.TRIALS.items():
            with self.subTest(key=key):
                search_fns_dict = searches.search_fns[key]

                trial_searches = trial_dict["searches"]
                self.assertEqual(len(trial_searches), len(search_fns_dict))

                queryset = trial_dict["get_queryset"]()

                for field, test_values in trial_searches.items():
                    for test_value in test_values:
                        with self.subTest(field=field, test_value=test_value):
                            q = search_fns_dict[field](
                                AllSearchesTestCase.MockRequest(),
                                test_value,
                            )
                            result = list(queryset.filter(q))

                            self.assertIsNotNone(result)


class SearchesTestCase(TestCase):
    def test_story_isPublished(self):
        user = User.objects.create_user("user1", "test@test.com", None)

        category = Category.objects.create(
            name="test", pretty_name="Test", description="Description", sort_key=0
        )

        story = Story.objects.create(
            title="Test Story",
            synopsis="Test Story Synopsis",
            author=user,
            category=category,
        )

        self.assertEqual(
            Story.objects.filter(
                searches._story_isPublished(Mock(HttpRequest), "true")
            ).count(),
            0,
        )
        self.assertGreater(
            Story.objects.filter(
                searches._story_isPublished(Mock(HttpRequest), "false")
            ).count(),
            0,
        )

        chapter = Chapter.objects.create(
            story=story,
            name="Chapter 1",
            synopsis="",
            index=0,
            markdown="Chapter Text",
            published_at=None,
        )

        self.assertEqual(
            Story.objects.filter(
                searches._story_isPublished(Mock(HttpRequest), "true")
            ).count(),
            0,
        )
        self.assertGreater(
            Story.objects.filter(
                searches._story_isPublished(Mock(HttpRequest), "false")
            ).count(),
            0,
        )

        chapter.published_at = timezone.now()
        chapter.save(update_fields=("published_at",))

        self.assertGreater(
            Story.objects.filter(
                searches._story_isPublished(Mock(HttpRequest), "true")
            ).count(),
            0,
        )
        self.assertEqual(
            Story.objects.filter(
                searches._story_isPublished(Mock(HttpRequest), "false")
            ).count(),
            0,
        )
