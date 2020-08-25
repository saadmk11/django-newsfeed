import logging
import time

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from newsfeed.app_settings import (
    NEWSFEED_EMAIL_BATCH_WAIT,
    NEWSFEED_EMAIL_BATCH_SIZE,
    NEWSFEED_SITE_BASE_URL,
)
from newsfeed.models import Newsletter, Subscriber


logger = logging.getLogger(__name__)


class NewsletterEmailSender:
    """The main class that handles sending email newsletters"""

    def __init__(self, newsletters=None, respect_schedule=True):
        self.newsletters = self._get_newsletters(
            newsletters=newsletters, respect_schedule=respect_schedule
        )
        # get subscriber email addresses
        self.subscriber_emails = Subscriber.objects.subscribed().values_list(
            'email_address', flat=True
        )
        # Size of each batch to be sent
        self.batch_size = NEWSFEED_EMAIL_BATCH_SIZE
        # list of newsletters that were sent
        self.sent_newsletters = []
        # Waiting time after each batch (in seconds)
        self.per_batch_wait = NEWSFEED_EMAIL_BATCH_WAIT
        # connection to the server
        self.connection = get_connection()
        self.email_host_user = settings.EMAIL_HOST_USER

    @staticmethod
    def _get_newsletters(newsletters=None, respect_schedule=True):
        """
        gets newsletters to be sent

        :param newsletters: Newsletter QuerySet
        :param respect_schedule: if ``True`` newsletters with future schedule
            will not be sent
        """
        now = timezone.now()

        if newsletters is None:
            newsletters = Newsletter.objects.filter(
                is_sent=False, issue__is_draft=False,
                issue__publish_date__lte=now
            )

        if respect_schedule:
            newsletters = newsletters.filter(schedule__lte=now)

        return newsletters.select_related('issue')

    @staticmethod
    def _render_newsletter(newsletter):
        """renders newsletter template and returns html and subject"""
        issue = newsletter.issue
        subject = newsletter.subject
        posts = issue.posts.visible().select_related('category')

        context = {
            'issue': issue,
            'post_list': posts,
            'unsubscribe_url': reverse('newsfeed:newsletter_unsubscribe'),
            'site_url': NEWSFEED_SITE_BASE_URL
        }

        html = render_to_string(
            'newsfeed/email/newsletter_email.html', context
        )

        rendered_newsletter = {
            'subject': subject,
            'html': html
        }

        return rendered_newsletter

    def _generate_email_message(self, to_email, rendered_newsletter):
        """
        Generates email message for an email_address

        :param to_email: subscribers email address
        :param rendered_newsletter: rendered html of the newsletter with subject
        """
        message = EmailMessage(
            subject=rendered_newsletter.get('subject'),
            body=rendered_newsletter.get('html'),
            from_email=self.email_host_user, to=[to_email],
            connection=self.connection
        )
        message.content_subtype = "html"

        return message

    def _get_batch_email_messages(self, rendered_newsletter):
        """
        Yields EmailMessage list in batches

        :param rendered_newsletter: newsletter with html and subject
        """

        # if there is no subscriber then stop iteration
        if len(self.subscriber_emails) == 0:
            logger.info('No subscriber found.')
            return

        # if there is no batch size specified
        # by the user send all in one batch
        if not self.batch_size or self.batch_size <= 0:
            self.batch_size = len(self.subscriber_emails)

        logger.info(
            'Batch size for sending emails is set to %s',
            self.batch_size
        )

        for i in range(0, len(self.subscriber_emails), self.batch_size):
            emails = self.subscriber_emails[i:i + self.batch_size]

            yield map(
                lambda email: self._generate_email_message(
                    email, rendered_newsletter
                ), emails
            )

    def send_emails(self):
        """sends newsletter emails to subscribers"""
        for newsletter in self.newsletters:
            issue_number = newsletter.issue.issue_number
            # this is used to calculate how many emails were
            # sent for each newsletter
            sent_emails = 0

            rendered_newsletter = self._render_newsletter(newsletter)

            logger.info(
                'Ready to send newsletter for ISSUE # %s',
                issue_number
            )

            for email_messages in self._get_batch_email_messages(
                rendered_newsletter
            ):
                messages = list(email_messages)

                try:
                    # send mass email with one connection open
                    sent = self.connection.send_messages(messages)

                    logger.info(
                        'Sent %s newsletters in one batch for ISSUE # %s',
                        len(messages), issue_number
                    )

                    sent_emails += sent
                except Exception as e:
                    # create a new connection on error
                    self.connection = get_connection()
                    logger.error(
                        'An error occurred while sending '
                        'newsletters for ISSUE # %s '
                        'newsletter ID: %s '
                        'EXCEPTION: %s',
                        issue_number, newsletter.id, e
                    )
                finally:
                    # Wait sometime before sending next batch
                    # this is to prevent server overload
                    logger.info(
                        'Waiting %s seconds before sending '
                        'next batch of newsletter for ISSUE # %s',
                        self.per_batch_wait, issue_number
                    )
                    time.sleep(self.per_batch_wait)

            if sent_emails > 0:
                self.sent_newsletters.append(newsletter.id)

            logger.info(
                'Successfully Sent %s email(s) for ISSUE # %s ',
                sent_emails, issue_number
            )

        # Save newsletters to sent state
        Newsletter.objects.filter(
            id__in=self.sent_newsletters
        ).update(is_sent=True, sent_at=timezone.now())

        logger.info(
            'Newsletter sending process completed. '
            'Successfully sent newsletters with ID %s', self.sent_newsletters
        )


def send_email_newsletter(newsletters=None, respect_schedule=True):
    send_newsletter = NewsletterEmailSender(
        newsletters=newsletters,
        respect_schedule=respect_schedule
    )
    send_newsletter.send_emails()
