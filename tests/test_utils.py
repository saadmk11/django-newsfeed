"""Tests for verification mail, newsletter delivery, and Ajax detection."""

from unittest import mock

import django
from django.core import mail
from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from newsfeed.app_settings import get_from_email
from newsfeed.models import Issue, Newsletter, Subscriber
from newsfeed.utils.check_ajax import is_ajax
from newsfeed.utils.send_newsletters import (
    NewsletterEmailSender,
    send_email_newsletter,
)
from newsfeed.utils.send_verification import (
    send_subscription_verification_email,
)


class SendSubscriptionVerificationEmailTest(TestCase):
    """Send Subscription Verification Email Test."""

    def setUp(self) -> None:
        """Create the objects used by this test."""
        self.unverified_subscriber = baker.make(
            Subscriber,
            subscribed=False,
            verified=False,
        )

    def test_send_subscription_verification_email(self) -> None:
        """Test that send subscription verification email."""
        send_subscription_verification_email(
            self.unverified_subscriber.get_verification_url(),
            self.unverified_subscriber.email_address,
        )

        assert len(mail.outbox) == 1
        assert mail.outbox[0].subject == "Please Confirm Your Subscription"
        assert mail.outbox[0].to == [self.unverified_subscriber.email_address]
        assert (
            self.unverified_subscriber.get_verification_url()
            in mail.outbox[0].body
        )
        assert mail.outbox[0].from_email == self.expected_from_email()

    @staticmethod
    def expected_from_email() -> str:
        """Return the From address used by the active Django version.

        Returns:
            ``DEFAULT_FROM_EMAIL`` on Django 6.1 and ``EMAIL_HOST_USER`` before
            that.

        """
        if django.VERSION >= (6, 1):
            return "news@example.com"
        return "test_user"

    @override_settings(
        MAILERS={
            "default": {
                "BACKEND": ("django.core.mail.backends.locmem.EmailBackend"),
            },
        },
        DEFAULT_FROM_EMAIL="mailers@example.com",
    )
    def test_verification_email_uses_default_from_when_mailers_is_set(
        self,
    ) -> None:
        """Test that mailers use the default From address."""
        send_subscription_verification_email(
            self.unverified_subscriber.get_verification_url(),
            self.unverified_subscriber.email_address,
        )

        assert len(mail.outbox) == 1
        assert mail.outbox[0].from_email == "mailers@example.com"
        assert get_from_email() == "mailers@example.com"


