from django.test import TestCase
from ninja.testing import TestClient

from art.api import router


class ApiTest(TestCase):
    def test_initial(self):
        client = TestClient(router)
        response = client.get("/story")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"items": [], "count": 0})
