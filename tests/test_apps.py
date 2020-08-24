from django.apps import apps
from django.test import TestCase

from newsfeed.apps import NewsfeedConfig


class NewsfeedConfigTest(TestCase):

    def test_apps(self):
        self.assertEqual(NewsfeedConfig.name, 'newsfeed')
        self.assertEqual(apps.get_app_config('newsfeed').name, 'newsfeed')
