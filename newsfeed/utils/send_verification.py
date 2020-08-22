from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_subscription_verification_email(subscriber):
    """
    Sends verification e-mail to subscribers

    :param to_email: subscribers email address
    :param rendered_newsletter: rendered html of the newsletter with subject
    :param connection: email connection
    """
    context = {
        'site_url': settings.SITE_BASE_URL,
        'verification_url': subscriber.get_verification_url()
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
        subject, text_body, settings.EMAIL_HOST_USER, [subscriber.email_address]
    )

    message.attach_alternative(html_body, 'text/html')
    message.send()
