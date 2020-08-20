from django.db import models
from django.utils import timezone


class IssueQuerySet(models.QuerySet):

    use_for_related_fields = True

    def released(self):
        return self.filter(
            is_draft=False,
            publish_date__lte=timezone.now()
        )
