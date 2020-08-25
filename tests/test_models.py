from unittest import mock

from django.test import TestCase
from django.utils import timezone

from model_bakery import baker

from newsfeed.models import Issue, Newsletter, Post, PostCategory, Subscriber


class PostModelTest(TestCase):

    def setUp(self):
        self.invisible_posts = baker.make(Post, is_visible=False, _quantity=2)
        self.visible_posts = baker.make(Post, is_visible=True, _quantity=2)

    def test_str(self):
        post = Post.objects.visible().first()
        self.assertEqual(post.title, str(post))

    def test_visible_queryset(self):
        posts = Post.objects.visible()

        self.assertEqual(posts.count(), 2)

    def test_all_queryset(self):
        posts = Post.objects.all()

        self.assertEqual(posts.count(), 4)


class IssueModelTest(TestCase):

    def setUp(self):
        self.released_issue = baker.make(
            Issue, is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.unreleased_issue = baker.make(
            Issue, is_draft=True,
        )

    def test_str(self):
        issue = Issue.objects.released().first()
        self.assertEqual(issue.title, str(issue))

    def test_all_queryset(self):
        issues = Issue.objects.all()

        self.assertEqual(issues.count(), 2)

    def test_released_queryset(self):
        issues = Issue.objects.released()

        self.assertEqual(issues.count(), 1)

    def test_released_with_future_released_date_queryset(self):
        future_issue = baker.make(
            Issue, is_draft=False,
            publish_date=timezone.now() + timezone.timedelta(days=1),
        )
        future_issue_exists = Issue.objects.released().filter(
            id=future_issue.id
        ).exists()

        self.assertFalse(future_issue_exists)

    def test_is_published(self):
        self.assertTrue(self.released_issue.is_published)
        self.assertFalse(self.unreleased_issue.is_published)

    def test_get_absolute_url(self):
        expected_url = f'/newsfeed/issues/{self.released_issue.issue_number}/'
        self.assertEqual(self.released_issue.get_absolute_url(), expected_url)


class SubscriberModelTest(TestCase):

    def setUp(self):
        self.verified_subscriber = baker.make(
            Subscriber, subscribed=True, verified=True
        )
        self.unverified_subscriber = baker.make(
            Subscriber, subscribed=False, verified=False
        )

    def test_str(self):
        subscriber = Subscriber.objects.subscribed().first()
        self.assertEqual(subscriber.email_address, str(subscriber))

    def test_all_queryset(self):
        subscribers = Subscriber.objects.all()

        self.assertEqual(subscribers.count(), 2)

    def test_subscribed_queryset(self):
        subscribers = Subscriber.objects.subscribed()

        self.assertEqual(subscribers.count(), 1)

    def test_token_expired(self):
        self.unverified_subscriber.verification_sent_date = (
            timezone.now() - timezone.timedelta(days=3)
        )
        self.unverified_subscriber.save()

        self.assertTrue(self.unverified_subscriber.token_expired())

    def test_token_not_expired(self):
        self.unverified_subscriber.verification_sent_date = timezone.now()
        self.unverified_subscriber.save()

        self.assertFalse(self.unverified_subscriber.token_expired())

    def test_token_expired_with_no_verification_sent_date(self):
        self.unverified_subscriber.verification_sent_date = None
        self.unverified_subscriber.save()

        self.assertTrue(self.unverified_subscriber.token_expired())

    def test_reset_token(self):
        old_token = self.unverified_subscriber.token
        self.unverified_subscriber.reset_token()

        self.assertNotEqual(old_token, self.unverified_subscriber.token)

    @mock.patch('newsfeed.models.uuid')
    def test_reset_token_with_existing_token(self, uuid):
        old_token = self.unverified_subscriber.token
        new_token = 'new_token'
        uuid.uuid4.side_effect = [old_token, new_token]

        self.unverified_subscriber.reset_token()

        self.assertNotEqual(old_token, self.unverified_subscriber.token)
        self.assertEqual(new_token, self.unverified_subscriber.token)

    def test_subscribe(self):
        self.unverified_subscriber.verification_sent_date = timezone.now()
        self.unverified_subscriber.save()

        self.assertFalse(self.unverified_subscriber.verified)
        self.assertFalse(self.unverified_subscriber.subscribed)

        subscribed = self.unverified_subscriber.subscribe()

        self.assertTrue(subscribed)
        self.assertTrue(self.unverified_subscriber.verified)
        self.assertTrue(self.unverified_subscriber.subscribed)

    def test_subscribe_with_expired_token(self):
        self.unverified_subscriber.verification_sent_date = (
            timezone.now() - timezone.timedelta(days=3)
        )
        self.unverified_subscriber.save()

        self.assertTrue(self.unverified_subscriber.token_expired())
        self.assertFalse(self.unverified_subscriber.verified)
        self.assertFalse(self.unverified_subscriber.subscribed)

        subscribed = self.unverified_subscriber.subscribe()

        self.assertFalse(subscribed)
        self.assertFalse(self.unverified_subscriber.verified)
        self.assertFalse(self.unverified_subscriber.subscribed)

    def test_unsubscribe_with_unsubscribed_email(self):
        self.assertFalse(self.unverified_subscriber.verified)
        self.assertFalse(self.unverified_subscriber.subscribed)

        unsubscribed = self.unverified_subscriber.unsubscribe()

        self.assertFalse(unsubscribed)
        self.assertFalse(self.unverified_subscriber.verified)
        self.assertFalse(self.unverified_subscriber.subscribed)

    def test_unsubscribe(self):
        self.assertTrue(self.verified_subscriber.verified)
        self.assertTrue(self.verified_subscriber.subscribed)

        unsubscribed = self.verified_subscriber.unsubscribe()

        self.assertTrue(unsubscribed)
        self.assertFalse(self.verified_subscriber.verified)
        self.assertFalse(self.verified_subscriber.subscribed)

    @mock.patch('newsfeed.models.send_subscription_verification_email')
    def test_send_verification_email_with_existing_email(
        self, send_verification_email
    ):
        old_token = self.unverified_subscriber.token

        self.unverified_subscriber.send_verification_email(False)

        self.assertNotEqual(self.unverified_subscriber.token, old_token)
        send_verification_email.assert_called_once_with(
            self.unverified_subscriber.get_verification_url(),
            self.unverified_subscriber.email_address
        )

    @mock.patch('newsfeed.models.send_subscription_verification_email')
    def test_send_verification_email_with_new_email(
        self, send_verification_email
    ):
        new_unverified_subscriber = baker.make(
            Subscriber, subscribed=False, verified=False
        )
        old_token = new_unverified_subscriber.token

        new_unverified_subscriber.send_verification_email(True)

        self.assertEqual(new_unverified_subscriber.token, old_token)
        send_verification_email.assert_called_once_with(
            new_unverified_subscriber.get_verification_url(),
            new_unverified_subscriber.email_address
        )

    @mock.patch('newsfeed.models.send_subscription_verification_email')
    def test_send_verification_email_dont_send_email(
        self, send_verification_email
    ):
        new_unverified_subscriber = baker.make(
            Subscriber, subscribed=False, verified=False
        )
        new_unverified_subscriber.verification_sent_date = (
            timezone.now() - timezone.timedelta(minutes=2)
        )
        new_unverified_subscriber.save()

        old_token = new_unverified_subscriber.token
        new_unverified_subscriber.send_verification_email(False)

        self.assertEqual(new_unverified_subscriber.token, old_token)
        send_verification_email.assert_not_called()

    def test_get_absolute_url(self):
        expected_url = (
            f'/newsfeed/subscribe/confirm/{self.unverified_subscriber.token}/'
        )
        self.assertEqual(
            self.unverified_subscriber.get_verification_url(),
            expected_url
        )


class NewsletterModelTest(TestCase):

    def test_str(self):
        newsletter = baker.make(Newsletter)
        self.assertEqual(newsletter.subject, str(newsletter))


class PostCategoryModelTest(TestCase):

    def test_str(self):
        category = baker.make(PostCategory)
        self.assertEqual(category.name, str(category))
