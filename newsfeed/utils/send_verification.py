from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from newsfeed.app_settings import NEWSFEED_SITE_BASE_URL


def send_subscription_verification_email(verification_url, to_email):
    """
    Sends verification e-mail to subscribers

    :param verification_url: subscribers unique verification url
    :param to_email: subscribers email
    """
    context = {
        'site_url': NEWSFEED_SITE_BASE_URL,
        'verification_url': verification_url
    }

    # Send context so that users can use context data in the subject
    subject = render_to_string(
        'newsfeed/email/email_verification_subject.txt',
        context
    ).rstrip('\n')

    text_body = render_to_string(
        'newsfeed/email/email_verification.txt', context
    )
    html_body = render_to_string(
        'newsfeed/email/email_verification.html', context
    )

    message = EmailMultiAlternatives(
        subject, text_body, settings.EMAIL_HOST_USER, [to_email]
    )

    message.attach_alternative(html_body, 'text/html')
    message.send()
