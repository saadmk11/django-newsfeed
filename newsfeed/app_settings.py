"""Settings read from the host Django project, with defaults."""

from django.conf import settings
from django.urls import reverse_lazy

NEWSFEED_EMAIL_BATCH_WAIT = getattr(
    settings,
    "NEWSFEED_EMAIL_BATCH_WAIT",
    0,
)
NEWSFEED_EMAIL_BATCH_SIZE = getattr(
    settings,
    "NEWSFEED_EMAIL_BATCH_SIZE",
    0,
)
NEWSFEED_EMAIL_CONFIRMATION_EXPIRE_DAYS = getattr(
    settings,
    "NEWSFEED_EMAIL_CONFIRMATION_EXPIRE_DAYS",
    3,
)
NEWSFEED_SITE_BASE_URL = getattr(
    settings,
    "NEWSFEED_SITE_BASE_URL",
    "http://127.0.0.1:8000",
)
NEWSFEED_SUBSCRIPTION_REDIRECT_URL = getattr(
    settings,
    "NEWSFEED_SUBSCRIPTION_REDIRECT_URL",
    reverse_lazy("newsfeed:issue_list"),
)
NEWSFEED_UNSUBSCRIPTION_REDIRECT_URL = getattr(
    settings,
    "NEWSFEED_UNSUBSCRIPTION_REDIRECT_URL",
    reverse_lazy("newsfeed:issue_list"),
)


def get_from_email() -> str:
    """Return the From address for newsletter and verification mail.

    Projects that still use the ``EMAIL_*`` settings send from
    ``EMAIL_HOST_USER``. Projects that set ``MAILERS`` send from
    ``DEFAULT_FROM_EMAIL``.

    Returns:
        The address used in the From header.

    """
    if not getattr(settings, "MAILERS", None):
        from_email = getattr(settings, "EMAIL_HOST_USER", "") or ""
        if from_email:
            return from_email
    return getattr(settings, "DEFAULT_FROM_EMAIL", "")
