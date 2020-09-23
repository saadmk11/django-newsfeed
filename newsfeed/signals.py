from django.dispatch import Signal

# Sent after email verification is sent, with Subscriber instance
email_verification_sent = Signal()

# Sent after subscription confirmed, with Subscriber instance
subscribed = Signal()

# Sent after unsubscription is successful, with Subscriber instance
unsubscribed = Signal()
