import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from apps.properties.models import PropertyFormField, PropertyFormFieldOption, FieldTypeChoices
from apps.moderation.models import AuditLog

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or getattr(user, 'is_admin_role', False))

@require_http_methods(["GET"])
def api_property_fields_list(request):
    """
    Public configuration API: GET /api/property-fields
    Fetch active field configuration for selected category and listing type.
    """
    category = request.GET.get('category', '').upper()
    listing_type = request.GET.get('listing_type', '').upper()

    fields = PropertyFormField.objects.filter(is_active=True).prefetch_related('options')

    filtered_fields = []
    for f in fields:
        cats = f.applicable_categories or []
        ltypes = f.applicable_listing_types or []

        cat_match = not category or 'ALL' in cats or category in cats
        ltype_match = not listing_type or 'ALL' in ltypes or listing_type in ltypes

        if cat_match and ltype_match:
            filtered_fields.append(f)

    fields_data = []
    for f in filtered_fields:
        options = [{'id': opt.id, 'label': opt.label, 'value': opt.value, 'order': opt.order} for opt in f.options.all()]
        fields_data.append({
            'id': f.id,
            'key': f.key,
            'label': f.label,
            'type': f.field_type,
            'required': f.required,
            'placeholder': f.placeholder or '',
            'help_text': f.help_text or '',
            'order': f.order,
            'options': options,
            'conditional_parent_key': f.conditional_parent_key,
            'conditional_parent_value': f.conditional_parent_value,
        })

    return JsonResponse({
        'success': True,
        'data': {
            'category': category or 'ALL',
            'listing_type': listing_type or 'ALL',
            'version': 1,
            'fields': fields_data
        }
    })

@require_http_methods(["GET", "POST"])
@csrf_exempt
def api_admin_property_fields(request):
    """
    Admin APIs:
    GET /api/admin/property-fields - Fetch all fields including disabled
    POST /api/admin/property-fields - Create a new field
    """
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Unauthorized admin access'}, status=403)

    if request.method == 'GET':
        fields = PropertyFormField.objects.all().prefetch_related('options')
        data = []
        for f in fields:
            options = [{'id': opt.id, 'label': opt.label, 'value': opt.value, 'order': opt.order} for opt in f.options.all()]
            data.append({
                'id': f.id,
                'key': f.key,
                'label': f.label,
                'type': f.field_type,
                'required': f.required,
                'is_active': f.is_active,
                'order': f.order,
                'placeholder': f.placeholder or '',
                'help_text': f.help_text or '',
                'applicable_categories': f.applicable_categories,
                'applicable_listing_types': f.applicable_listing_types,
                'is_system_field': f.is_system_field,
                'options': options,
            })
        return JsonResponse({'success': True, 'data': data})

    elif request.method == 'POST':
        try:
            body = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            key = body.get('key')
            label = body.get('label')
            field_type = body.get('field_type', body.get('type', 'text'))
            required = bool(body.get('required', False))
            order = int(body.get('order', 0))
            placeholder = body.get('placeholder', '')
            help_text = body.get('help_text', '')
            categories = body.get('applicable_categories', ['ALL'])
            listing_types = body.get('applicable_listing_types', ['ALL'])

            if isinstance(categories, str):
                categories = [c.strip() for c in categories.split(',') if c.strip()]
            if isinstance(listing_types, str):
                listing_types = [l.strip() for l in listing_types.split(',') if l.strip()]

            if not key or not label:
                return JsonResponse({'success': False, 'error': 'Key and label are required.'}, status=400)

            if PropertyFormField.objects.filter(key=key).exists():
                return JsonResponse({'success': False, 'error': f'Field with key "{key}" already exists.'}, status=400)

            field_obj = PropertyFormField.objects.create(
                key=key,
                label=label,
                field_type=field_type,
                required=required,
                order=order,
                placeholder=placeholder,
                help_text=help_text,
                applicable_categories=categories,
                applicable_listing_types=listing_types,
                is_active=True,
                is_system_field=False
            )

            AuditLog.objects.create(
                user=request.user,
                action='CREATE_PROPERTY_FIELD',
                entity='PropertyFormField',
                entity_id=str(field_obj.id),
                payload={'key': key, 'label': label}
            )

            return JsonResponse({'success': True, 'message': 'Field created successfully.', 'id': field_obj.id})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["GET", "PUT", "DELETE"])
