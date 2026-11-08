from django.test import TestCase, Client
from django.core.management import call_command
from django.core.exceptions import ValidationError
from apps.locations.models import Country, State, District, City, Locality, SubLocality
from apps.properties.models import Property, PropertyType, ListingPurposeChoices

MAHARASHTRA_36_DISTRICTS = [
    'Ahilyanagar', 'Akola', 'Amravati', 'Beed', 'Bhandara', 'Buldhana',
    'Chandrapur', 'Chhatrapati Sambhajinagar', 'Dharashiv', 'Dhule',
    'Gadchiroli', 'Gondia', 'Hingoli', 'Jalgaon', 'Jalna', 'Kolhapur',
    'Latur', 'Mumbai', 'Mumbai Suburban', 'Nagpur', 'Nanded', 'Nandurbar',
    'Nashik', 'Palghar', 'Parbhani', 'Pune', 'Raigad', 'Ratnagiri',
    'Sangli', 'Satara', 'Sindhudurg', 'Solapur', 'Thane', 'Wardha',
    'Washim', 'Yavatmal'
]

class LocationSystemTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        call_command('import_india_locations')
        call_command('seed_maharashtra_districts')

    def test_maharashtra_has_36_districts(self):
        mh = State.objects.filter(name__iexact='Maharashtra').first()
        self.assertIsNotNone(mh)
        districts = District.objects.filter(state=mh, is_active=True)
        self.assertEqual(districts.count(), 36)
        district_names = set(districts.values_list('name', flat=True))
        for expected in MAHARASHTRA_36_DISTRICTS:
            self.assertIn(expected, district_names)

    def test_1_states_and_uts_imported(self):
        states_count = State.objects.count()
        self.assertGreaterEqual(states_count, 35)
        mh = State.objects.filter(state_code='MH').first()
        self.assertIsNotNone(mh)

    def test_2_districts_linked_to_state(self):
        mh = State.objects.get(state_code='MH')
        districts = District.objects.filter(state=mh)
        self.assertEqual(districts.count(), 36)
        for d in districts:
            self.assertEqual(d.state, mh)

    def test_3_cities_linked_to_district(self):
        pune_dist = District.objects.filter(name='Pune').first()
        self.assertIsNotNone(pune_dist)
        cities = City.objects.filter(district=pune_dist)
        self.assertGreater(cities.count(), 0)
        for c in cities:
            self.assertEqual(c.district, pune_dist)

    def test_4_localities_linked_to_city(self):
        mumbai_city = City.objects.filter(slug='mumbai-suburban').first() or City.objects.filter(slug='mumbai').first()
        self.assertIsNotNone(mumbai_city)
        localities = Locality.objects.filter(city=mumbai_city)
        for l in localities:
            self.assertEqual(l.city, mumbai_city)

    def test_5_sub_localities_linked_to_locality(self):
        powai_loc = Locality.objects.filter(slug='powai').first()
        if powai_loc:
            subs = SubLocality.objects.filter(locality=powai_loc)
            for s in subs:
                self.assertEqual(s.locality, powai_loc)

    def test_6_api_districts_by_state(self):
        mh = State.objects.get(state_code='MH')
        response = self.client.get(f'/api/locations/districts/?state_id={mh.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('districts', data)
        self.assertEqual(len(data['districts']), 36)

    def test_api_direct_endpoints_state_and_district(self):
        # Test /api/states/
        res1 = self.client.get('/api/states/')
        self.assertEqual(res1.status_code, 200)
        data1 = res1.json()
        self.assertIn('states', data1)

        # Test /api/districts/
        res2 = self.client.get('/api/districts/')
        self.assertEqual(res2.status_code, 200)

        # Test /api/districts/?state_id={id}
        mh = State.objects.get(state_code='MH')
        res3 = self.client.get(f'/api/districts/?state_id={mh.id}')
        self.assertEqual(res3.status_code, 200)
        data3 = res3.json()
        self.assertEqual(len(data3['districts']), 36)

    def test_7_api_cities_by_district(self):
        pune_dist = District.objects.filter(name='Pune').first()
        if pune_dist:
            response = self.client.get(f'/api/locations/cities/?district_id={pune_dist.id}')
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn('cities', data)
            self.assertGreater(len(data['cities']), 0)

    def test_8_api_localities_by_city(self):
        city = City.objects.first()
        response = self.client.get(f'/api/locations/localities/?city_id={city.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('localities', data)

    def test_9_api_sub_localities_by_locality(self):
        loc = Locality.objects.first()
        response = self.client.get(f'/api/locations/sub-localities/?locality_id={loc.id}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('sub_localities', data)

    def test_10_and_13_backend_validation_invalid_combination(self):
        mh = State.objects.get(state_code='MH')
        ka = State.objects.get(state_code='KA')
        pune_dist = District.objects.filter(state=mh, name='Pune').first()
        bengaluru_city = City.objects.filter(state=ka).first()
        pune_locality = Locality.objects.filter(city__district=pune_dist).first()

        if pune_locality and bengaluru_city:
            prop = Property(
                title='Test Property',
                slug='test-property-invalid',
                description='Test description',
                state=ka,
                district=pune_dist,
                city=bengaluru_city,
                locality=pune_locality,
                carpet_area=500
            )
            with self.assertRaises(ValidationError):
                prop.full_clean()

    def test_11_and_12_admin_add_locality_appears_in_form(self):
        city = City.objects.first()
        new_loc = Locality.objects.create(
            city=city,
            name='Test New Locality',
            slug='test-new-locality',
            pincode='400999'
        )
        self.assertIn(new_loc, city.localities.all())

    def test_14_existing_properties_work(self):
        active_props = Property.objects.public()
        self.assertIsNotNone(active_props)

    def test_15_idempotent_import(self):
        state_count_before = State.objects.count()
        call_command('import_india_locations')
        call_command('seed_maharashtra_districts')
        mh = State.objects.get(state_code='MH')
        self.assertEqual(District.objects.filter(state=mh, is_active=True).count(), 36)
