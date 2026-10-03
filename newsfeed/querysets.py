"""Querysets for published issues, visible posts, and active subscribers."""

from typing import Self

from django.db import models
from django.utils import timezone


class IssueQuerySet(models.QuerySet):
    """Queryset for newsletter issues."""

    def released(self) -> Self:
        """Return issues that are public.

        Returns:
            Issues that are not drafts and whose publish date has passed.

        """
        return self.filter(
            is_draft=False,
            publish_date__lte=timezone.now(),
        )


class SubscriberQuerySet(models.QuerySet):
    """Queryset for newsletter subscribers."""

    def subscribed(self) -> Self:
        """Return subscribers who can receive newsletters.

        Returns:
            Subscribers that are verified and still subscribed.

        """
        return self.filter(verified=True, subscribed=True)


class PostQuerySet(models.QuerySet):
    """Queryset for issue posts."""

    def visible(self) -> Self:
        """Return posts that should be shown.

        Returns:
            Posts marked visible.

        """
        return self.filter(is_visible=True)
