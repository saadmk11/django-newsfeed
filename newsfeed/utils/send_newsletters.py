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


def send_email_newsletter(newsletters=None, respect_schedule=True):
    """
    sends newsletter emails to subscribers.

    Should always be called inside a background task or a cronjob

    :param newsletters: Newsletter QuerySet
    :param respect_schedule: if ``True`` newsletters with future schedule
        wont be sent
    """
    now = timezone.now()

    if newsletters is None:
        newsletters = Newsletter.objects.filter(
            is_sent=False,
            issue__is_draft=False,
            issue__publish_date__lte=now
        ).select_related('issue').prefetch_related(
            'issue__posts', 'issue__posts__category'
        )

    if respect_schedule:
        newsletters = newsletters.filter(schedule__lte=now)

    sent_newsletters = []

    for newsletter in newsletters:
        batch_size = NEWSFEED_EMAIL_BATCH_SIZE
        issue_number = newsletter.issue.issue_number
        sent_emails = 0
        connection = get_connection()

        rendered_newsletter = render_newsletter(newsletter)

        logger.info(
            'Ready to send newsletter for ISSUE # %s',
            issue_number
        )

        for email_messages in get_subscriber_emails(
            rendered_newsletter, batch_size, connection
        ):
            messages = list(email_messages)

            if messages:
                try:
                    # send mass email with one connection open
                    connection.send_messages(messages)

                    logger.info(
                        'Sent %s newsletters in one batch for ISSUE # %s',
                        len(messages), issue_number
                    )

                    sent_emails += len(messages)
                except Exception as e:
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
                        NEWSFEED_EMAIL_BATCH_WAIT,
                        issue_number
                    )
                    time.sleep(NEWSFEED_EMAIL_BATCH_WAIT)

        if sent_emails > 0:
            sent_newsletters.append(newsletter.id)

        logger.info(
            'Successfully Sent %s email(s) for ISSUE # %s ',
            sent_emails, issue_number
        )

    # Save newsletters to sent state
    Newsletter.objects.filter(
        id__in=sent_newsletters
    ).update(is_sent=True, sent_at=timezone.now())

    logger.info(
        'Newsletter sending process completed. '
        'Successfully sent newsletters with ID %s', sent_newsletters
    )


def render_newsletter(newsletter):
    """renders newsletter template and returns html and subject"""
    issue = newsletter.issue
    subject = newsletter.subject

    context = {
        'issue_title': issue.title,
        'issue_number': issue.issue_number,
        'publish_date': issue.publish_date,
        'short_description': issue.short_description,
        'post_list': issue.posts.visible(),
        'unsubscribe_url': reverse('newsfeed:newsletter_unsubscribe'),
        'site_url': NEWSFEED_SITE_BASE_URL
    }

    html = render_to_string('newsfeed/email/newsletter_email.html', context)

    rendered_newsletter = {
        'subject': subject,
        'html': html
    }

    return rendered_newsletter


def generate_email_message(to_email, rendered_newsletter, connection):
    """
    Generates email message for an email_address

    :param to_email: subscribers email address
    :param rendered_newsletter: rendered html of the newsletter with subject
    :param connection: email connection
    """
    message = EmailMessage(
        subject=rendered_newsletter.get('subject'),
        body=rendered_newsletter.get('html'),
        from_email=settings.EMAIL_HOST_USER, to=[to_email],
        connection=connection
    )
    message.content_subtype = "html"

    return message


def get_subscriber_emails(rendered_newsletter, batch_size, connection):
    """
    Yields EmailMessage list in batches

    :param rendered_newsletter: newsletter with html and subject
    :param connection: email connection
    """
    subscriber_emails = Subscriber.objects.subscribed().values_list(
        'email_address', flat=True
    )

    # if there is no batch size specified
    # by the user send all in one batch
    if not batch_size or batch_size <= 0:
        batch_size = len(subscriber_emails)

    logger.info('batch size for sending emails is set to %s', batch_size)

    for i in range(0, len(subscriber_emails), batch_size):
        emails = subscriber_emails[i:i + batch_size]

        yield map(
            lambda email: generate_email_message(
                email, rendered_newsletter, connection
            ), emails
        )
