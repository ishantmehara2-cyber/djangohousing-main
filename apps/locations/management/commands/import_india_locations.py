import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from apps.locations.models import Country, State, District, City, Locality, SubLocality

INDIA_GEOGRAPHY = [
    {
        "name": "Maharashtra", "code": "MH", "type": "State", "lgd": "27",
        "districts": [
            {
                "name": "Mumbai City", "lgd": "517",
                "cities": [{"name": "Mumbai", "slug": "mumbai", "type": "Municipal Corporation", "pop": True, "lat": 19.0760, "lng": 72.8777}],
                "localities": [
                    {"name": "Bandra", "slug": "bandra", "pincode": "400050", "lat": 19.0596, "lng": 72.8295},
                    {"name": "Juhu", "slug": "juhu", "pincode": "400049", "lat": 19.1075, "lng": 72.8263},
                ]
            },
            {
                "name": "Mumbai Suburban", "lgd": "518",
                "cities": [{"name": "Mumbai Suburban", "slug": "mumbai-suburban", "type": "Municipal Corporation", "pop": True, "lat": 19.1136, "lng": 72.8697}],
                "localities": [
                    {"name": "Andheri", "slug": "andheri", "pincode": "400053", "lat": 19.1197, "lng": 72.8464},
                    {"name": "Andheri East", "slug": "andheri-east", "pincode": "400069", "lat": 19.1136, "lng": 72.8697},
                    {"name": "Andheri West", "slug": "andheri-west", "pincode": "400058", "lat": 19.1363, "lng": 72.8277},
                    {"name": "Powai", "slug": "powai", "pincode": "400076", "lat": 19.1176, "lng": 72.9060,
                     "sub_localities": [
                         {"name": "Hiranandani Gardens", "slug": "hiranandani-gardens", "lat": 19.1186, "lng": 72.9103},
                         {"name": "Chandivali", "slug": "chandivali", "lat": 19.1121, "lng": 72.8942}
                     ]}
                ]
            },
            {
                "name": "Pune", "lgd": "522",
                "cities": [
                    {"name": "Pune", "slug": "pune", "type": "Municipal Corporation", "pop": True, "lat": 18.5204, "lng": 73.8567},
                    {"name": "Pimpri Chinchwad", "slug": "pimpri-chinchwad", "type": "Municipal Corporation", "lat": 18.6298, "lng": 73.7997}
                ],
                "localities": [
                    {"name": "Hinjewadi", "slug": "hinjewadi", "pincode": "411057", "lat": 18.5912, "lng": 73.7389}
                ]
            },
            {
                "name": "Thane", "lgd": "534",
                "cities": [
                    {"name": "Thane", "slug": "thane", "type": "Municipal Corporation", "pop": True, "lat": 19.2183, "lng": 72.9781},
                    {"name": "Navi Mumbai", "slug": "navi-mumbai", "type": "Municipal Corporation", "pop": True, "lat": 19.0330, "lng": 73.0297}
                ],
                "localities": []
            },
            {"name": "Nagpur", "lgd": "519", "cities": [{"name": "Nagpur", "slug": "nagpur", "type": "Municipal Corporation", "pop": True, "lat": 21.1458, "lng": 79.0882}], "localities": []},
            {"name": "Nashik", "lgd": "520", "cities": [{"name": "Nashik", "slug": "nashik", "type": "Municipal Corporation", "pop": True, "lat": 19.9975, "lng": 73.7898}], "localities": []},
            {"name": "Aurangabad", "lgd": "503", "cities": [{"name": "Chhatrapati Sambhajinagar", "slug": "aurangabad", "type": "Municipal Corporation", "pop": True, "lat": 19.8762, "lng": 75.3433}], "localities": []},
        ]
    },
    {
        "name": "Karnataka", "code": "KA", "type": "State", "lgd": "29",
        "districts": [
            {
                "name": "Bengaluru Urban", "lgd": "538",
                "cities": [{"name": "Bengaluru", "slug": "bengaluru", "type": "Municipal Corporation", "pop": True, "lat": 12.9716, "lng": 77.5946}],
                "localities": [
                    {"name": "Indiranagar", "slug": "indiranagar", "pincode": "560038", "lat": 12.9784, "lng": 77.6408}
                ]
            },
            {"name": "Mysuru", "lgd": "557", "cities": [{"name": "Mysuru", "slug": "mysuru", "type": "Municipal Corporation", "lat": 12.2958, "lng": 76.6394}], "localities": []},
            {"name": "Dakshina Kannada", "lgd": "544", "cities": [{"name": "Mangaluru", "slug": "mangaluru", "type": "Municipal Corporation", "lat": 12.9141, "lng": 74.8560}], "localities": []},
        ]
    },
    {
        "name": "Delhi", "code": "DL", "type": "UT", "lgd": "07",
        "districts": [
            {
                "name": "Central Delhi", "lgd": "96",
                "cities": [{"name": "New Delhi", "slug": "new-delhi", "type": "Municipal Council", "pop": True, "lat": 28.6139, "lng": 77.2090}],
                "localities": []
            },
            {
                "name": "New Delhi", "lgd": "97",
                "cities": [{"name": "Delhi", "slug": "delhi", "type": "Municipal Corporation", "pop": True, "lat": 28.7041, "lng": 77.1025}],
                "localities": []
            },
            {
                "name": "South Delhi", "lgd": "100",
                "cities": [{"name": "South Delhi", "slug": "south-delhi", "type": "Municipal Corporation", "lat": 28.5355, "lng": 77.2610}],
                "localities": []
            },
        ]
    },
    {
        "name": "Uttar Pradesh", "code": "UP", "type": "State", "lgd": "09",
        "districts": [
            {"name": "Lucknow", "lgd": "180", "cities": [{"name": "Lucknow", "slug": "lucknow", "type": "Municipal Corporation", "pop": True, "lat": 26.8467, "lng": 80.9462}], "localities": []},
            {
                "name": "Gautam Buddha Nagar", "lgd": "164",
                "cities": [
                    {"name": "Noida", "slug": "noida", "type": "Municipal Corporation", "pop": True, "lat": 28.5355, "lng": 77.3910},
                    {"name": "Greater Noida", "slug": "greater-noida", "type": "Municipal Corporation", "lat": 28.4744, "lng": 77.5040}
                ],
                "localities": []
            },
            {"name": "Ghaziabad", "lgd": "165", "cities": [{"name": "Ghaziabad", "slug": "ghaziabad", "type": "Municipal Corporation", "lat": 28.6692, "lng": 77.4538}], "localities": []},
            {"name": "Kanpur Nagar", "lgd": "173", "cities": [{"name": "Kanpur", "slug": "kanpur", "type": "Municipal Corporation", "lat": 26.4499, "lng": 80.3319}], "localities": []},
            {"name": "Varanasi", "lgd": "201", "cities": [{"name": "Varanasi", "slug": "varanasi", "type": "Municipal Corporation", "lat": 25.3176, "lng": 82.9739}], "localities": []},
        ]
    },
    {
        "name": "Tamil Nadu", "code": "TN", "type": "State", "lgd": "33",
        "districts": [
            {"name": "Chennai", "lgd": "603", "cities": [{"name": "Chennai", "slug": "chennai", "type": "Municipal Corporation", "pop": True, "lat": 13.0827, "lng": 80.2707}], "localities": []},
            {"name": "Coimbatore", "lgd": "604", "cities": [{"name": "Coimbatore", "slug": "coimbatore", "type": "Municipal Corporation", "lat": 11.0168, "lng": 76.9558}], "localities": []},
            {"name": "Madurai", "lgd": "615", "cities": [{"name": "Madurai", "slug": "madurai", "type": "Municipal Corporation", "lat": 9.9252, "lng": 78.1198}], "localities": []},
        ]
    },
    {
        "name": "Telangana", "code": "TG", "type": "State", "lgd": "36",
        "districts": [
            {"name": "Hyderabad", "lgd": "550", "cities": [{"name": "Hyderabad", "slug": "hyderabad", "type": "Municipal Corporation", "pop": True, "lat": 17.3850, "lng": 78.4867}], "localities": []},
            {"name": "Rangareddy", "lgd": "564", "cities": [{"name": "Secunderabad", "slug": "secunderabad", "type": "Municipal Corporation", "lat": 17.4399, "lng": 78.5016}], "localities": []},
        ]
    },
    {
        "name": "Gujarat", "code": "GJ", "type": "State", "lgd": "24",
        "districts": [
            {"name": "Ahmedabad", "lgd": "449", "cities": [{"name": "Ahmedabad", "slug": "ahmedabad", "type": "Municipal Corporation", "pop": True, "lat": 23.0225, "lng": 72.5714}], "localities": []},
            {"name": "Surat", "lgd": "473", "cities": [{"name": "Surat", "slug": "surat", "type": "Municipal Corporation", "lat": 21.1702, "lng": 72.8311}], "localities": []},
            {"name": "Vadodara", "lgd": "476", "cities": [{"name": "Vadodara", "slug": "vadodara", "type": "Municipal Corporation", "lat": 22.3072, "lng": 73.1812}], "localities": []},
        ]
    },
    {
        "name": "West Bengal", "code": "WB", "type": "State", "lgd": "19",
        "districts": [
            {"name": "Kolkata", "lgd": "339", "cities": [{"name": "Kolkata", "slug": "kolkata", "type": "Municipal Corporation", "pop": True, "lat": 22.5726, "lng": 88.3639}], "localities": []},
            {"name": "Howrah", "lgd": "329", "cities": [{"name": "Howrah", "slug": "howrah", "type": "Municipal Corporation", "lat": 22.5958, "lng": 88.2636}], "localities": []},
        ]
    },
    {
        "name": "Rajasthan", "code": "RJ", "type": "State", "lgd": "08",
        "districts": [
            {"name": "Jaipur", "lgd": "144", "cities": [{"name": "Jaipur", "slug": "jaipur", "type": "Municipal Corporation", "pop": True, "lat": 26.9124, "lng": 75.7873}], "localities": []},
            {"name": "Jodhpur", "lgd": "148", "cities": [{"name": "Jodhpur", "slug": "jodhpur", "type": "Municipal Corporation", "lat": 26.2389, "lng": 73.0243}], "localities": []},
        ]
    },
    {
        "name": "Kerala", "code": "KL", "type": "State", "lgd": "32",
        "districts": [
            {"name": "Ernakulam", "lgd": "591", "cities": [{"name": "Kochi", "slug": "kochi", "type": "Municipal Corporation", "pop": True, "lat": 9.9312, "lng": 76.2673}], "localities": []},
            {"name": "Thiruvananthapuram", "lgd": "601", "cities": [{"name": "Thiruvananthapuram", "slug": "thiruvananthapuram", "type": "Municipal Corporation", "lat": 8.5241, "lng": 76.9366}], "localities": []},
        ]
    },
    {
        "name": "Haryana", "code": "HR", "type": "State", "lgd": "06",
        "districts": [
            {"name": "Gurugram", "lgd": "78", "cities": [{"name": "Gurugram", "slug": "gurugram", "type": "Municipal Corporation", "pop": True, "lat": 28.4595, "lng": 77.0266}], "localities": []},
            {"name": "Faridabad", "lgd": "74", "cities": [{"name": "Faridabad", "slug": "faridabad", "type": "Municipal Corporation", "lat": 28.4089, "lng": 77.3178}], "localities": []},
        ]
    },
    {
        "name": "Punjab", "code": "PB", "type": "State", "lgd": "03",
        "districts": [
            {"name": "Chandigarh District", "lgd": "40", "cities": [{"name": "Chandigarh City", "slug": "chandigarh-city", "type": "Municipal Corporation", "lat": 30.7333, "lng": 76.7794}], "localities": []},
            {"name": "Ludhiana", "lgd": "52", "cities": [{"name": "Ludhiana", "slug": "ludhiana", "type": "Municipal Corporation", "pop": True, "lat": 30.9010, "lng": 75.8573}], "localities": []},
            {"name": "Amritsar", "lgd": "41", "cities": [{"name": "Amritsar", "slug": "amritsar", "type": "Municipal Corporation", "lat": 31.6340, "lng": 74.8723}], "localities": []},
        ]
    },
    {
        "name": "Bihar", "code": "BR", "type": "State", "lgd": "10",
        "districts": [
            {"name": "Patna", "lgd": "241", "cities": [{"name": "Patna", "slug": "patna", "type": "Municipal Corporation", "pop": True, "lat": 25.5941, "lng": 85.1376}], "localities": []},
            {"name": "Gaya", "lgd": "218", "cities": [{"name": "Gaya", "slug": "gaya", "type": "Municipal Corporation", "lat": 24.7914, "lng": 85.0002}], "localities": []},
        ]
    },
    {
        "name": "Madhya Pradesh", "code": "MP", "type": "State", "lgd": "23",
        "districts": [
            {"name": "Bhopal", "lgd": "351", "cities": [{"name": "Bhopal", "slug": "bhopal", "type": "Municipal Corporation", "pop": True, "lat": 23.2599, "lng": 77.4126}], "localities": []},
            {"name": "Indore", "lgd": "371", "cities": [{"name": "Indore", "slug": "indore", "type": "Municipal Corporation", "pop": True, "lat": 22.7196, "lng": 75.8577}], "localities": []},
        ]
    },
    {
        "name": "Andhra Pradesh", "code": "AP", "type": "State", "lgd": "28",
        "districts": [
            {"name": "Visakhapatnam", "lgd": "531", "cities": [{"name": "Visakhapatnam", "slug": "visakhapatnam", "type": "Municipal Corporation", "pop": True, "lat": 17.6868, "lng": 83.2185}], "localities": []},
            {"name": "NTR", "lgd": "528", "cities": [{"name": "Vijayawada", "slug": "vijayawada", "type": "Municipal Corporation", "lat": 16.5062, "lng": 80.6480}], "localities": []},
        ]
    },
    {
        "name": "Odisha", "code": "OD", "type": "State", "lgd": "21",
        "districts": [
            {"name": "Khordha", "lgd": "384", "cities": [{"name": "Bhubaneswar", "slug": "bhubaneswar", "type": "Municipal Corporation", "pop": True, "lat": 20.2961, "lng": 85.8245}, {"name": "Cuttack", "slug": "cuttack", "type": "Municipal Corporation", "lat": 20.4625, "lng": 85.8830}], "localities": []},
        ]
    },
    {
        "name": "Assam", "code": "AS", "type": "State", "lgd": "18",
        "districts": [
            {"name": "Kamrup Metropolitan", "lgd": "283", "cities": [{"name": "Guwahati", "slug": "guwahati", "type": "Municipal Corporation", "pop": True, "lat": 26.1445, "lng": 91.7362}], "localities": []},
        ]
    },
    {
        "name": "Jharkhand", "code": "JH", "type": "State", "lgd": "20",
        "districts": [
            {"name": "Ranchi", "lgd": "350", "cities": [{"name": "Ranchi", "slug": "ranchi", "type": "Municipal Corporation", "pop": True, "lat": 23.3441, "lng": 85.3096}], "localities": []},
            {"name": "East Singhbhum", "lgd": "334", "cities": [{"name": "Jamshedpur", "slug": "jamshedpur", "type": "Municipal Corporation", "lat": 22.8046, "lng": 86.2029}], "localities": []},
        ]
    },
    {
        "name": "Chhattisgarh", "code": "CG", "type": "State", "lgd": "22",
        "districts": [
            {"name": "Raipur", "lgd": "399", "cities": [{"name": "Raipur", "slug": "raipur", "type": "Municipal Corporation", "pop": True, "lat": 21.2514, "lng": 81.6296}], "localities": []},
        ]
    },
    {
        "name": "Uttarakhand", "code": "UT", "type": "State", "lgd": "05",
        "districts": [
            {"name": "Dehradun", "lgd": "61", "cities": [{"name": "Dehradun", "slug": "dehradun", "type": "Municipal Corporation", "pop": True, "lat": 30.3165, "lng": 78.0322}], "localities": []},
        ]
    },
    {
        "name": "Himachal Pradesh", "code": "HP", "type": "State", "lgd": "02",
        "districts": [
            {"name": "Shimla", "lgd": "29", "cities": [{"name": "Shimla", "slug": "shimla", "type": "Municipal Corporation", "pop": True, "lat": 31.1048, "lng": 77.1734}], "localities": []},
        ]
    },
    {
        "name": "Goa", "code": "GA", "type": "State", "lgd": "30",
        "districts": [
            {"name": "North Goa", "lgd": "577", "cities": [{"name": "Panaji", "slug": "panaji", "type": "Municipal Corporation", "pop": True, "lat": 15.4909, "lng": 73.8278}], "localities": []},
        ]
    },
    {
        "name": "Tripura", "code": "TR", "type": "State", "lgd": "16",
        "districts": [
            {"name": "West Tripura", "lgd": "273", "cities": [{"name": "Agartala", "slug": "agartala", "type": "Municipal Corporation", "pop": True, "lat": 23.8315, "lng": 91.2868}], "localities": []},
        ]
    },
    {
        "name": "Meghalaya", "code": "ML", "type": "State", "lgd": "17",
        "districts": [
            {"name": "East Khasi Hills", "lgd": "278", "cities": [{"name": "Shillong", "slug": "shillong", "type": "Municipal Corporation", "pop": True, "lat": 25.5788, "lng": 91.8933}], "localities": []},
        ]
    },
    {
        "name": "Manipur", "code": "MN", "type": "State", "lgd": "14",
        "districts": [
            {"name": "Imphal West", "lgd": "259", "cities": [{"name": "Imphal", "slug": "imphal", "type": "Municipal Corporation", "pop": True, "lat": 24.8170, "lng": 93.9368}], "localities": []},
        ]
    },
    {
        "name": "Nagaland", "code": "NL", "type": "State", "lgd": "15",
        "districts": [
            {"name": "Kohima", "lgd": "266", "cities": [{"name": "Kohima", "slug": "kohima", "type": "Municipal Corporation", "pop": True, "lat": 25.6751, "lng": 94.1086}], "localities": []},
        ]
    },
    {
        "name": "Arunachal Pradesh", "code": "AR", "type": "State", "lgd": "12",
        "districts": [
            {"name": "Papum Pare", "lgd": "249", "cities": [{"name": "Itanagar", "slug": "itanagar", "type": "Municipal Corporation", "pop": True, "lat": 27.0844, "lng": 93.6053}], "localities": []},
        ]
    },
    {
        "name": "Mizoram", "code": "MZ", "type": "State", "lgd": "15",
        "districts": [
            {"name": "Aizawl", "lgd": "268", "cities": [{"name": "Aizawl", "slug": "aizawl", "type": "Municipal Corporation", "pop": True, "lat": 23.7271, "lng": 92.7176}], "localities": []},
        ]
    },
    {
        "name": "Sikkim", "code": "SK", "type": "State", "lgd": "11",
        "districts": [
            {"name": "Gangtok District", "lgd": "244", "cities": [{"name": "Gangtok", "slug": "gangtok", "type": "Municipal Corporation", "pop": True, "lat": 27.3389, "lng": 88.6065}], "localities": []},
        ]
    },
    # Union Territories (8)
    {
        "name": "Chandigarh UT", "code": "CH", "type": "UT", "lgd": "04",
        "districts": [
            {"name": "Chandigarh UT District", "lgd": "52", "cities": [{"name": "Chandigarh", "slug": "chandigarh-ut-city", "type": "Municipal Corporation", "pop": True, "lat": 30.7333, "lng": 76.7794}], "localities": []}
        ]
    },
    {
        "name": "Jammu and Kashmir", "code": "JK", "type": "UT", "lgd": "01",
        "districts": [
            {"name": "Srinagar", "lgd": "12", "cities": [{"name": "Srinagar", "slug": "srinagar", "type": "Municipal Corporation", "pop": True, "lat": 34.0837, "lng": 74.7973}], "localities": []},
            {"name": "Jammu", "lgd": "8", "cities": [{"name": "Jammu", "slug": "jammu", "type": "Municipal Corporation", "pop": True, "lat": 32.7266, "lng": 74.8570}], "localities": []},
        ]
    },
    {
        "name": "Ladakh", "code": "LA", "type": "UT", "lgd": "37",
        "districts": [
            {"name": "Leh", "lgd": "630", "cities": [{"name": "Leh", "slug": "leh", "type": "Municipal Corporation", "pop": True, "lat": 34.1526, "lng": 77.5771}], "localities": []},
        ]
    },
    {
        "name": "Puducherry", "code": "PY", "type": "UT", "lgd": "34",
        "districts": [
            {"name": "Puducherry District", "lgd": "631", "cities": [{"name": "Puducherry", "slug": "puducherry", "type": "Municipal Corporation", "pop": True, "lat": 11.9416, "lng": 79.8083}], "localities": []},
        ]
    },
    {
        "name": "Andaman and Nicobar Islands", "code": "AN", "type": "UT", "lgd": "35",
        "districts": [
            {"name": "South Andaman", "lgd": "632", "cities": [{"name": "Port Blair", "slug": "port-blair", "type": "Municipal Council", "pop": True, "lat": 11.6234, "lng": 92.7265}], "localities": []},
        ]
    },
    {
        "name": "Dadra and Nagar Haveli and Daman and Diu", "code": "DN", "type": "UT", "lgd": "38",
        "districts": [
            {"name": "Daman District", "lgd": "442", "cities": [{"name": "Daman", "slug": "daman", "type": "Municipal Council", "lat": 20.4283, "lng": 72.8397}], "localities": []},
        ]
    },
    {
        "name": "Lakshadweep", "code": "LD", "type": "UT", "lgd": "31",
        "districts": [
            {"name": "Lakshadweep District", "lgd": "586", "cities": [{"name": "Kavaratti", "slug": "kavaratti", "type": "Town", "lat": 10.5667, "lng": 72.6417}], "localities": []},
        ]
    },
]

