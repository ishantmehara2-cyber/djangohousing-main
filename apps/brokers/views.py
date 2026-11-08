from django.shortcuts import render
from apps.accounts.models import User, RoleChoices

def brokers_list_view(request):
    agents = User.objects.filter(role__in=[RoleChoices.AGENT, RoleChoices.DEVELOPER], status='ACTIVE')
    context = {'agents': agents}
    return render(request, 'brokers/brokers_list.html', context)
