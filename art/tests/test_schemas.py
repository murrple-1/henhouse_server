from unittest.mock import Mock

from django.http import HttpRequest
from django.test import SimpleTestCase
from pydantic import ValidationError
from django.db.models import Q, F

from art.schemas import ChapterInSchema, ListSchema


class SchemasTestCase(SimpleTestCase):
    def test_ListSchema__get_filter_by_args(self):
        self.assertEqual(ListSchema().get_filter_args("story", Mock(HttpRequest)), [])
        self.assertEqual(
            ListSchema(search='title_exact:"test"').get_filter_args(
                "story", Mock(HttpRequest)
            ),
            [Q(title__iexact="test")],
        )

    def test_ListSchema__get_order_by_args(self):
        self.assertEqual(ListSchema().get_order_by_args("story"), [F("uuid").asc()])
        self.assertEqual(
            ListSchema(sort="title:DESC").get_order_by_args("story"),
            [F("title").desc(), F("uuid").asc()],
        )

    def test_ListSchema_default_sort_enabled(self):
        list_schema = ListSchema.model_validate({})
        self.assertTrue(list_schema.default_sort_enabled)

        list_schema = ListSchema.model_validate(
            {
                "defaultSortEnabled": False,
            }
        )
        self.assertFalse(list_schema.default_sort_enabled)

        list_schema = ListSchema.model_validate(
            {
                "default_sort_enabled": False,
            }
        )
        self.assertTrue(list_schema.default_sort_enabled)

    def test_ChapterInSchema(self):
        ChapterInSchema(name="Name", markdown="Markdown")

        with self.assertRaises(ValidationError):
            ChapterInSchema(name="", markdown="Markdown")

        with self.assertRaises(ValidationError):
            ChapterInSchema(name="Name", markdown="")
