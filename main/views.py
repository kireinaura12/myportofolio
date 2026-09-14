from django.shortcuts import render

# Create your views here.
from django.shortcuts import render

from main.models import Experience, Project


def show_main(request):
    context = {
        "name": "Kireina Naura Alifa",
        "npm": "2506590006",
        "study_program": "S1 Ilmu Komputer",
        "bio": (
            "Hi! I'm a second-year student with a growing interest in Product Management and Data Science. I actively explore other areas of computer science through bootcamps, and enjoy collaborating on team-based projects that sharpen my problem solving and adaptability skills"
        ),
        "preview_experiences": Experience.objects.all()[:3],
        "preview_projects": Project.objects.all()[:3],
    }
    return render(request, "index.html", context)


def show_experience(request):
    context = {
        "name": "Kireina Naura Alifa",
        "experience_list": Experience.objects.all(),
    }
    return render(request, "experience.html", context)

def show_projects(request):
    context = {
        "name": "Kireina Naura Alifa",
        "project_list": Project.objects.all(),
    }
    return render(request, "projects.html", context)