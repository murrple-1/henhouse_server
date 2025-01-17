from django.test import TestCase

from art.models import Tag


class TagTestCase(TestCase):
    def test_str(self):
        tag = Tag.objects.create(pretty_name="Test", name="test")
        self.assertEqual(str(tag), "Tag: Test (test)")
