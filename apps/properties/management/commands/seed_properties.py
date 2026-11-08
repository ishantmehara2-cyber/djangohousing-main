from django.core.management.base import BaseCommand
from apps.properties.models import PropertyType, Amenity, PropertyCategoryChoices

class Command(BaseCommand):
    help = 'Seeds property types and amenities catalog for all categories and property types.'

    def handle(self, *args, **options):
        self.stdout.write('🏢 Seeding comprehensive property types and amenities...')

        types_data = [
            # Residential
            {'name': 'Apartment', 'slug': 'apartment', 'category': PropertyCategoryChoices.RESIDENTIAL},
            {'name': 'Independent House', 'slug': 'independent-house', 'category': PropertyCategoryChoices.RESIDENTIAL},
            {'name': 'Villa', 'slug': 'villa', 'category': PropertyCategoryChoices.RESIDENTIAL},
            {'name': 'Studio Apartment', 'slug': 'studio-apartment', 'category': PropertyCategoryChoices.RESIDENTIAL},
            {'name': 'Residential Plot', 'slug': 'residential-plot', 'category': PropertyCategoryChoices.RESIDENTIAL},

            # Commercial
            {'name': 'Office Space', 'slug': 'office-space', 'category': PropertyCategoryChoices.COMMERCIAL},
            {'name': 'Shop', 'slug': 'shop', 'category': PropertyCategoryChoices.COMMERCIAL},
            {'name': 'Showroom', 'slug': 'showroom', 'category': PropertyCategoryChoices.COMMERCIAL},
            {'name': 'Commercial Building', 'slug': 'commercial-building', 'category': PropertyCategoryChoices.COMMERCIAL},
            {'name': 'Commercial Plot', 'slug': 'commercial-plot', 'category': PropertyCategoryChoices.COMMERCIAL},
            {'name': 'Warehouse', 'slug': 'warehouse', 'category': PropertyCategoryChoices.COMMERCIAL},
        ]

        for t in types_data:
            PropertyType.objects.get_or_create(
                slug=t['slug'],
                defaults={'name': t['name'], 'category': t['category']}
            )

        amenities_data = [
            {'name': 'Swimming Pool', 'slug': 'swimming-pool', 'category': 'RECREATION'},
            {'name': 'Gymnasium', 'slug': 'gymnasium', 'category': 'FITNESS'},
            {'name': 'Power Backup', 'slug': 'power-backup', 'category': 'ESSENTIALS'},
            {'name': '24/7 Security', 'slug': 'security-24-7', 'category': 'SECURITY'},
            {'name': 'Car Parking', 'slug': 'car-parking', 'category': 'ESSENTIALS'},
            {'name': 'Lift / Elevator', 'slug': 'lift', 'category': 'ESSENTIALS'},
            {'name': 'Clubhouse', 'slug': 'clubhouse', 'category': 'RECREATION'},
            {'name': 'Children Play Area', 'slug': 'children-play-area', 'category': 'RECREATION'},
            {'name': 'Intercom', 'slug': 'intercom', 'category': 'SECURITY'},
            {'name': 'Fire Safety', 'slug': 'fire-safety', 'category': 'SECURITY'},
        ]

        for a in amenities_data:
            Amenity.objects.get_or_create(
                slug=a['slug'],
                defaults={'name': a['name'], 'category': a['category']}
            )

        self.stdout.write(self.style.SUCCESS('✅ Property types and amenities successfully seeded!'))
