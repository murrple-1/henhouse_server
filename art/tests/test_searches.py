import uuid
from typing import Any, Callable, ClassVar, TypedDict
from unittest.mock import Mock

from django.db.models import QuerySet
from django.db.models.manager import BaseManager
from django.http import HttpRequest
from django.test import TestCase

from app_admin.models import User
from art import searches
from art.models import Chapter, Story, Tag


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
            },
        },
        "chapter": {
            "get_queryset": lambda: Chapter.annotate_search_vectors(
                Chapter.objects.all()
            ),
            "searches": {
                "uuid": [str(uuid.uuid4())],
                "name": ["test"],
                "name_exact": ["test"],
                "text": ["test"],
            },
        },
        "tag": {
            "get_queryset": lambda: Tag.objects.all(),
            "searches": {
                "uuid": [str(uuid.uuid4())],
                "name": ["test"],
                "name_exact": ["test"],
                "prettyName": ["test"],
                "prettyName_exact": ["test"],
                "description": ["test"],
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
