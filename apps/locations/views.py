from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from apps.locations.models import Country, State, District, City, Locality, SubLocality

def api_states_list(request):
    states = list(State.objects.filter(is_active=True).order_by('name').values('id', 'name', 'state_code', 'lgd_code'))
    return JsonResponse({'states': states, 'results': states}, safe=False)

def api_districts_list(request):
    state_id = request.GET.get('state_id') or request.GET.get('state')
    qs = District.objects.filter(is_active=True).select_related('state').order_by('name')
    if state_id:
        if str(state_id).isdigit():
            qs = qs.filter(state_id=int(state_id))
        else:
            qs = qs.filter(state__name__iexact=state_id)
    data = list(qs.values('id', 'name', 'state_id', 'lgd_code'))
    return JsonResponse({'districts': data, 'results': data}, safe=False)

def api_districts_by_state_id(request, state_id):
    if str(state_id).isdigit():
        state = get_object_or_404(State, id=int(state_id))
    else:
        state = get_object_or_404(State, name__iexact=state_id)
    districts = list(
        District.objects.filter(state=state, is_active=True)
        .order_by('name')
        .values('id', 'name', 'lgd_code')
    )
    return JsonResponse({
        'state': state.name,
        'state_id': state.id,
        'districts': districts,
        'results': districts,
    })

def api_cities_list(request):
    district_id = request.GET.get('district_id')
    state_id = request.GET.get('state_id') or request.GET.get('state')
    qs = City.objects.filter(is_active=True).order_by('name')
    if district_id:
        qs = qs.filter(district_id=district_id)
    elif state_id:
        if str(state_id).isdigit():
            qs = qs.filter(state_id=int(state_id))
        else:
            qs = qs.filter(state__name__iexact=state_id)
    data = list(qs.values('id', 'name', 'district_id', 'state_id', 'city_type', 'slug', 'is_popular'))
    return JsonResponse({'cities': data, 'results': data}, safe=False)

def api_localities_list(request):
    city_id = request.GET.get('city_id')
    district_id = request.GET.get('district_id')
    state_id = request.GET.get('state_id') or request.GET.get('state')
    qs = Locality.objects.filter(is_active=True).order_by('name')
    if city_id:
        qs = qs.filter(city_id=city_id)
    elif district_id:
        qs = qs.filter(city__district_id=district_id)
    elif state_id:
        if str(state_id).isdigit():
            qs = qs.filter(city__state_id=int(state_id))
        else:
            qs = qs.filter(city__state__name__iexact=state_id)
    data = list(qs.values('id', 'name', 'city_id', 'pincode', 'slug'))
    return JsonResponse({'localities': data, 'results': data}, safe=False)

def api_sub_localities_list(request):
    locality_id = request.GET.get('locality_id')
    qs = SubLocality.objects.filter(is_active=True).order_by('name')
    if locality_id:
        qs = qs.filter(locality_id=locality_id)
    data = list(qs.values('id', 'name', 'locality_id', 'pincode', 'slug'))
    return JsonResponse({'sub_localities': data, 'results': data}, safe=False)

def api_location_search(request):
    query = request.GET.get('q', '').strip()
    results = {'states': [], 'districts': [], 'cities': [], 'localities': []}
    if query and len(query) >= 2:
        states = State.objects.filter(name__icontains=query, is_active=True)[:5]
        results['states'] = list(states.values('id', 'name', 'state_code'))

        districts = District.objects.filter(name__icontains=query, is_active=True).select_related('state')[:10]
        results['districts'] = [{'id': d.id, 'name': d.name, 'state': d.state.name, 'state_id': d.state_id} for d in districts]

        cities = City.objects.filter(name__icontains=query, is_active=True).select_related('state', 'district')[:10]
        results['cities'] = [{'id': c.id, 'name': c.name, 'state': c.state.name, 'district': c.district.name if c.district else ''} for c in cities]

        localities = Locality.objects.filter(name__icontains=query, is_active=True).select_related('city', 'city__state')[:15]
        results['localities'] = [{'id': l.id, 'name': l.name, 'city': l.city.name, 'state': l.city.state.name} for l in localities]

    return JsonResponse(results)

def api_location_hierarchy(request):
    city_id = request.GET.get('city_id')
    locality_id = request.GET.get('locality_id')
    data = {}
    if city_id:
        city = get_object_or_404(City.objects.select_related('state', 'district'), id=city_id)
        data = {
            'city': {'id': city.id, 'name': city.name},
            'district': {'id': city.district.id, 'name': city.district.name} if city.district else None,
            'state': {'id': city.state.id, 'name': city.state.name, 'code': city.state.state_code},
        }
    elif locality_id:
        locality = get_object_or_404(Locality.objects.select_related('city', 'city__state', 'city__district'), id=locality_id)
        city = locality.city
        data = {
            'locality': {'id': locality.id, 'name': locality.name},
            'city': {'id': city.id, 'name': city.name},
            'district': {'id': city.district.id, 'name': city.district.name} if city.district else None,
            'state': {'id': city.state.id, 'name': city.state.name, 'code': city.state.state_code},
        }
    return JsonResponse(data)
