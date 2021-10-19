def is_ajax(request):
    """Check if the request is ajax or not"""
    return any(
        [
            request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest',
            request.META.get('HTTP_ACCEPT') == 'application/json'
        ]
    )
