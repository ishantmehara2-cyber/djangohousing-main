from django.core.management.base import BaseCommand
from apps.billing.models import Package
from apps.accounts.models import RoleChoices

class Command(BaseCommand):
    help = 'Seeds initial subscription plans and packages.'

    def handle(self, *args, **options):
        self.stdout.write('💳 Seeding monetization subscription packages...')

        packages = [
            {
                'name': 'FREE',
                'target_role': RoleChoices.OWNER,
                'description': 'Basic seller plan with standard listing visibility.',
                'price': 0.00,
                'validity_days': 30,
                'max_listings': 3,
                'featured_listings_count': 0,
            },
            {
                'name': 'BASIC',
                'target_role': RoleChoices.OWNER,
                'description': 'Expanded listing limit for individual property owners.',
                'price': 999.00,
                'validity_days': 30,
                'max_listings': 5,
                'featured_listings_count': 1,
            },
            {
                'name': 'PRO',
                'target_role': RoleChoices.OWNER,
                'description': 'Popular seller plan with featured promotions and lead management.',
                'price': 2999.00,
                'validity_days': 30,
                'max_listings': 15,
                'featured_listings_count': 3,
            },
            {
                'name': 'BUSINESS',
                'target_role': RoleChoices.AGENT,
                'description': 'Full agent agency suite with high listing capacity and CRM tools.',
                'price': 9999.00,
                'validity_days': 90,
                'max_listings': 50,
                'featured_listings_count': 10,
            },
        ]

        for p in packages:
            Package.objects.get_or_create(
                name=p['name'],
                defaults=p
            )

        self.stdout.write(self.style.SUCCESS('✅ Monetization packages seeded successfully!'))
