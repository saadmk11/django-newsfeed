"""Forms for subscribing to and unsubscribing from the newsletter."""

from django import forms


class SubscriberEmailForm(forms.Form):
    """Subscriber Email Form."""

    email_address = forms.EmailField()
