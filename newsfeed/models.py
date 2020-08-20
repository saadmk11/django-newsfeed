from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from .constants import ISSUE_TYPE_CHOICES, WEEKLY_ISSUE
from .querysets import IssueQuerySet


class Issue(models.Model):
    title = models.CharField(max_length=128)
    issue_number = models.PositiveIntegerField(
        unique=True, help_text='Used as a slug for each issue'
    )
    publish_date = models.DateTimeField()
    issue_type = models.PositiveSmallIntegerField(
        choices=ISSUE_TYPE_CHOICES,
        default=WEEKLY_ISSUE
    )
    short_description = models.TextField(blank=True, null=True)
    is_draft = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = IssueQuerySet.as_manager()

    class Meta:
        ordering = ['-publish_date', '-created_at']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'newsfeed:issue_detail',
            kwargs={'issue_number': self.issue_number}
        )


class PostCategory(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Post categories'

    def __str__(self):
        return self.name


class Post(models.Model):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True
    )
    category = models.ForeignKey(
        PostCategory,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True
    )
    title = models.CharField(max_length=255)
    source_url = models.URLField()
    is_visible = models.BooleanField(default=False)
    short_description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='newsletters'
    )
    subject = models.CharField(max_length=128)
    is_sent = models.BooleanField(default=False)
    schedule = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject


class Subscriber(models.Model):
    email_address = models.EmailField(unique=True)
    token = models.CharField(max_length=128, unique=True)
    verified = models.BooleanField(default=False)
    subscribed = models.BooleanField(default=False)
    confirmation_sent_date = models.DateTimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email_address

    def confirmation_expired(self):
        expiration_date = (
            self.confirmation_sent_date +
            timezone.timedelta(
                days=settings.SUBSCRIPTION_EMAIL_CONFIRMATION_EXPIRE_DAYS
            )
        )
        return expiration_date <= timezone.now()
