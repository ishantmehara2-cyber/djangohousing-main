from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.billing.models import Subscription, PropertyPromotion
from apps.engagements.services.notifications import NotificationService

class Command(BaseCommand):
    help = 'Processes scheduled background tasks: subscription expiry, promotion expiry, and alerts'

    def handle(self, *args, **options):
        now = timezone.now()

        # 1. Process Expired Subscriptions
        expired_subs = Subscription.objects.filter(is_active=True, end_date__lt=now)
        sub_count = expired_subs.count()
        expired_subs.update(is_active=False)
        for sub in expired_subs:
            NotificationService.create_notification(
                user=sub.user,
                title="Subscription Expired",
                message=f"Your subscription plan '{sub.package.name}' has expired. Renew to continue listing properties."
            )
        self.stdout.write(self.style.SUCCESS(f"Processed {sub_count} expired subscriptions."))

        # 2. Process Expired Promotions
        expired_promos = PropertyPromotion.objects.filter(is_active=True, end_date__lt=now)
        promo_count = expired_promos.count()
        expired_promos.update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f"Processed {promo_count} expired property promotions."))
