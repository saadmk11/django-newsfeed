"""Tests for publishing, drafting, and sending newsletters from the admin."""

from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker
from newsfeed.models import Issue, Newsletter, Post


class IssueAdminTest(TestCase):
    """Issue Admin Test."""

    def setUp(self) -> None:
        """Create the objects used by this test."""
        self.admin = baker.make(
            User,
            username="admin",
            password="test_passWord",
            is_staff=True,
            is_superuser=True,
        )
        self.unreleased_issue = baker.make(
            Issue,
            is_draft=True,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_issue = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.client.force_login(self.admin)

    def test_publish_issues_action(self) -> None:
        """Test that publish issues action."""
        assert self.unreleased_issue.is_draft
        data = {
            "action": "publish_issues",
            "_selected_action": [self.unreleased_issue.id],
        }

        response = self.client.post(
            reverse("admin:newsfeed_issue_changelist"),
            data,
        )

        self.assertRedirects(
            response,
            reverse("admin:newsfeed_issue_changelist"),
        )

        self.unreleased_issue.refresh_from_db()
        assert not self.unreleased_issue.is_draft

    def test_make_draft_action(self) -> None:
        """Test that make draft action."""
        assert not self.released_issue.is_draft
        data = {
            "action": "make_draft",
            "_selected_action": [self.released_issue.id],
        }

        response = self.client.post(
            reverse("admin:newsfeed_issue_changelist"),
            data,
        )

        self.assertRedirects(
            response,
            reverse("admin:newsfeed_issue_changelist"),
        )

        self.released_issue.refresh_from_db()
        assert self.released_issue.is_draft


class NewsletterAdminTest(TestCase):
    """Newsletter Admin Test."""

    def setUp(self) -> None:
        """Create the objects used by this test."""
        self.admin = baker.make(
            User,
            username="admin",
            password="test_passWord",
            is_staff=True,
            is_superuser=True,
        )
        self.released_issue = baker.make(
            Issue,
            is_draft=False,
            publish_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.released_newsletter = baker.make(
            Newsletter,
            issue=self.released_issue,
            is_sent=False,
            schedule=timezone.now() - timezone.timedelta(days=1),
        )
        self.client.force_login(self.admin)

    @mock.patch("newsfeed.admin.send_email_newsletter")
    def test_send_newsletters_action(
        self,
        send_email_newsletter: mock.MagicMock,
    ) -> None:
        """Send the selected newsletters from the admin action."""
        data = {
            "action": "send_newsletters",
            "_selected_action": [self.released_newsletter.id],
        }
        response = self.client.post(
            reverse("admin:newsfeed_newsletter_changelist"),
            data,
        )

        self.assertRedirects(
            response,
            reverse("admin:newsfeed_newsletter_changelist"),
        )
        send_email_newsletter.assert_called_once_with(
            newsletters=mock.ANY,
            respect_schedule=False,
        )


class PostAdminTest(TestCase):
    """Post Admin Test."""

    def setUp(self) -> None:
        """Create the objects used by this test."""
        self.admin = baker.make(
            User,
            username="admin",
            password="test_passWord",
            is_staff=True,
            is_superuser=True,
        )
        self.visible_post = baker.make(
            Post,
            is_visible=True,
        )
        self.invisible_post = baker.make(
            Post,
            is_visible=False,
        )

        self.client.force_login(self.admin)

    def test_hide_post_action(self) -> None:
        """Test that hide post action."""
        assert self.visible_post.is_visible
        data = {
            "action": "hide_post",
            "_selected_action": [self.visible_post.id],
        }

        response = self.client.post(
            reverse("admin:newsfeed_post_changelist"),
            data,
        )

        self.assertRedirects(
            response,
            reverse("admin:newsfeed_post_changelist"),
        )

        self.visible_post.refresh_from_db()
        assert not self.visible_post.is_visible

    def test_make_post_visible_action(self) -> None:
        """Test that make post visible action."""
        assert not self.invisible_post.is_visible
        data = {
            "action": "make_post_visible",
            "_selected_action": [self.invisible_post.id],
        }

        response = self.client.post(
            reverse("admin:newsfeed_post_changelist"),
            data,
        )

        self.assertRedirects(
            response,
            reverse("admin:newsfeed_post_changelist"),
        )

        self.invisible_post.refresh_from_db()
        assert self.invisible_post.is_visible
