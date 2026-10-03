"""Render and send the subscription confirmation email."""

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from newsfeed.app_settings import NEWSFEED_SITE_BASE_URL, get_from_email
from newsfeed.utils.mail import send_message


def send_subscription_verification_email(
    verification_url: str,
    to_email: str,
) -> None:
    """Send a verification email to a subscriber.

    Args:
        verification_url: The subscriber's confirmation path.
        to_email: The subscriber's email address.

    """
    context = {
        "site_url": NEWSFEED_SITE_BASE_URL,
        "verification_url": verification_url,
    }

    # Send context so that users can use context data in the subject
    subject = render_to_string(
        "newsfeed/email/email_verification_subject.txt",
        context,
    ).rstrip("\n")

    text_body = render_to_string(
        "newsfeed/email/email_verification.txt",
        context,
    )
    html_body = render_to_string(
        "newsfeed/email/email_verification.html",
        context,
    )

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=get_from_email(),
        to=[to_email],
    )

    message.attach_alternative(html_body, "text/html")
    send_message(message)
