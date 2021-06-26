from django.test import TestCase
from posts.apps import PostsConfig


class ReportsConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(PostsConfig.name, "posts")
