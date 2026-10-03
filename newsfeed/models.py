"""Newsletter issues, posts, and subscribers."""

import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone

from . import signals
from .app_settings import NEWSFEED_EMAIL_CONFIRMATION_EXPIRE_DAYS
from .constants import ISSUE_TYPE_CHOICES, WEEKLY_ISSUE
from .querysets import IssueQuerySet, PostQuerySet, SubscriberQuerySet
from .utils.send_verification import send_subscription_verification_email


class Issue(models.Model):
    """Issue."""

    title = models.CharField(max_length=128)
    issue_number = models.PositiveIntegerField(
        unique=True,
        help_text="Used as a slug for each issue",
    )
    publish_date = models.DateTimeField()
    issue_type = models.PositiveSmallIntegerField(
        choices=ISSUE_TYPE_CHOICES,
        default=WEEKLY_ISSUE,
    )
    short_description = models.TextField(blank=True, null=True)
    is_draft = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = IssueQuerySet.as_manager()

    class Meta:
        """Model metadata."""

        ordering = ("-issue_number", "-publish_date")

    def __str__(self) -> str:
        """Return the issue title.

        Returns:
            The issue title.

        """
        return self.title

    def get_absolute_url(self) -> str:
        """Return the public path for this issue.

        Returns:
            The issue detail URL.

        """
        return reverse(
            "newsfeed:issue_detail",
            kwargs={"issue_number": self.issue_number},
        )

    @property
    def is_published(self) -> bool:
        """Whether the issue is public.

        Returns:
            True when the issue is not a draft and its date has passed.

        """
        return not self.is_draft and self.publish_date <= timezone.now()


class PostCategory(models.Model):
    """Post Category."""

    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        """Model metadata."""

        verbose_name_plural = "Post categories"
        ordering = ("order",)

    def __str__(self) -> str:
        """Return the category name.

        Returns:
            The category name.

        """
        return self.name


class Post(models.Model):
    """Post."""

    issue = models.ForeignKey(
        Issue,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
    )
    category = models.ForeignKey(
        PostCategory,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
    )
    title = models.CharField(max_length=255)
    source_url = models.URLField()
    is_visible = models.BooleanField(default=True)
    short_description = models.TextField()
    order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        """Model metadata."""

        ordering = ("order", "-created_at")

    def __str__(self) -> str:
        """Return the post title.

        Returns:
            The post title.

        """
        return self.title


class Newsletter(models.Model):
    """Newsletter."""

    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name="newsletters",
    )
    subject = models.CharField(max_length=128)
    schedule = models.DateTimeField(blank=True, null=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Return the newsletter subject.

        Returns:
            The newsletter subject.

        """
        return self.subject


class Subscriber(models.Model):
    """Subscriber."""

    email_address = models.EmailField(unique=True)
    token = models.CharField(max_length=128, unique=True, default=uuid.uuid4)
    verified = models.BooleanField(default=False)
    subscribed = models.BooleanField(default=False)
    verification_sent_date = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = SubscriberQuerySet.as_manager()

    def __str__(self) -> str:
        """Return the subscriber email address.

        Returns:
            The subscriber email address.

        """
        return self.email_address

    def token_expired(self) -> bool:
        """Return whether the confirmation token is past its deadline.

        Returns:
            True when no message was sent or the confirmation window ended.

        """
        if not self.verification_sent_date:
            return True

        expiration_date = self.verification_sent_date + timezone.timedelta(
            days=NEWSFEED_EMAIL_CONFIRMATION_EXPIRE_DAYS,
        )
        return expiration_date <= timezone.now()

    def reset_token(self) -> None:
        """Replace the confirmation token with a new unique value."""
        """Handle reset token."""
        unique_token = str(uuid.uuid4())

        while self.__class__.objects.filter(token=unique_token).exists():
            unique_token = str(uuid.uuid4())

        self.token = unique_token
        self.save()

    def subscribe(self) -> bool | None:
        """Confirm the subscription when the token is still valid.

        Returns:
            True when the subscriber is confirmed, otherwise None.

        """
        """Handle subscribe."""
        if not self.token_expired():
            self.verified = True
            self.subscribed = True
            self.save()

            signals.subscribed.send(
                sender=self.__class__,
                instance=self,
            )

            return True
        return None

    def unsubscribe(self) -> bool | None:
        """Stop delivery for a current subscriber.

        Returns:
            True when the subscriber was unsubscribed, otherwise None.

        """
        """Handle unsubscribe."""
        if self.subscribed:
            self.subscribed = False
            self.verified = False
            self.save()

            signals.unsubscribed.send(
                sender=Subscriber,
                instance=self,
            )

            return True
        return None

    def send_verification_email(self, *, created: bool) -> None:
        """Send a confirmation message unless one was sent recently."""
        """Handle send verification email."""
        minutes_before = timezone.now() - timezone.timedelta(minutes=5)
        sent_date = self.verification_sent_date

        # Only send email again if the last sent date is five minutes earlier
        if sent_date and sent_date >= minutes_before:
            return

        if not created:
            self.reset_token()

        self.verification_sent_date = timezone.now()
        self.save()

        send_subscription_verification_email(
            self.get_verification_url(),
            self.email_address,
        )
        signals.email_verification_sent.send(
            sender=self.__class__,
            instance=self,
        )

    def get_verification_url(self) -> str:
        """Return the relative confirmation URL.

        Returns:
            The confirmation path for this subscriber's token.

        """
        """Handle get verification url."""
        return reverse(
            "newsfeed:newsletter_subscription_confirm",
            kwargs={"token": self.token},
        )
