"""Email backend helpers that work on Django 5.2 through 6.1."""

from django.core import mail
from django.core.mail import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend


def open_mail_connection() -> BaseEmailBackend:
    """Return the default email backend for the installed Django version.

    Django 6.1 replaces ``get_connection()`` with ``mailers``. The mailers
    handler still falls back to ``EMAIL_BACKEND`` when ``MAILERS`` is unset.

    Returns:
        The default email backend instance.

    """
    mailers = getattr(mail, "mailers", None)
    if mailers is not None:
        return mailers["default"]
    return mail.get_connection()


def send_message(message: EmailMessage) -> int:
    """Send one message through the default email backend.

    Args:
        message: The message to send.

    Returns:
        The number of messages accepted by the backend.

    """
    if getattr(mail, "mailers", None) is not None:
        return message.send(using="default")
    return message.send()
