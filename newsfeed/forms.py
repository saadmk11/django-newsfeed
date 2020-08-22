from django import forms


class SubscriberEmailForm(forms.Form):
    email_address = forms.EmailField()
