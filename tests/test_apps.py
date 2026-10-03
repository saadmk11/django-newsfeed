"""Tests for the newsfeed application configuration."""

from django.apps import apps
from django.test import TestCase
from newsfeed.apps import NewsfeedConfig


class NewsfeedConfigTest(TestCase):
    """Newsfeed Config Test."""

    def test_apps(self) -> None:
        """Test that apps."""
        assert NewsfeedConfig.name == "newsfeed"
        assert apps.get_app_config("newsfeed").name == "newsfeed"
        assert (
            apps.get_app_config("newsfeed").default_auto_field
            == "django.db.models.AutoField"
        )