class SendNewsletterEmailTest(TestCase):
    """Send Newsletter Email Test."""

    def setUp(self) -> None:
        # Subscribers
        """Create the objects used by this test."""
        self.unverified_subscribers = baker.make(
            Subscriber,
            subscribed=False,
            verified=False,
            _quantity=2,
        )
        self.verified_subscribers = baker.make(
            Subscriber,
            subscribed=True,
            verified=True,
            _quantity=5,
        )
        # Issues
        self.released_issue = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_issue_2 = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_issue_3 = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.unreleased_issue = baker.make(
            Issue,
            is_draft=True,
        )
        # Newsletters
        self.released_newsletter_1 = baker.make(
            Newsletter,
            issue=self.released_issue,
            is_sent=False,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_newsletter_2 = baker.make(
            Newsletter,
            issue=self.released_issue_2,
            is_sent=False,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.sent_newsletter = baker.make(
            Newsletter,
            issue=self.released_issue_3,
            is_sent=True,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.unreleased_newsletter = baker.make(
            Newsletter,
            issue=self.unreleased_issue,
            is_sent=False,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.future_scheduled_newsletter = baker.make(
            Newsletter,
            issue=self.released_issue,
            is_sent=False,
            schedule=timezone.now() + timezone.timedelta(days=1),
        )

    def test_send_email_newsletter(self) -> None:
        """Test that send email newsletter."""
        newsletters = Newsletter.objects.filter(
            id__in=[
                self.released_newsletter_1.id,
                self.released_newsletter_2.id,
            ],
            is_sent=True,
        )
        assert not newsletters.exists()

        send_email_newsletter()

        sent_messages = 10
        assert len(mail.outbox) == sent_messages
        assert mail.outbox[0].subject == self.released_newsletter_1.subject
        assert mail.outbox[5].subject == self.released_newsletter_2.subject
        if django.VERSION >= (6, 1):
            assert mail.outbox[0].from_email == "news@example.com"
        else:
            assert mail.outbox[0].from_email == "test_user"

        assert newsletters.exists()

    def test_send_email_newsletter_custom_queryset(self) -> None:
        """Test that send email newsletter custom queryset."""
        newsletters = Newsletter.objects.filter(
            id__in=[
                self.released_newsletter_1.id,
                self.released_newsletter_2.id,
            ],
        )
        assert not newsletters.filter(is_sent=True).exists()

        send_email_newsletter(newsletters=newsletters)

        sent_messages = 10
        assert len(mail.outbox) == sent_messages
        assert mail.outbox[0].subject == self.released_newsletter_1.subject
        assert mail.outbox[5].subject == self.released_newsletter_2.subject

        assert newsletters.filter(is_sent=True).exists()

    @override_settings(
        MAILERS={
            "default": {
                "BACKEND": ("django.core.mail.backends.locmem.EmailBackend"),
            },
        },
        DEFAULT_FROM_EMAIL="mailers@example.com",
    )
    def test_send_email_newsletter_when_mailers_is_set(self) -> None:
        """Test that send email newsletter when mailers is set."""
        send_email_newsletter(
            newsletters=Newsletter.objects.filter(
                id=self.released_newsletter_1.id,
            ),
        )

        sent_messages = 5
        assert len(mail.outbox) == sent_messages
        assert mail.outbox[0].from_email == "mailers@example.com"

    @mock.patch("newsfeed.utils.send_newsletters.logger")
    def test_send_email_newsletter_with_error(
        self,
        logger: mock.MagicMock,
    ) -> None:
        """Test that send email newsletter with error."""
        send_newsletter = NewsletterEmailSender()
        send_newsletter.connection.send_messages = mock.Mock(
            side_effect=Exception(),
        )
        send_newsletter.send_emails()
        logger.exception.assert_called()

    def test_send_email_newsletter_with_no_subscribers(self) -> None:
        """Test that send email newsletter with no subscribers."""
        newsletters = Newsletter.objects.filter(
            id__in=[
                self.released_newsletter_1.id,
                self.released_newsletter_2.id,
            ],
        )
        assert not newsletters.filter(is_sent=True).exists()

        Subscriber.objects.all().update(subscribed=False)
        send_newsletter = NewsletterEmailSender()
        send_newsletter.send_emails()

        assert not newsletters.filter(is_sent=True).exists()

    def test_send_email_newsletter_dont_respect_schedule(self) -> None:
        """Test that send email newsletter dont respect schedule."""
        newsletters = Newsletter.objects.filter(
            id__in=[
                self.released_newsletter_1.id,
                self.released_newsletter_2.id,
                self.future_scheduled_newsletter.id,
            ],
            is_sent=True,
        )
        assert not newsletters.exists()

        send_email_newsletter(respect_schedule=False)

        sent_messages = 15
        assert len(mail.outbox) == sent_messages
        assert mail.outbox[0].subject == self.released_newsletter_1.subject
        assert mail.outbox[5].subject == self.released_newsletter_2.subject
        assert (
            mail.outbox[10].subject == self.future_scheduled_newsletter.subject
        )

        assert newsletters.exists()

    def testrender_newsletter(self) -> None:
        """Test that render newsletter."""
        rendered = NewsletterEmailSender.render_newsletter(
            self.released_newsletter_1,
        )

        assert rendered["subject"] == self.released_newsletter_1.subject
        assert isinstance(rendered, dict)

    def testgenerate_email_message(self) -> None:
        """Test that generate email message."""
        rendered = NewsletterEmailSender.render_newsletter(
            self.released_newsletter_1,
        )
        send_newsletter = NewsletterEmailSender()
        message = send_newsletter.generate_email_message(
            "test@test.com",
            rendered,
        )

        assert message.subject == self.released_newsletter_1.subject
        assert message.body == rendered["html"]
        assert message.to == ["test@test.com"]

    def test_get_subscriber_emails(self) -> None:
        """Test that get subscriber emails."""
        rendered = NewsletterEmailSender.render_newsletter(
            self.released_newsletter_1,
        )
        send_newsletter = NewsletterEmailSender()
        # set batch size to 2
        send_newsletter.batch_size = 2

        email_msg_generator = send_newsletter.iter_email_batches(
            rendered,
        )

        # total five subscribed emails were added in the setUp()
        first_batch = 2
        second_batch = 2
        assert len(list(next(email_msg_generator))) == first_batch
        assert len(list(next(email_msg_generator))) == second_batch
        assert len(list(next(email_msg_generator))) == 1

    def test_get_subscriber_emails_return_email_message_instances(self) -> None:
        """Test that get subscriber emails return email message instances."""
        rendered = NewsletterEmailSender.render_newsletter(
            self.released_newsletter_1,
        )
        send_newsletter = NewsletterEmailSender()

        email_msg_generator = send_newsletter.iter_email_batches(
            rendered,
        )

        messages = list(next(email_msg_generator))

        assert isinstance(messages[0], mail.EmailMessage)

    def test_get_subscriber_emails_with_zero_subscribers(self) -> None:
        """Test that get subscriber emails with zero subscribers."""
        Subscriber.objects.all().update(subscribed=False)

        rendered = NewsletterEmailSender.render_newsletter(
            self.released_newsletter_1,
        )
        send_newsletter = NewsletterEmailSender()

        email_msg_generator = send_newsletter.iter_email_batches(
            rendered,
        )

        with self.assertRaises(StopIteration):
            next(email_msg_generator)


class CheckAjaxTest(TestCase):
    """Check Ajax Test."""

    def test_request_is_ajax(self) -> None:
        """Test that request is ajax."""
        factory = RequestFactory()
        request = factory.get(
            reverse("newsfeed:newsletter_subscribe"),
            data={"email_address": "test@test.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        assert is_ajax(request)

    def test_request_is_not_ajax(self) -> None:
        """Test that request is not ajax."""
        factory = RequestFactory()
        request = factory.get(
            reverse("newsfeed:newsletter_subscribe"),
            data={"email_address": "test@test.com"},
        )
        assert not is_ajax(request)