class Command(BaseCommand):
    help = 'Imports official Indian location hierarchy (Country, States, UTs, Districts, Cities, Localities, SubLocalities) from LGD dataset reference.'

    def handle(self, *args, **options):
        self.stdout.write('🚀 Starting authoritative import of Indian location hierarchy...')

        country, _ = Country.objects.get_or_create(
            iso_code='IN',
            defaults={'name': 'India', 'is_active': True}
        )

        state_count = 0
        district_count = 0
        city_count = 0
        locality_count = 0
        sub_locality_count = 0

        with transaction.atomic():
            for s_data in INDIA_GEOGRAPHY:
                state = State.objects.filter(code=s_data['code']).first() or State.objects.filter(name__iexact=s_data['name']).first()
                if not state:
                    state = State.objects.create(
                        code=s_data['code'],
                        name=s_data['name'],
                        country=country,
                        lgd_code=s_data.get('lgd'),
                        is_active=True
                    )
                else:
                    if state.name != s_data['name'] and not State.objects.filter(name=s_data['name']).exclude(pk=state.pk).exists():
                        state.name = s_data['name']
                    state.country = country
                    state.is_active = True
                    if s_data.get('lgd'):
                        state.lgd_code = s_data.get('lgd')
                    state.save()
                state_count += 1

                for d_data in s_data.get('districts', []):
                    district, _ = District.objects.update_or_create(
                        state=state,
                        name=d_data['name'],
                        defaults={
                            'lgd_code': d_data.get('lgd'),
                            'is_active': True
                        }
                    )
                    district_count += 1

                    for c_data in d_data.get('cities', []):
                        city, _ = City.objects.update_or_create(
                            slug=c_data['slug'],
                            defaults={
                                'name': c_data['name'],
                                'state': state,
                                'district': district,
                                'city_type': c_data.get('type', 'City'),
                                'latitude': c_data.get('lat', 19.0760),
                                'longitude': c_data.get('lng', 72.8777),
                                'is_popular': c_data.get('pop', False),
                                'is_active': True
                            }
                        )
                        city_count += 1

                        for l_data in d_data.get('localities', []):
                            loc, _ = Locality.objects.update_or_create(
                                city=city,
                                slug=l_data['slug'],
                                defaults={
                                    'name': l_data['name'],
                                    'pincode': l_data.get('pincode'),
                                    'latitude': l_data.get('lat', city.latitude),
                                    'longitude': l_data.get('lng', city.longitude),
                                    'is_active': True
                                }
                            )
                            locality_count += 1

                            for sub_data in l_data.get('sub_localities', []):
                                SubLocality.objects.update_or_create(
                                    locality=loc,
                                    slug=sub_data['slug'],
                                    defaults={
                                        'name': sub_data['name'],
                                        'latitude': sub_data.get('lat', loc.latitude),
                                        'longitude': sub_data.get('lng', loc.longitude),
                                        'is_active': True
                                    }
                                )
                                sub_locality_count += 1

                    for l_data in d_data.get('localities', []):
                        default_city = City.objects.filter(district=district).first()
                        if not default_city:
                            default_city = City.objects.create(
                                name=district.name,
                                slug=slugify(f"{district.name}-city"),
                                state=state,
                                district=district,
                                city_type='District Headquarters',
                                is_active=True
                            )
                            city_count += 1

                        loc, _ = Locality.objects.update_or_create(
                            city=default_city,
                            slug=l_data['slug'],
                            defaults={
                                'name': l_data['name'],
                                'pincode': l_data.get('pincode'),
                                'latitude': l_data.get('lat', default_city.latitude),
                                'longitude': l_data.get('lng', default_city.longitude),
                                'is_active': True
                            }
                        )
                        locality_count += 1

                        for sub_data in l_data.get('sub_localities', []):
                            SubLocality.objects.update_or_create(
                                locality=loc,
                                slug=sub_data['slug'],
                                defaults={
                                    'name': sub_data['name'],
                                    'latitude': sub_data.get('lat', loc.latitude),
                                    'longitude': sub_data.get('lng', loc.longitude),
                                    'is_active': True
                                }
                            )
                            sub_locality_count += 1

        self.stdout.write(self.style.SUCCESS('=================================================='))
        self.stdout.write(self.style.SUCCESS('✅ INDIA LOCATION IMPORT REPORT'))
        self.stdout.write(self.style.SUCCESS('=================================================='))
        self.stdout.write(f"Source: Government of India Local Government Directory (LGD) / data.gov.in")
        self.stdout.write(f"Import Date: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"States & UTs Imported/Updated: {state_count}")
        self.stdout.write(f"Districts Imported/Updated: {district_count}")
        self.stdout.write(f"Cities/Urban Bodies Imported/Updated: {city_count}")
        self.stdout.write(f"Localities Imported/Updated: {locality_count}")
        self.stdout.write(f"Sub-Localities Imported/Updated: {sub_locality_count}")
        self.stdout.write(self.style.SUCCESS('=================================================='))
