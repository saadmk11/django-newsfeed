"""Application configuration for the newsfeed app."""

from django.apps import AppConfig


class NewsfeedConfig(AppConfig):
    """Newsfeed Config."""

    name = "newsfeed"
    # Migrations already create AutoField primary keys. Pinning the app
    # default keeps a project-level BigAutoField from rewriting them.
    default_auto_field = "django.db.models.AutoField"
