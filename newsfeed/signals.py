from django.dispatch import Signal

# Sent after email verification sent, with Subscriber instance
email_verification_sent = Signal()

# Sent after subscription confirmed, with Subscriber instance
subscribed = Signal()

# Sent after unsubscribe successful, with Subscriber instance
unsubscribed = Signal()
