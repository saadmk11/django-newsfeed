"""Render issue newsletters and send them to subscribers in batches."""

import logging
import time
from collections.abc import Iterator

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from newsfeed.app_settings import (
    NEWSFEED_EMAIL_BATCH_SIZE,
    NEWSFEED_EMAIL_BATCH_WAIT,
    NEWSFEED_SITE_BASE_URL,
    get_from_email,
)
from newsfeed.models import Newsletter, Subscriber
from newsfeed.utils.mail import open_mail_connection

logger = logging.getLogger(__name__)


class NewsletterEmailSender:
    """The main class that handles sending email newsletters."""

    def __init__(
        self,
        newsletters: object = None,
        *,
        respect_schedule: bool = True,
    ) -> None:
        """Implement __init__."""
        self.newsletters = self.select_newsletters(
            newsletters=newsletters,
            respect_schedule=respect_schedule,
        )
        # get subscriber email addresses
        self.subscriber_emails = Subscriber.objects.subscribed().values_list(
            "email_address",
            flat=True,
        )
        # Size of each batch to be sent
        self.batch_size = NEWSFEED_EMAIL_BATCH_SIZE
        # list of newsletters that were sent
        self.sent_newsletters = []
        # Waiting time after each batch (in seconds)
        self.per_batch_wait = NEWSFEED_EMAIL_BATCH_WAIT
        # connection to the server
        self.connection = open_mail_connection()
        self.from_email = get_from_email()

    @staticmethod
    def select_newsletters(
        newsletters: object = None,
        *,
        respect_schedule: bool = True,
    ) -> object:
        """Return the newsletters that should be sent.

        Args:
            newsletters: Optional newsletter queryset. All unsent newsletters
                are used when this is omitted.
            respect_schedule: Skip newsletters whose schedule is still in the
                future.

        Returns:
            The newsletters selected for delivery.

        """
        now = timezone.now()

        if newsletters is None:
            newsletters = Newsletter.objects.filter(
                is_sent=False,
                issue__is_draft=False,
                issue__publish_date__lte=now,
            )

        if respect_schedule:
            newsletters = newsletters.filter(schedule__lte=now)

        return newsletters.select_related("issue")

    @staticmethod
    def render_newsletter(newsletter: Newsletter) -> dict[str, object]:
        """Render a newsletter subject and HTML body.

        Args:
            newsletter: The newsletter to render.

        Returns:
            The subject and rendered HTML.

        """
        issue = newsletter.issue
        subject = newsletter.subject
        posts = issue.posts.visible().select_related("category")

        context = {
            "issue": issue,
            "post_list": posts,
            "unsubscribe_url": reverse("newsfeed:newsletter_unsubscribe"),
            "site_url": NEWSFEED_SITE_BASE_URL,
        }

        html = render_to_string(
            "newsfeed/email/newsletter_email.html",
            context,
        )

        return {
            "subject": subject,
            "html": html,
        }

    def generate_email_message(
        self,
        to_email: str,
        rendered_newsletter: dict[str, object],
    ) -> EmailMessage:
        """Build one HTML email message.

        Args:
            to_email: Recipient address.
            rendered_newsletter: Subject and HTML produced for the issue.

        Returns:
            The message ready to send.

        """
        message = EmailMessage(
            subject=rendered_newsletter.get("subject"),
            body=rendered_newsletter.get("html"),
            from_email=self.from_email,
            to=[to_email],
        )
        message.content_subtype = "html"

        return message

    def iter_email_batches(
        self,
        rendered_newsletter: dict[str, object],
    ) -> Iterator[Iterator[EmailMessage]]:
        """Yield each batch of email messages.

        Args:
            rendered_newsletter: Subject and HTML produced for the issue.

        Yields:
            Generators of messages, one generator per batch.

        """
        # if there is no subscriber then stop iteration
        if len(self.subscriber_emails) == 0:
            logger.info("No subscriber found.")
            return

        # if there is no batch size specified
        # by the user send all in one batch
        if not self.batch_size or self.batch_size <= 0:
            self.batch_size = len(self.subscriber_emails)

        logger.info(
            "Batch size for sending emails is set to %s",
            self.batch_size,
        )

        for i in range(0, len(self.subscriber_emails), self.batch_size):
            emails = self.subscriber_emails[i : i + self.batch_size]

            yield (
                self.generate_email_message(
                    email,
                    rendered_newsletter,
                )
                for email in emails
            )

    def send_emails(self) -> None:
        """Send newsletter emails to subscribers."""
        for newsletter in self.newsletters:
            issue_number = newsletter.issue.issue_number
            # this is used to calculate how many emails were
            # sent for each newsletter
            sent_emails = 0

            rendered_newsletter = self.render_newsletter(newsletter)

            logger.info(
                "Ready to send newsletter for ISSUE # %s",
                issue_number,
            )

            for email_messages in self.iter_email_batches(
                rendered_newsletter,
            ):
                messages = list(email_messages)

                try:
                    # send mass email with one connection open
                    sent = self.connection.send_messages(messages)

                    logger.info(
                        "Sent %s newsletters in one batch for ISSUE # %s",
                        len(messages),
                        issue_number,
                    )

                    sent_emails += sent
                except Exception:
                    # Delivery can fail for SMTP, template, or connection
                    # errors. Log it and keep going with a fresh connection.
                    self.connection = open_mail_connection()
                    logger.exception(
                        "An error occurred while sending "
                        "newsletters for ISSUE # %s "
                        "newsletter ID: %s",
                        issue_number,
                        newsletter.id,
                    )
                finally:
                    # Wait sometime before sending next batch
                    # this is to prevent server overload
                    logger.info(
                        "Waiting %s seconds before sending "
                        "next batch of newsletter for ISSUE # %s",
                        self.per_batch_wait,
                        issue_number,
                    )
                    time.sleep(self.per_batch_wait)

            if sent_emails > 0:
                self.sent_newsletters.append(newsletter.id)

            logger.info(
                "Successfully Sent %s email(s) for ISSUE # %s ",
                sent_emails,
                issue_number,
            )

        # Save newsletters to sent state
        Newsletter.objects.filter(
            id__in=self.sent_newsletters,
        ).update(is_sent=True, sent_at=timezone.now())

        logger.info(
            "Newsletter sending process completed. "
            "Successfully sent newsletters with ID %s",
            self.sent_newsletters,
        )


def send_email_newsletter(
    newsletters: object = None,
    *,
    respect_schedule: bool = True,
) -> None:
    """Send the selected newsletters."""
    send_newsletter = NewsletterEmailSender(
        newsletters=newsletters,
        respect_schedule=respect_schedule,
    )
    send_newsletter.send_emails()
