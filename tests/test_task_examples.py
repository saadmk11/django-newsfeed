"""The README task examples send the newsletters they are given."""

import django
from django.core import mail
from django.test import TestCase
from django.utils import timezone
from model_bakery import baker
from newsfeed.models import Issue, Newsletter, Subscriber
from newsfeed.utils.send_newsletters import send_email_newsletter

if django.VERSION >= (6, 0):
    from django.tasks import task
else:
    task = None


def send_selected_newsletters(
    newsletter_ids: list[int],
    *,
    respect_schedule: bool = False,
) -> None:
    """Send the newsletters named by the task payload.

    Args:
        newsletter_ids: Primary keys received from the task runner.
        respect_schedule: Skip newsletters whose schedule is still in the
            future.

    """
    send_email_newsletter(
        newsletters=Newsletter.objects.filter(pk__in=newsletter_ids),
        respect_schedule=respect_schedule,
    )


class TaskExampleTest(TestCase):
    """Task Example Test."""

    def setUp(self) -> None:
        """Create one future newsletter and one confirmed subscriber."""
        self.issue = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.newsletter = baker.make(
            Newsletter,
            issue=self.issue,
            is_sent=False,
            schedule=timezone.now() + timezone.timedelta(days=1),
        )
        baker.make(
            Subscriber,
            email_address="reader@example.com",
            subscribed=True,
            verified=True,
        )

    def test_task_body_sends_the_selected_newsletter(self) -> None:
        """A task body loads newsletters by primary key and sends them."""
        send_selected_newsletters(
            newsletter_ids=[self.newsletter.pk],
            respect_schedule=False,
        )

        sent_messages = 1
        assert len(mail.outbox) == sent_messages
        self.newsletter.refresh_from_db()
        assert self.newsletter.is_sent

    def test_django_task_enqueues_the_same_call(self) -> None:
        """Django's task framework can run the documented call."""
        if task is None:
            self.skipTest("Django tasks were added in Django 6.0.")

        documented_task = task(send_selected_newsletters)
        documented_task.enqueue(
            newsletter_ids=[self.newsletter.pk],
            respect_schedule=False,
        )

        sent_messages = 1
        assert len(mail.outbox) == sent_messages
        self.newsletter.refresh_from_db()
        assert self.newsletter.is_sent
