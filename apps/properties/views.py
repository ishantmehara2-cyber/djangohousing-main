from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.utils.text import slugify
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone

from apps.accounts.models import RoleChoices
from apps.accounts.permissions import role_required, can_edit_property, user_has_role, can_post_property
from apps.core.validators import MAX_UPLOAD_SIZE_BYTES, validate_file_size_5mb
from apps.properties.models import (
    Property, PropertyType, Amenity, PropertyAmenity, PropertyMedia,
    ListingPurposeChoices, ListingStateChoices, PropertyCategoryChoices,
    FurnishingChoices, PossessionStatusChoices
)
from apps.locations.models import State, District, City, Locality, SubLocality
from apps.engagements.models import Favorite, RecentlyViewed, PropertyPriceHistory
from apps.properties.filters import apply_property_filters
from apps.properties.forms import PropertySearchForm
from apps.properties.services.recommendation_service import PropertyRecommendationService
from apps.properties.services.lets_api_adapter import LetsApiAdapter
from apps.properties.utils import validate_property_image

def render_template(request, template_name, context):
    template = get_template(template_name)
    return HttpResponse(template.render(context, request))

def get_common_search_context(request):
    states = State.objects.filter(is_active=True).order_by('name')
    districts = District.objects.filter(is_active=True).order_by('name')
    cities = City.objects.filter(is_active=True)
    property_types = PropertyType.objects.all()
    amenities = Amenity.objects.all()

    bhk_raw = request.GET.get('bhk', '')
    bhk_list = [b.strip() for b in bhk_raw.split(',') if b.strip()] if bhk_raw else request.GET.getlist('bhk')

    context = {
        'request': request,
        'user': request.user,
        'states': states,
        'districts': districts,
        'cities': cities,
        'property_types': property_types,
        'amenities': amenities,
        'purposes': ListingPurposeChoices.choices,
        'furnishing_choices': FurnishingChoices.choices,
        'availability_choices': PossessionStatusChoices.choices,
        'selected_state': request.GET.get('state') or request.GET.get('state_id', ''),
        'selected_district': request.GET.get('district') or request.GET.get('district_id', ''),
        'selected_city': request.GET.get('city', ''),
        'selected_purpose': request.GET.get('purpose') or request.GET.get('listing_purpose', ''),
        'selected_property_type': request.GET.get('property_type', ''),
        'selected_furnishing': request.GET.get('furnishing', ''),
        'selected_availability': request.GET.get('availability') or request.GET.get('possession_status', ''),
        'selected_bhk_list': bhk_list,
        'selected_bhk': bhk_raw,
        'min_price': request.GET.get('min_price', ''),
        'max_price': request.GET.get('max_price', ''),
        'min_area': request.GET.get('min_area', ''),
        'max_area': request.GET.get('max_area', ''),
        'keyword': request.GET.get('keyword') or request.GET.get('q', ''),
        'selected_amenities': request.GET.getlist('amenities'),
        'current_sort': request.GET.get('sort', 'newest'),
    }
    return context

