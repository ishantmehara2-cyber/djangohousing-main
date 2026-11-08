from django.core.mail import send_mail
from django.conf import settings
from apps.engagements.models import Notification

class NotificationService:
    """
    Centralized notification creation service supporting in-app notifications
    and optional email dispatch with development backend support.
    """
    @staticmethod
    def create_notification(user, title, message, channel='IN_APP', send_email_flag=True):
        if not user:
            return None

        notif = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            channel=channel,
            is_read=False
        )

        if send_email_flag and user.email:
            try:
                send_mail(
                    subject=title,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            except Exception:
                pass

        return notif
