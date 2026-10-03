"""Tests for issues, posts, newsletters, and subscribers."""

from unittest import mock

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker
from newsfeed.models import Issue, Newsletter, Post, PostCategory, Subscriber


class PostModelTest(TestCase):
    """Post Model Test."""

    def setUp(self) -> None:
        """Create the objects used by this test."""
        self.invisible_posts = baker.make(Post, is_visible=False, _quantity=2)
        self.visible_posts = baker.make(Post, is_visible=True, _quantity=2)

    def test_str(self) -> None:
        """Test that str."""
        post = Post.objects.visible().first()
        assert post.title == str(post)

    def test_visible_queryset(self) -> None:
        """Test that visible queryset."""
        posts = Post.objects.visible()

        visible_posts = 2
        assert posts.count() == visible_posts

    def test_all_queryset(self) -> None:
        """Test that all queryset."""
        posts = Post.objects.all()

        all_posts = 4
        assert posts.count() == all_posts


class IssueModelTest(TestCase):
    """Issue Model Test."""

    def setUp(self) -> None:
        """Create the objects used by this test."""
        self.released_issue = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.unreleased_issue = baker.make(
            Issue,
            is_draft=True,
        )

    def test_str(self) -> None:
        """Test that str."""
        issue = Issue.objects.released().first()
        assert issue.title == str(issue)

    def test_all_queryset(self) -> None:
        """Test that all queryset."""
        issues = Issue.objects.all()

        all_issues = 2
        assert issues.count() == all_issues

    def test_released_queryset(self) -> None:
        """Test that released queryset."""
        issues = Issue.objects.released()

        assert issues.count() == 1

    def test_released_with_future_released_date_queryset(self) -> None:
        """Test that released with future released date queryset."""
        future_issue = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() + timezone.timedelta(days=1),
        )
        future_issue_exists = (
            Issue.objects.released()
            .filter(
                id=future_issue.id,
            )
            .exists()
        )

        assert not future_issue_exists

    def test_is_published(self) -> None:
        """Test that is published."""
        assert self.released_issue.is_published
        assert not self.unreleased_issue.is_published

    def test_get_absolute_url(self) -> None:
        """Test that get absolute url."""
        expected_url = f"/newsfeed/issues/{self.released_issue.issue_number}/"
        assert self.released_issue.get_absolute_url() == expected_url


