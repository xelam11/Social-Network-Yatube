from django.test import TestCase
from about.apps import AboutConfig


class ReportsConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(AboutConfig.name, "about")
