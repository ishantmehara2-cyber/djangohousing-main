from django.shortcuts import render, get_object_or_404
from apps.projects.models import Project, DeveloperOrganization

def projects_list_view(request):
    projects = Project.objects.select_related('developer', 'city', 'locality').all()
    developers = DeveloperOrganization.objects.all()
    context = {'projects': projects, 'developers': developers}
    return render(request, 'projects/projects_list.html', context)

def project_detail_view(request, slug):
    project = get_object_or_404(Project.objects.select_related('developer', 'city', 'locality').prefetch_related('media'), slug=slug)
    context = {'project': project}
    return render(request, 'projects/project_detail.html', context)