@csrf_exempt
def api_admin_property_field_detail(request, pk):
    """
    GET /api/admin/property-fields/{id}
    PUT /api/admin/property-fields/{id}
    """
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    field_obj = get_object_or_404(PropertyFormField, pk=pk)

    if request.method == 'GET':
        options = [{'id': opt.id, 'label': opt.label, 'value': opt.value, 'order': opt.order} for opt in field_obj.options.all()]
        return JsonResponse({
            'success': True,
            'data': {
                'id': field_obj.id,
                'key': field_obj.key,
                'label': field_obj.label,
                'type': field_obj.field_type,
                'required': field_obj.required,
                'is_active': field_obj.is_active,
                'order': field_obj.order,
                'placeholder': field_obj.placeholder or '',
                'help_text': field_obj.help_text or '',
                'applicable_categories': field_obj.applicable_categories,
                'applicable_listing_types': field_obj.applicable_listing_types,
                'is_system_field': field_obj.is_system_field,
                'options': options,
            }
        })

    elif request.method == 'PUT':
        try:
            body = json.loads(request.body) if request.content_type == 'application/json' else request.POST

            new_key = body.get('key')
            if new_key and new_key != field_obj.key:
                if field_obj.is_system_field:
                    return JsonResponse({'success': False, 'error': 'Cannot change internal key of core system fields.'}, status=400)
                if PropertyFormField.objects.filter(key=new_key).exclude(pk=pk).exists():
                    return JsonResponse({'success': False, 'error': f'Field with key "{new_key}" already exists.'}, status=400)
                field_obj.key = new_key

            field_obj.label = body.get('label', field_obj.label)
            field_obj.field_type = body.get('type', body.get('field_type', field_obj.field_type))
            field_obj.required = bool(body.get('required', field_obj.required))
            field_obj.order = int(body.get('order', field_obj.order))
            field_obj.placeholder = body.get('placeholder', field_obj.placeholder)
            field_obj.help_text = body.get('help_text', field_obj.help_text)

            cats = body.get('applicable_categories', field_obj.applicable_categories)
            ltypes = body.get('applicable_listing_types', field_obj.applicable_listing_types)
            if isinstance(cats, str):
                cats = [c.strip() for c in cats.split(',') if c.strip()]
            if isinstance(ltypes, str):
                ltypes = [l.strip() for l in ltypes.split(',') if l.strip()]
            field_obj.applicable_categories = cats
            field_obj.applicable_listing_types = ltypes

            field_obj.save()

            AuditLog.objects.create(
                user=request.user,
                action='UPDATE_PROPERTY_FIELD',
                entity='PropertyFormField',
                entity_id=str(field_obj.id),
                payload={'key': field_obj.key, 'label': field_obj.label}
            )

            return JsonResponse({'success': True, 'message': 'Field updated successfully.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["PATCH"])
@csrf_exempt
def api_admin_property_field_status(request, pk):
    """
    PATCH /api/admin/property-fields/{id}/status
    Enable or disable a field.
    """
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    field_obj = get_object_or_404(PropertyFormField, pk=pk)
    try:
        body = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        is_active = body.get('is_active')
        if is_active is None:
            is_active = not field_obj.is_active
        else:
            is_active = bool(is_active)

        if field_obj.is_system_field and not is_active and field_obj.required:
            return JsonResponse({'success': False, 'error': 'Cannot disable required core system fields.'}, status=400)

        field_obj.is_active = is_active
        field_obj.save(update_fields=['is_active', 'updated_at'])

        AuditLog.objects.create(
            user=request.user,
            action='TOGGLE_PROPERTY_FIELD_STATUS',
            entity='PropertyFormField',
            entity_id=str(field_obj.id),
            payload={'key': field_obj.key, 'is_active': is_active}
        )

        return JsonResponse({'success': True, 'is_active': field_obj.is_active})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["PUT"])
@csrf_exempt
def api_admin_property_fields_reorder(request):
    """
    PUT /api/admin/property-fields/reorder
    Update field ordering.
    """
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    try:
        body = json.loads(request.body)
        orders = body.get('orders', [])
        for item in orders:
            f_id = item.get('id')
            new_order = item.get('order')
            if f_id is not None and new_order is not None:
                PropertyFormField.objects.filter(pk=f_id).update(order=new_order)

        AuditLog.objects.create(
            user=request.user,
            action='REORDER_PROPERTY_FIELDS',
            entity='PropertyFormField',
            payload={'count': len(orders)}
        )

        return JsonResponse({'success': True, 'message': 'Fields reordered successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@require_http_methods(["POST", "PUT"])
@csrf_exempt
def api_admin_property_field_options(request, pk):
    """
    POST /api/admin/property-fields/{id}/options
    Create or update dropdown options.
    """
    if not is_admin(request.user):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    field_obj = get_object_or_404(PropertyFormField, pk=pk)
    try:
        body = json.loads(request.body)
        options = body.get('options', [])

        field_obj.options.all().delete()
        for idx, opt in enumerate(options):
            PropertyFormFieldOption.objects.create(
                field=field_obj,
                label=opt.get('label'),
                value=opt.get('value'),
                order=opt.get('order', idx)
            )

        AuditLog.objects.create(
            user=request.user,
            action='UPDATE_FIELD_OPTIONS',
            entity='PropertyFormField',
            entity_id=str(field_obj.id),
            payload={'options_count': len(options)}
        )

        return JsonResponse({'success': True, 'message': 'Field options updated successfully.'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
