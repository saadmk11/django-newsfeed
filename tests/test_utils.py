from django.core import mail
from django.test import TestCase
from django.utils import timezone

from model_bakery import baker

from newsfeed.models import Issue, Subscriber, Newsletter
from newsfeed.utils.send_verification import (
    send_subscription_verification_email
)
from newsfeed.utils.send_newsletters import (
    generate_email_message,
    get_subscriber_emails,
    render_newsletter,
    send_email_newsletter,
)


class SendSubscriptionVerificationEmailTest(TestCase):

    def setUp(self):
        self.unverified_subscriber = baker.make(
            Subscriber, subscribed=False, verified=False
        )

    def test_send_subscription_verification_email(self):
        send_subscription_verification_email(
            self.unverified_subscriber.get_verification_url(),
            self.unverified_subscriber.email_address
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'Please Confirm Your Subscription'
        )
        self.assertEqual(
            mail.outbox[0].to,
            [self.unverified_subscriber.email_address]
        )
        self.assertIn(
            self.unverified_subscriber.get_verification_url(),
            mail.outbox[0].body
        )


class SendNewsletterEmailTest(TestCase):

    def setUp(self):
        # Subscribers
        self.unverified_subscribers = baker.make(
            Subscriber, subscribed=False, verified=False, _quantity=2
        )
        self.verified_subscribers = baker.make(
            Subscriber, subscribed=True, verified=True, _quantity=5
        )
        # Issues
        self.released_issue = baker.make(
            Issue, is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_issue_2 = baker.make(
            Issue, is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_issue_3 = baker.make(
            Issue, is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.unreleased_issue = baker.make(
            Issue, is_draft=True,
        )
        # Newsletters
        self.released_newsletter_1 = baker.make(
            Newsletter, issue=self.released_issue, is_sent=False,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_newsletter_2 = baker.make(
            Newsletter, issue=self.released_issue_2, is_sent=False,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.sent_newsletter = baker.make(
            Newsletter, issue=self.released_issue_3, is_sent=True,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.unreleased_newsletter = baker.make(
            Newsletter, issue=self.unreleased_issue, is_sent=False,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.future_scheduled_newsletter = baker.make(
            Newsletter, issue=self.released_issue, is_sent=False,
            schedule=timezone.now() + timezone.timedelta(days=1),
        )

    def test_send_email_newsletter(self):
        newsletters = Newsletter.objects.filter(
            id__in=[
                self.released_newsletter_1.id,
                self.released_newsletter_2.id
            ],
            is_sent=True
        )
        self.assertFalse(newsletters.exists())

        send_email_newsletter()

        self.assertEqual(len(mail.outbox), 10)
        self.assertEqual(
            mail.outbox[0].subject,
            self.released_newsletter_1.subject
        )
        self.assertEqual(
            mail.outbox[5].subject,
            self.released_newsletter_2.subject
        )

        self.assertTrue(newsletters.exists())

    def test_send_email_newsletter_custom_queryset(self):
        newsletters = Newsletter.objects.filter(
            id__in=[
                self.released_newsletter_1.id,
                self.released_newsletter_2.id
            ]
        )
        self.assertFalse(newsletters.filter(is_sent=True).exists())

        send_email_newsletter(newsletters=newsletters)

        self.assertEqual(len(mail.outbox), 10)
        self.assertEqual(
            mail.outbox[0].subject,
            self.released_newsletter_1.subject
        )
        self.assertEqual(
            mail.outbox[5].subject,
            self.released_newsletter_2.subject
        )

        self.assertTrue(newsletters.filter(is_sent=True).exists())

    def test_send_email_newsletter_dont_respect_schedule(self):
        newsletters = Newsletter.objects.filter(
            id__in=[
                self.released_newsletter_1.id,
                self.released_newsletter_2.id,
                self.future_scheduled_newsletter.id,
            ],
            is_sent=True
        )
        self.assertFalse(newsletters.exists())

        send_email_newsletter(respect_schedule=False)

        self.assertEqual(len(mail.outbox), 15)
        self.assertEqual(
            mail.outbox[0].subject,
            self.released_newsletter_1.subject
        )
        self.assertEqual(
            mail.outbox[5].subject,
            self.released_newsletter_2.subject
        )
        self.assertEqual(
            mail.outbox[10].subject,
            self.future_scheduled_newsletter.subject
        )

        self.assertTrue(newsletters.exists())

    def test_render_newsletter(self):
        rendered = render_newsletter(self.released_newsletter_1)

        self.assertEqual(
            rendered['subject'],
            self.released_newsletter_1.subject
        )
        self.assertEqual(type(rendered), dict)

    def test_generate_email_message(self):
        rendered = render_newsletter(self.released_newsletter_1)
        message = generate_email_message('test@test.com', rendered, None)

        self.assertEqual(
            message.subject,
            self.released_newsletter_1.subject
        )
        self.assertEqual(message.body, rendered['html'])
        self.assertEqual(message.to, ['test@test.com'])

    def test_get_subscriber_emails(self):
        rendered = render_newsletter(self.released_newsletter_1)

        emails = [
            subscriber.email_address
            for subscriber in self.verified_subscribers
        ]

        email_msg_generator = get_subscriber_emails(
            rendered, emails, 2, None
        )

        # total five subscribed emails were added in the setUp()
        self.assertEqual(len(list(next(email_msg_generator))), 2)
        self.assertEqual(len(list(next(email_msg_generator))), 2)
        self.assertEqual(len(list(next(email_msg_generator))), 1)

    def test_get_subscriber_emails_return_email_message_instances(self):
        rendered = render_newsletter(self.released_newsletter_1)

        email_msg_generator = get_subscriber_emails(
            rendered, [self.verified_subscribers[0].email_address],
            2, None
        )

        messages = list(next(email_msg_generator))

        self.assertTrue(isinstance(messages[0], mail.EmailMessage))

    def test_get_subscriber_emails_with_zero_subscribers(self):
        Subscriber.objects.all().update(subscribed=False)
        rendered = render_newsletter(self.released_newsletter_1)

        email_msg_generator = get_subscriber_emails(rendered, [], 0, None)

        with self.assertRaises(StopIteration):
            next(email_msg_generator)