class SubscriberModelTest(TestCase):
    """Subscriber Model Test."""

    def setUp(self) -> None:
        """Create the objects used by this test."""
        self.verified_subscriber = baker.make(
            Subscriber,
            subscribed=True,
            verified=True,
        )
        self.unverified_subscriber = baker.make(
            Subscriber,
            subscribed=False,
            verified=False,
        )

    def test_str(self) -> None:
        """Test that str."""
        subscriber = Subscriber.objects.subscribed().first()
        assert subscriber.email_address == str(subscriber)

    def test_all_queryset(self) -> None:
        """Test that all queryset."""
        subscribers = Subscriber.objects.all()

        all_subscribers = 2
        assert subscribers.count() == all_subscribers

    def test_subscribed_queryset(self) -> None:
        """Test that subscribed queryset."""
        subscribers = Subscriber.objects.subscribed()

        assert subscribers.count() == 1

    def test_token_expired(self) -> None:
        """Test that token expired."""
        self.unverified_subscriber.verification_sent_date = (
            timezone.now() - timezone.timedelta(days=3)
        )
        self.unverified_subscriber.save()

        assert self.unverified_subscriber.token_expired()

    def test_token_not_expired(self) -> None:
        """Test that token not expired."""
        self.unverified_subscriber.verification_sent_date = timezone.now()
        self.unverified_subscriber.save()

        assert not self.unverified_subscriber.token_expired()

    def test_token_expired_with_no_verification_sent_date(self) -> None:
        """Test that token expired with no verification sent date."""
        self.unverified_subscriber.verification_sent_date = None
        self.unverified_subscriber.save()

        assert self.unverified_subscriber.token_expired()

    def test_reset_token(self) -> None:
        """Test that reset token."""
        old_token = self.unverified_subscriber.token
        self.unverified_subscriber.reset_token()

        assert old_token != self.unverified_subscriber.token

    @mock.patch("newsfeed.models.uuid")
    def test_reset_token_with_existing_token(
        self,
        uuid: mock.MagicMock,
    ) -> None:
        """Test that reset token with existing token."""
        old_token = self.unverified_subscriber.token
        new_token = "new_token"
        uuid.uuid4.side_effect = [old_token, new_token]

        self.unverified_subscriber.reset_token()

        assert old_token != self.unverified_subscriber.token
        assert new_token == self.unverified_subscriber.token

    def test_subscribe(self) -> None:
        """Test that subscribe."""
        self.unverified_subscriber.verification_sent_date = timezone.now()
        self.unverified_subscriber.save()

        assert not self.unverified_subscriber.verified
        assert not self.unverified_subscriber.subscribed

        subscribed = self.unverified_subscriber.subscribe()

        assert subscribed
        assert self.unverified_subscriber.verified
        assert self.unverified_subscriber.subscribed

    def test_subscribe_with_expired_token(self) -> None:
        """Test that subscribe with expired token."""
        self.unverified_subscriber.verification_sent_date = (
            timezone.now() - timezone.timedelta(days=3)
        )
        self.unverified_subscriber.save()

        assert self.unverified_subscriber.token_expired()
        assert not self.unverified_subscriber.verified
        assert not self.unverified_subscriber.subscribed

        subscribed = self.unverified_subscriber.subscribe()

        assert not subscribed
        assert not self.unverified_subscriber.verified
        assert not self.unverified_subscriber.subscribed

    def test_unsubscribe_with_unsubscribed_email(self) -> None:
        """Test that unsubscribe with unsubscribed email."""
        assert not self.unverified_subscriber.verified
        assert not self.unverified_subscriber.subscribed

        unsubscribed = self.unverified_subscriber.unsubscribe()

        assert not unsubscribed
        assert not self.unverified_subscriber.verified
        assert not self.unverified_subscriber.subscribed

    def test_unsubscribe(self) -> None:
        """Test that unsubscribe."""
        assert self.verified_subscriber.verified
        assert self.verified_subscriber.subscribed

        unsubscribed = self.verified_subscriber.unsubscribe()

        assert unsubscribed
        assert not self.verified_subscriber.verified
        assert not self.verified_subscriber.subscribed

    @mock.patch("newsfeed.models.send_subscription_verification_email")
    def test_send_verification_email_with_existing_email(
        self,
        send_verification_email: mock.MagicMock,
    ) -> None:
        """Test that send verification email with existing email."""
        old_token = self.unverified_subscriber.token

        self.unverified_subscriber.send_verification_email(created=False)

        assert self.unverified_subscriber.token != old_token
        send_verification_email.assert_called_once_with(
            self.unverified_subscriber.get_verification_url(),
            self.unverified_subscriber.email_address,
        )

    @mock.patch("newsfeed.models.send_subscription_verification_email")
    def test_send_verification_email_with_new_email(
        self,
        send_verification_email: mock.MagicMock,
    ) -> None:
        """Test that send verification email with new email."""
        new_unverified_subscriber = baker.make(
            Subscriber,
            subscribed=False,
            verified=False,
        )
        old_token = new_unverified_subscriber.token

        new_unverified_subscriber.send_verification_email(created=True)

        assert new_unverified_subscriber.token == old_token
        send_verification_email.assert_called_once_with(
            new_unverified_subscriber.get_verification_url(),
            new_unverified_subscriber.email_address,
        )

    @mock.patch("newsfeed.models.send_subscription_verification_email")
    def test_send_verification_email_dont_send_email(
        self,
        send_verification_email: mock.MagicMock,
    ) -> None:
        """Test that send verification email dont send email."""
        new_unverified_subscriber = baker.make(
            Subscriber,
            subscribed=False,
            verified=False,
        )
        new_unverified_subscriber.verification_sent_date = (
            timezone.now() - timezone.timedelta(minutes=2)
        )
        new_unverified_subscriber.save()

        old_token = new_unverified_subscriber.token
        new_unverified_subscriber.send_verification_email(created=False)

        assert new_unverified_subscriber.token == old_token
        send_verification_email.assert_not_called()

    def test_get_absolute_url(self) -> None:
        """Test that get absolute url."""
        expected_url = (
            f"/newsfeed/subscribe/confirm/{self.unverified_subscriber.token}/"
        )
        assert self.unverified_subscriber.get_verification_url() == expected_url


class NewsletterModelTest(TestCase):
    """Newsletter Model Test."""

    def test_str(self) -> None:
        """Test that str."""
        newsletter = baker.make(Newsletter)
        assert newsletter.subject == str(newsletter)


class PostCategoryModelTest(TestCase):
    """Post Category Model Test."""

    def test_str(self) -> None:
        """Test that str."""
        category = baker.make(PostCategory)
        assert category.name == str(category)
