from django.db import migrations

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

def seed_maharashtra_districts(apps, schema_editor):
    State = apps.get_model('locations', 'State')
    District = apps.get_model('locations', 'District')
    City = apps.get_model('locations', 'City')

    mh = State.objects.filter(name__iexact='Maharashtra').first()
    if not mh:
        mh = State.objects.create(name='Maharashtra', code='MH', state_code='MH')
    elif mh.name != 'Maharashtra':
        mh.name = 'Maharashtra'
        mh.save()

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

    for district_name in MAHARASHTRA_DISTRICTS:
        District.objects.get_or_create(state=mh, name=district_name, defaults={'is_active': True})

def reverse_seed(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0003_state_state_code'),
    ]

    operations = [
        migrations.RunPython(seed_maharashtra_districts, reverse_code=reverse_seed),
    ]
