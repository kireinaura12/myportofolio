from django.shortcuts import render
from main.models import Experience, Projects
from django.contrib import messages
from django.core import serializers
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from main.forms import ProjectForm


def show_main(request):
    context = {
        "name": "Kireina Naura Alifa",
        "npm": "2506590006",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Hi! I'm a second-year student with a growing interest in Product Management and Data Science. I actively explore other areas of computer science through bootcamps, and enjoy collaborating on team-based projects that sharpen my problem solving and adaptability skills"
        ),
        "preview_experiences": Experience.objects.all()[:3],
        "preview_projects": Projects.objects.all()[:3],
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Kireina Naura Alifa",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

def show_projects(request):
    json_response = get_projects_json(request)

    projects = serializers.deserialize(
        "json",
        json_response.content.decode("utf-8"),
    )
    projects = [project.object for project in projects]
    title_query = request.GET.get("title", "").strip()

    context = {
        "name": "Kireina Naura Alifa",
        "project_list": Projects.objects.all(),
    }
    return render(request, "projects.html", context)

def create_project(request):
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Proyek baru berhasil ditambahkan!")
        return redirect("main:show_projects")

    context = {
        "name": "Kireina Naura Alifa",
        "form": form,
    }
    return render(request, "projects_form.html", context)

def get_projects_json(request):
    title_query = request.GET.get("title", "").strip()
    projects = Projects.objects.all()

    if title_query:
        projects = projects.filter(title__icontains=title_query)

    projects_json = serializers.serialize("json", projects)
    return HttpResponse(projects_json, content_type="application/json")

def delete_project(request, project_id):
    project = get_object_or_404(Projects, pk=project_id)

    if request.method == "POST":
        project.delete()
        messages.success(request, "Project berhasil dihapus!")
        return redirect("main:show_projects")

    return redirect("main:show_projects")
