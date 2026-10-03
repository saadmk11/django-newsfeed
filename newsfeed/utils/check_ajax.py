"""Detect Ajax requests without Django's removed request.is_ajax helper."""

from django.http import HttpRequest


def is_ajax(request: HttpRequest) -> bool:
    """Return whether the request asks for an Ajax response.

    Args:
        request: The current HTTP request.

    Returns:
        True when the client sent an Ajax header or accepts JSON.

    """
    return any(
        [
            request.META.get("HTTP_X_REQUESTED_WITH") == "XMLHttpRequest",
            request.META.get("HTTP_ACCEPT") == "application/json",
        ],
    )
