from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from main.models import Experience, Projects


class MainTest(TestCase):
    def setUp(self):
        self.experience = Experience.objects.create(
            title="Asisten Dosen PBP",
            description="Membantu mahasiswa memahami pengembangan web.",
            category="part-time",
        )
        self.project = Projects.objects.create(
            title="NexTask",
            description="Productivity app untuk membantu mahasiswa mengatur tugas.",
            tech_stack="Django, Python",
            project_url="https://example.com/nextask",
            project_image_url="https://example.com/nextask.png",
        )

    def test_main_url_is_accessible(self):
        response = self.client.get(reverse("main:show_main"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "index.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.project.title)
        self.assertContains(response, f'href="{reverse("main:show_experience")}"')

    def test_nonexistent_page_returns_404(self):
        response = self.client.get("/halaman-yang-tidak-ada/")

        self.assertEqual(response.status_code, 404)

    def test_experience_model(self):
        self.assertEqual(str(self.experience), "Asisten Dosen PBP")
        self.assertEqual(self.experience.category, "part-time")
        self.assertTrue(self.experience.is_ongoing)

    def test_experience_page(self):
        response = self.client.get(reverse("main:show_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience.html")
        self.assertContains(response, self.experience.title)
        self.assertContains(response, self.experience.description)
        self.assertContains(response, "Part-Time")
        self.assertContains(response, "Sedang berlangsung")
        self.assertContains(response, f'href="{reverse("main:show_main")}"')

    def test_empty_experience_page(self):
        Experience.objects.all().delete()
        response = self.client.get(reverse("main:show_experience"))

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_completed_experience(self):
        self.experience.ended_at = timezone.now()
        self.experience.save()
        response = self.client.get(reverse("main:show_experience"))

        self.assertFalse(self.experience.is_ongoing)
        self.assertContains(response, "Selesai")
        self.assertNotContains(response, "Sedang berlangsung")

    def test_experience_form_page(self):
        response = self.client.get(reverse("main:create_experience"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "experience_form.html")

    def test_create_experience(self):
        response = self.client.post(
            reverse("main:create_experience"),
            {
                "title": "Magang Data Analyst",
                "description": "Menganalisis data penjualan.",
                "category": "internship",
                "thumbnail": "",
                "ended_at": "",
            },
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertTrue(Experience.objects.filter(title="Magang Data Analyst").exists())

    def test_create_experience_invalid(self):
        response = self.client.post(
            reverse("main:create_experience"),
            {"title": "", "description": "", "category": "internship"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Experience.objects.count(), 1)

    def test_update_experience(self):
        url = reverse("main:update_experience", args=[self.experience.id])

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "Edit Experience")

        response = self.client.post(
            url,
            {
                "title": "Asisten Dosen Baru",
                "description": self.experience.description,
                "category": "part-time",
                "thumbnail": "",
                "ended_at": "",
            },
        )

        self.assertRedirects(response, reverse("main:show_experience"))
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Asisten Dosen Baru")
        self.assertEqual(Experience.objects.count(), 1)

    def test_delete_experience(self):
        url = reverse("main:delete_experience", args=[self.experience.id])

        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Experience.objects.count(), 1)

        response = self.client.post(url)

        self.assertRedirects(response, reverse("main:show_experience"))
        self.assertEqual(Experience.objects.count(), 0)

    def test_experience_json(self):
        response = self.client.get(reverse("main:get_experiences_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["fields"]["title"], self.experience.title)

    def test_experience_search(self):
        response = self.client.get(reverse("main:show_experience"), {"title": "tidak-ada"})

        self.assertContains(response, "Belum ada pengalaman yang ditambahkan.")

    def test_projects_url_is_accessible(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "projects.html")

    def test_projects_page_shows_data(self):
        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, self.project.title)
        self.assertContains(response, self.project.description)

    def test_projects_page_empty_state(self):
        Projects.objects.all().delete()
        response = self.client.get(reverse("main:show_projects"))

        self.assertContains(response, "Belum ada proyek yang ditambahkan.")

    def test_create_project(self):
        response = self.client.post(
            reverse("main:create_project"),
            {
                "title": "Portfolio Website",
                "description": "Website portfolio pribadi.",
                "tech_stack": "Django, HTML, CSS",
                "project_url": "https://example.com/portfolio",
                "project_image_url": "",
                "project_date": "2025-01-15",
            },
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertTrue(Projects.objects.filter(title="Portfolio Website").exists())

    def test_update_project(self):
        url = reverse("main:update_project", args=[self.project.id])

        get_response = self.client.get(url)
        self.assertEqual(get_response.status_code, 200)
        self.assertContains(get_response, "Edit Project")

        response = self.client.post(
            url,
            {
                "title": "NexTask v2",
                "description": self.project.description,
                "tech_stack": self.project.tech_stack,
                "project_url": self.project.project_url,
                "project_image_url": self.project.project_image_url,
                "project_date": "2025-02-01",
            },
        )

        self.assertRedirects(response, reverse("main:show_projects"))
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "NexTask v2")
        self.assertEqual(Projects.objects.count(), 1)

    def test_delete_project(self):
        url = reverse("main:delete_project", args=[self.project.id])

        self.assertEqual(self.client.get(url).status_code, 405)

        response = self.client.post(url)

        self.assertRedirects(response, reverse("main:show_projects"))
        self.assertEqual(Projects.objects.count(), 0)

    def test_projects_json_and_search(self):
        response = self.client.get(reverse("main:get_projects_json"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(response.json()[0]["fields"]["title"], "NexTask")

        empty = self.client.get(reverse("main:get_projects_json"), {"title": "tidak-ada"})
        self.assertEqual(empty.json(), [])