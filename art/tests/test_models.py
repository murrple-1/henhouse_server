from django.test import SimpleTestCase

from art.models import Tag, Category


class CategoryTestCase(SimpleTestCase):
    def test_str(self):
        category = Category(pretty_name="Test", name="test")
        self.assertEqual(str(category), "Category: Test (test)")


class TagTestCase(SimpleTestCase):
    def test_str(self):
        tag = Tag(pretty_name="Test", name="test")
        self.assertEqual(str(tag), "Tag: Test (test)")