def paginate_properties_queryset(request, properties, page_title, active_tab=None, active_category=None):
    paginator = Paginator(properties, 9)
    page_number = request.GET.get('page', 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        query_params.pop('page')
    query_string = query_params.urlencode()

    favorite_property_ids = set()
    if request.user.is_authenticated:
        favorite_property_ids = set(
            Favorite.objects.filter(user=request.user).values_list('property_id', flat=True)
        )

    context = get_common_search_context(request)
    context.update({
        'page_obj': page_obj,
        'paginator': paginator,
        'query_string': query_string,
        'favorite_property_ids': favorite_property_ids,
        'page_title': page_title,
        'active_tab': active_tab,
        'active_category': active_category,
    })
    return context

def property_list_view(request):
    form = PropertySearchForm(request.GET)
    if form.is_valid():
        properties = apply_property_filters(request.GET)
    else:
        properties = Property.objects.public()

    context = paginate_properties_queryset(request, properties, page_title="Property Catalog & Advanced Search")
    return render_template(request, 'pages/search.html', context)

def buy_property_list_view(request):
    params = request.GET.copy()
    params['purpose'] = 'BUY'
    properties = apply_property_filters(params)
    context = paginate_properties_queryset(request, properties, page_title="Properties for Buy & Sale", active_tab='buy')
    return render_template(request, 'pages/search.html', context)

def rent_property_list_view(request):
    params = request.GET.copy()
    params['purpose'] = 'RENT'
    properties = apply_property_filters(params)
    context = paginate_properties_queryset(request, properties, page_title="Properties for Rent & Lease", active_tab='rent')
    return render_template(request, 'pages/search.html', context)

def commercial_property_list_view(request):
    params = request.GET.copy()
    params['purpose'] = 'COMMERCIAL'
    properties = apply_property_filters(params)
    context = paginate_properties_queryset(request, properties, page_title="Commercial Properties & Offices", active_tab='commercial', active_category='Commercial')
    return render_template(request, 'pages/search.html', context)

def residential_property_list_view(request):
    params = request.GET.copy()
    params['purpose'] = 'RESIDENTIAL'
    properties = apply_property_filters(params)
    context = paginate_properties_queryset(request, properties, page_title="Residential Properties", active_tab='residential', active_category='Residential')
    return render_template(request, 'pages/search.html', context)

def property_search_view(request):
    form = PropertySearchForm(request.GET)
    if form.is_valid():
        properties = apply_property_filters(request.GET)
    else:
        properties = Property.objects.public()

    context = paginate_properties_queryset(request, properties, page_title="Property Search & Advanced Filters")
    return render_template(request, 'pages/search.html', context)

def property_detail_view(request, slug):
    property_item = get_object_or_404(
        Property.objects.select_related('city', 'locality', 'property_type', 'owner', 'posted_by_user'),
        slug=slug
    )

    is_public = property_item.listing_state == ListingStateChoices.ACTIVE
    if not is_public:
        if not request.user.is_authenticated or not can_edit_property(request.user, property_item):
            raise Http404("Property not found or unavailable.")

    if is_public:
        property_item.views_count += 1
        property_item.save(update_fields=['views_count'])

        # Record Recently Viewed for authenticated user
        if request.user.is_authenticated:
            RecentlyViewed.objects.update_or_create(
                user=request.user,
                property=property_item,
                defaults={'viewed_at': timezone.now()}
            )

    amenities = property_item.property_amenities.select_related('amenity').all()
    media_items = property_item.media.all()
    similar_properties = PropertyRecommendationService.get_similar_properties(property_item, limit=3)

    is_favorited = False
    if request.user.is_authenticated:
        is_favorited = Favorite.objects.filter(user=request.user, property=property_item).exists()

    context = {
        'request': request,
        'user': request.user,
        'property': property_item,
        'amenities': amenities,
        'media_items': media_items,
        'similar_properties': similar_properties,
        'is_favorited': is_favorited,
        'is_preview': not is_public,
    }
    return render_template(request, 'pages/property_detail.html', context)

def property_compare_view(request):
    """Side-by-side comparison tool for up to 4 selected public properties."""
    prop_ids = request.GET.getlist('id')
    properties = Property.objects.public().filter(id__in=prop_ids).select_related('city', 'locality', 'property_type').prefetch_related('property_amenities__amenity')[:4]

    context = {
        'request': request,
        'user': request.user,
        'properties': properties,
    }
    return render_template(request, 'pages/property_compare.html', context)

@login_required
def post_property_view(request):
    can_post, msg = can_post_property(request.user)
    if not can_post:
        messages.error(request, msg)
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        listing_purpose = request.POST.get('listing_purpose', ListingPurposeChoices.BUY)
        property_type_id = request.POST.get('property_type')
        price = request.POST.get('price')
        rent = request.POST.get('rent')
        security_deposit = request.POST.get('security_deposit')
        maintenance_fee = request.POST.get('maintenance_fee')
        bhk = request.POST.get('bhk', 1)
        bathrooms = request.POST.get('bathrooms', 1)
        balconies = request.POST.get('balconies', 0)
        carpet_area = request.POST.get('carpet_area', 500)
        built_up_area = request.POST.get('built_up_area')
        furnishing = request.POST.get('furnishing', FurnishingChoices.UNFURNISHED)
        floor_number = request.POST.get('floor_number')
        total_floors = request.POST.get('total_floors')
        state_id = request.POST.get('state')
        district_id = request.POST.get('district')
        city_id = request.POST.get('city')
        locality_id = request.POST.get('locality')
        sub_locality_id = request.POST.get('sub_locality')
        address = request.POST.get('address')
        pincode = request.POST.get('pincode')
        action_type = request.POST.get('action', 'submit')
        selected_thumbnail_index = request.POST.get('selected_thumbnail_index')

        if locality_id and not city_id:
            try:
                locality_obj = Locality.objects.get(id=locality_id)
                city_id = locality_obj.city_id
            except Locality.DoesNotExist:
                pass

        if not title or not property_type_id or not locality_id or not carpet_area:
            messages.error(request, "Please fill in all required property details.")
            return redirect('properties:post-property')

        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Property.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        property_type = get_object_or_404(PropertyType, id=property_type_id)
        locality = get_object_or_404(Locality, id=locality_id)
        city = locality.city if locality else get_object_or_404(City, id=city_id)
        state = get_object_or_404(State, id=state_id) if state_id else city.state
        district = get_object_or_404(District, id=district_id) if district_id else city.district
        sub_locality = get_object_or_404(SubLocality, id=sub_locality_id) if sub_locality_id else None

        listing_state = ListingStateChoices.DRAFT if action_type == 'draft' else ListingStateChoices.PENDING_APPROVAL

        prop = Property.objects.create(
            title=title,
            slug=slug,
            description=description,
            listing_purpose=listing_purpose,
            property_category=property_type.category,
            property_type=property_type,
            owner=request.user,
            posted_by_user=request.user,
            price=float(price) if price else None,
            rent=float(rent) if rent else None,
            security_deposit=float(security_deposit) if security_deposit else None,
            maintenance_fee=float(maintenance_fee) if maintenance_fee else None,
            bhk=int(bhk) if bhk else 1,
            bathrooms=int(bathrooms) if bathrooms else 1,
            balconies=int(balconies) if balconies else 0,
            carpet_area=float(carpet_area),
            built_up_area=float(built_up_area) if built_up_area else None,
            furnishing=furnishing,
            floor_number=int(floor_number) if floor_number else None,
            total_floors=int(total_floors) if total_floors else None,
            state=state,
            district=district,
            city=city,
            locality=locality,
            sub_locality=sub_locality,
            address=address,
            pincode=pincode,
            listing_state=listing_state
        )

        amenity_ids = request.POST.getlist('amenities')
        for am_id in amenity_ids:
            try:
                amenity = Amenity.objects.get(id=am_id)
                PropertyAmenity.objects.create(property=prop, amenity=amenity)
            except Amenity.DoesNotExist:
                pass

        images = request.FILES.getlist('images')
        MAX_PROPERTY_IMAGES = 8
        if len(images) > MAX_PROPERTY_IMAGES:
            messages.warning(request, f"Maximum 8 property images allowed. Only the first {MAX_PROPERTY_IMAGES} images were saved.")
            images = images[:MAX_PROPERTY_IMAGES]

        created_media = []

        for idx, img in enumerate(images):
            if img.size > MAX_UPLOAD_SIZE_BYTES:
                size_mb = img.size / (1024 * 1024)
                messages.error(request, f"Maximum allowed file size is 5 MB per file. Image '{img.name}' ({size_mb:.2f} MB) was rejected.")
                continue

            try:
                validate_property_image(img)
                media_obj = PropertyMedia.objects.create(
                    property=prop,
                    file=img,
                    media_type='IMAGE',
                    display_order=idx
                )
                created_media.append(media_obj)
            except Exception as e:
                messages.warning(request, f"Image '{img.name}' validation error: {e}")

        # Main Thumbnail Selection (MODULE 6)
        if created_media:
            main_thumb = created_media[0]
            if selected_thumbnail_index is not None and str(selected_thumbnail_index).isdigit():
                idx_val = int(selected_thumbnail_index)
                if 0 <= idx_val < len(created_media):
                    main_thumb = created_media[idx_val]
            prop.thumbnail_media = main_thumb
            prop.save(update_fields=['thumbnail_media'])
        elif listing_state != ListingStateChoices.DRAFT:
            prop.listing_state = ListingStateChoices.DRAFT
            prop.save(update_fields=['listing_state'])
            messages.warning(request, "Property requires at least one property image and main thumbnail before publishing. Saved as Draft.")
            return redirect('properties:edit', slug=prop.slug)

        # Trigger Let's API external sync safely
        try:
            LetsApiAdapter.sync_property(prop)
        except Exception:
            pass

        if listing_state == ListingStateChoices.DRAFT:
            messages.success(request, "Property saved as draft successfully!")
        else:
            messages.success(request, "Your property has been submitted successfully with selected cover thumbnail and is awaiting admin review.")
        return redirect('properties:my-properties')

    states = State.objects.filter(is_active=True)
    districts = District.objects.filter(is_active=True)
    cities = City.objects.filter(is_active=True)
    localities = Locality.objects.filter(is_active=True)
    sub_localities = SubLocality.objects.filter(is_active=True)
    property_types = PropertyType.objects.all()
    amenities = Amenity.objects.all()
    context = {
        'request': request,
        'user': request.user,
        'states': states,
        'districts': districts,
        'cities': cities,
        'localities': localities,
        'sub_localities': sub_localities,
        'property_types': property_types,
        'amenities': amenities,
        'purposes': ListingPurposeChoices.choices,
        'furnishing_choices': FurnishingChoices.choices,
        'availability_choices': PossessionStatusChoices.choices,
    }
    return render_template(request, 'pages/post_property.html', context)

@login_required
def edit_property_view(request, slug):
    property_item = get_object_or_404(Property, slug=slug)

    can_post, msg = can_post_property(request.user)
    if not can_post or not can_edit_property(request.user, property_item):
        messages.error(request, "Unauthorized action: Only approved Real Estate Partners can edit property listings.")
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        # Handle media deletion
        delete_media_id = request.POST.get('delete_media_id')
        if delete_media_id:
            try:
                media_to_delete = PropertyMedia.objects.get(id=delete_media_id, property=property_item)
                is_thumbnail = (property_item.thumbnail_media_id == media_to_delete.id)
                media_to_delete.delete()
                if is_thumbnail:
                    remaining_media = property_item.media.filter(media_type='IMAGE').first()
                    property_item.thumbnail_media = remaining_media
                    property_item.save(update_fields=['thumbnail_media'])
                    messages.info(request, "Selected thumbnail was deleted. Thumbnail updated to next available photo.")
                else:
                    messages.success(request, "Image deleted successfully.")
                return redirect('properties:edit', slug=property_item.slug)
            except PropertyMedia.DoesNotExist:
                pass

        property_item.title = request.POST.get('title', property_item.title)
        property_item.description = request.POST.get('description', property_item.description)

        state_id = request.POST.get('state')
        district_id = request.POST.get('district')
        city_id = request.POST.get('city')
        locality_id = request.POST.get('locality')
        sub_locality_id = request.POST.get('sub_locality')

        if state_id:
            property_item.state = get_object_or_404(State, id=state_id)
        if district_id:
            property_item.district = get_object_or_404(District, id=district_id)
        if city_id:
            property_item.city = get_object_or_404(City, id=city_id)
        if locality_id:
            property_item.locality = get_object_or_404(Locality, id=locality_id)
        property_item.sub_locality = get_object_or_404(SubLocality, id=sub_locality_id) if sub_locality_id else None

        price_val = request.POST.get('price')
        if price_val:
            new_p = float(price_val)
            if property_item.price and new_p < float(property_item.price):
                PropertyPriceHistory.objects.create(
                    property=property_item,
                    previous_price=property_item.price,
                    new_price=new_p
                )
            property_item.price = new_p

        rent_val = request.POST.get('rent')
        if rent_val:
            property_item.rent = float(rent_val)

        # Selected Main Thumbnail Update (MODULE 6)
        selected_thumb_id = request.POST.get('selected_thumbnail_id')
        if selected_thumb_id:
            try:
                thumb_media = PropertyMedia.objects.get(id=selected_thumb_id, property=property_item)
                property_item.thumbnail_media = thumb_media
            except PropertyMedia.DoesNotExist:
                pass

        if property_item.listing_state == ListingStateChoices.ACTIVE:
            property_item.listing_state = ListingStateChoices.PENDING_APPROVAL
            messages.info(request, "Property updated and submitted for re-review moderation.")
        else:
            messages.success(request, "Property updated successfully.")

        property_item.save()

        # Handle newly uploaded images (Max 8 limit)
        images = request.FILES.getlist('images')
        MAX_PROPERTY_IMAGES = 8
        current_media_count = property_item.media.count()

        if current_media_count >= MAX_PROPERTY_IMAGES and images:
            messages.warning(request, f"Property already has the maximum of {MAX_PROPERTY_IMAGES} photos uploaded. No additional images were added.")
            images = []
        elif current_media_count + len(images) > MAX_PROPERTY_IMAGES:
            allowed_slots = MAX_PROPERTY_IMAGES - current_media_count
            messages.warning(request, f"Maximum limit of {MAX_PROPERTY_IMAGES} photos reached. Only the first {allowed_slots} new photo(s) were added.")
            images = images[:allowed_slots]

        newly_created = []

        for idx, img in enumerate(images):
            if img.size > MAX_UPLOAD_SIZE_BYTES:
                size_mb = img.size / (1024 * 1024)
                messages.error(request, f"Maximum allowed file size is 5 MB per file. Image '{img.name}' ({size_mb:.2f} MB) was rejected.")
                continue

            try:
                validate_property_image(img)
                m_obj = PropertyMedia.objects.create(
                    property=property_item,
                    file=img,
                    media_type='IMAGE',
                    display_order=current_media_count + idx
                )
                newly_created.append(m_obj)
            except Exception as e:
                messages.warning(request, f"Image '{img.name}' validation error: {e}")

        # If property had no thumbnail set, set to first available
        if not property_item.thumbnail_media:
            first_m = property_item.media.filter(media_type='IMAGE').first()
            if first_m:
                property_item.thumbnail_media = first_m
                property_item.save(update_fields=['thumbnail_media'])

        return redirect('properties:detail', slug=property_item.slug)

    states = State.objects.filter(is_active=True)
    districts = District.objects.filter(is_active=True)
    cities = City.objects.filter(is_active=True)
    localities = Locality.objects.filter(is_active=True)
    sub_localities = SubLocality.objects.filter(is_active=True)
    property_types = PropertyType.objects.all()
    amenities = Amenity.objects.all()
    context = {
        'request': request,
        'user': request.user,
        'property': property_item,
        'states': states,
        'districts': districts,
        'cities': cities,
        'localities': localities,
        'sub_localities': sub_localities,
        'property_types': property_types,
        'amenities': amenities,
        'purposes': ListingPurposeChoices.choices,
        'furnishing_choices': FurnishingChoices.choices,
    }
    return render_template(request, 'pages/post_property.html', context)

@login_required
@role_required(RoleChoices.OWNER, RoleChoices.AGENT, RoleChoices.DEVELOPER, RoleChoices.ADMIN)
def my_properties_view(request):
    status_filter = request.GET.get('status', 'ALL')
    properties = Property.objects.filter(owner=request.user).select_related('city', 'locality', 'property_type')

    if status_filter != 'ALL':
        properties = properties.filter(listing_state=status_filter)

    total_listings = Property.objects.filter(owner=request.user).count()
    draft_count = Property.objects.filter(owner=request.user, listing_state=ListingStateChoices.DRAFT).count()
    pending_count = Property.objects.filter(owner=request.user, listing_state=ListingStateChoices.PENDING_APPROVAL).count()
    approved_count = Property.objects.filter(owner=request.user, listing_state=ListingStateChoices.ACTIVE).count()
    rejected_count = Property.objects.filter(owner=request.user, listing_state=ListingStateChoices.REJECTED).count()

    context = {
        'request': request,
        'user': request.user,
        'properties': properties,
        'status_filter': status_filter,
        'total_listings': total_listings,
        'draft_count': draft_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render_template(request, 'dashboard/my_properties.html', context)
