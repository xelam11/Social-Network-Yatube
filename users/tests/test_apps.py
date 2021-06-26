from django.test import TestCase
from users.apps import UsersConfig


class ReportsConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(UsersConfig.name, "users")
