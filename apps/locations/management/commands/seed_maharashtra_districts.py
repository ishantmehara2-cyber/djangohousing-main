from django.core.management.base import BaseCommand
from apps.locations.models import State, District, City

MAHARASHTRA_DISTRICTS = [
    'Ahilyanagar',
    'Akola',
    'Amravati',
    'Beed',
    'Bhandara',
    'Buldhana',
    'Chandrapur',
    'Chhatrapati Sambhajinagar',
    'Dharashiv',
    'Dhule',
    'Gadchiroli',
    'Gondia',
    'Hingoli',
    'Jalgaon',
    'Jalna',
    'Kolhapur',
    'Latur',
    'Mumbai',
    'Mumbai Suburban',
    'Nagpur',
    'Nanded',
    'Nandurbar',
    'Nashik',
    'Palghar',
    'Parbhani',
    'Pune',
    'Raigad',
    'Ratnagiri',
    'Sangli',
    'Satara',
    'Sindhudurg',
    'Solapur',
    'Thane',
    'Wardha',
    'Washim',
    'Yavatmal'
]

class Command(BaseCommand):
    help = 'Idempotently seeds all 36 Districts of Maharashtra'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding 36 Districts of Maharashtra...')

        mh = State.objects.filter(name__iexact='Maharashtra').first()
        if not mh:
            mh = State.objects.create(name='Maharashtra', code='MH', state_code='MH')
        elif mh.name != 'Maharashtra':
            mh.name = 'Maharashtra'
            mh.save()

        # Safely handle legacy district names without unique constraint conflicts
        aur = District.objects.filter(state=mh, name='Aurangabad').first()
        cs_dist = District.objects.filter(state=mh, name='Chhatrapati Sambhajinagar').first()
        if aur and cs_dist:
            City.objects.filter(district=aur).update(district=cs_dist)
            aur.delete()
        elif aur:
            aur.name = 'Chhatrapati Sambhajinagar'
            aur.save()

        mum_city = District.objects.filter(state=mh, name='Mumbai City').first()
        mum_dist = District.objects.filter(state=mh, name='Mumbai').first()
        if mum_city and mum_dist:
            City.objects.filter(district=mum_city).update(district=mum_dist)
            mum_city.delete()
        elif mum_city:
            mum_city.name = 'Mumbai'
            mum_city.save()

        created_count = 0
        for name in MAHARASHTRA_DISTRICTS:
            _, created = District.objects.get_or_create(state=mh, name=name, defaults={'is_active': True})
            if created:
                created_count += 1

        total = District.objects.filter(state=mh, is_active=True).count()
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully ensured 36 districts for Maharashtra. Total active: {total} (New created: {created_count})'))
