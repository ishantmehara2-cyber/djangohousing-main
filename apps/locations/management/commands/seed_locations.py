from django.core.management.base import BaseCommand
from apps.locations.models import State, City, Locality, SubLocality

class Command(BaseCommand):
    help = 'Seeds initial Indian location hierarchy (States, Cities, Localities, SubLocalities).'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding location hierarchy...')

        # States
        states_data = [
            {'name': 'Maharashtra', 'code': 'MH'},
            {'name': 'Karnataka', 'code': 'KA'},
            {'name': 'Delhi NCR', 'code': 'DL'},
            {'name': 'Uttar Pradesh', 'code': 'UP'},
        ]

        state_objs = {}
        for s in states_data:
            st, _ = State.objects.get_or_create(code=s['code'], defaults={'name': s['name']})
            state_objs[s['code']] = st

        # Cities
        cities_data = [
            {'name': 'Mumbai', 'slug': 'mumbai', 'state': 'MH', 'lat': 19.0760, 'lng': 72.8777, 'is_popular': True},
            {'name': 'Pune', 'slug': 'pune', 'state': 'MH', 'lat': 18.5204, 'lng': 73.8567, 'is_popular': True},
            {'name': 'Bengaluru', 'slug': 'bengaluru', 'state': 'KA', 'lat': 12.9716, 'lng': 77.5946, 'is_popular': True},
            {'name': 'Delhi', 'slug': 'delhi', 'state': 'DL', 'lat': 28.7041, 'lng': 77.1025, 'is_popular': True},
        ]

        city_objs = {}
        for c in cities_data:
            city, _ = City.objects.get_or_create(
                slug=c['slug'],
                defaults={
                    'name': c['name'],
                    'state': state_objs[c['state']],
                    'latitude': c['lat'],
                    'longitude': c['lng'],
                    'is_popular': c['is_popular'],
                }
            )
            city_objs[c['slug']] = city

        # Localities
        localities_data = [
            {'city': 'mumbai', 'name': 'Andheri', 'slug': 'andheri', 'pincode': '400053', 'lat': 19.1197, 'lng': 72.8464},
            {'city': 'mumbai', 'name': 'Andheri East', 'slug': 'andheri-east', 'pincode': '400069', 'lat': 19.1136, 'lng': 72.8697},
            {'city': 'mumbai', 'name': 'Andheri West', 'slug': 'andheri-west', 'pincode': '400058', 'lat': 19.1363, 'lng': 72.8277},
            {'city': 'mumbai', 'name': 'Bandra', 'slug': 'bandra', 'pincode': '400050', 'lat': 19.0596, 'lng': 72.8295},
            {'city': 'mumbai', 'name': 'Powai', 'slug': 'powai', 'pincode': '400076', 'lat': 19.1176, 'lng': 72.9060},
            {'city': 'mumbai', 'name': 'Juhu', 'slug': 'juhu', 'pincode': '400049', 'lat': 19.1075, 'lng': 72.8263},
            {'city': 'pune', 'name': 'Hinjewadi', 'slug': 'hinjewadi', 'pincode': '411057', 'lat': 18.5912, 'lng': 73.7389},
            {'city': 'bengaluru', 'name': 'Indiranagar', 'slug': 'indiranagar', 'pincode': '560038', 'lat': 12.9784, 'lng': 77.6408},
        ]

        locality_objs = {}
        for l in localities_data:
            loc, _ = Locality.objects.get_or_create(
                city=city_objs[l['city']],
                slug=l['slug'],
                defaults={
                    'name': l['name'],
                    'pincode': l['pincode'],
                    'latitude': l['lat'],
                    'longitude': l['lng'],
                }
            )
            locality_objs[f"{l['city']}_{l['slug']}"] = loc

        # SubLocalities
        sub_data = [
            {'loc_key': 'mumbai_powai', 'name': 'Hiranandani Gardens', 'slug': 'hiranandani-gardens', 'lat': 19.1186, 'lng': 72.9103},
            {'loc_key': 'mumbai_powai', 'name': 'Chandivali', 'slug': 'chandivali', 'lat': 19.1121, 'lng': 72.8942},
            {'loc_key': 'mumbai_andheri-west', 'name': 'Lokhandwala Complex', 'slug': 'lokhandwala-complex', 'lat': 19.1418, 'lng': 72.8242},
        ]

        for sub in sub_data:
            loc = locality_objs.get(sub['loc_key'])
            if loc:
                SubLocality.objects.get_or_create(
                    locality=loc,
                    slug=sub['slug'],
                    defaults={
                        'name': sub['name'],
                        'latitude': sub['lat'],
                        'longitude': sub['lng'],
                    }
                )

        self.stdout.write(self.style.SUCCESS('✅ Location hierarchy seeded successfully!'))
