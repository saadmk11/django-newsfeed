from django.db import models
from django.utils import timezone


class IssueQuerySet(models.QuerySet):

    use_for_related_fields = True

    def released(self):
        return self.filter(
            is_draft=False,
            publish_date__lte=timezone.now()
        )


class SubscriberQuerySet(models.QuerySet):

    use_for_related_fields = True

    def subscribed(self):
        return self.filter(verified=True, subscribed=True)


class PostQuerySet(models.QuerySet):

    use_for_related_fields = True

    def visible(self):
        return self.filter(is_visible=True)
