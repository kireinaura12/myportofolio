import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from main.models import Projects


class ProjectAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_superuser("owner", password="pass12345")
        self.editor = User.objects.create_user("editor", password="pass12345")
        self.editor.groups.add(Group.objects.get_or_create(name="Editor")[0])
        self.user = User.objects.create_user(
            "biasa",
            email="secret@example.com",
            password="pass12345",
        )
        self.project = Projects.objects.create(
            title="NexTask",
            description="Productivity app.",
            tech_stack="Django, Python",
            project_url="https://example.com/nextask",
        )
        self.list_url = reverse("api:project-list")
        self.detail_url = reverse("api:project-detail", args=[self.project.id])
        self.star_url = reverse("api:project-star", args=[self.project.id])
        self.payload = {
            "title": "Baru",
            "description": "Deskripsi baru.",
            "tech_stack": "Python",
        }

    def test_anonymous_can_list_projects(self):
        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["title"], "NexTask")
        self.assertEqual(response.json()[0]["star_count"], 0)
        self.assertFalse(response.json()[0]["is_starred"])

    def test_anonymous_can_view_detail_and_missing_returns_404(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], str(self.project.id))

        missing = reverse("api:project-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(missing).status_code, 404)

    def test_search_and_empty_result(self):
        found = self.client.get(self.list_url, {"title": "next"})
        self.assertEqual(len(found.json()), 1)

        empty = self.client.get(self.list_url, {"title": "tidak-ada"})
        self.assertEqual(empty.status_code, 200)
        self.assertEqual(empty.json(), [])

        Projects.objects.all().delete()
        self.assertEqual(self.client.get(self.list_url).json(), [])

    def test_anonymous_cannot_write(self):
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.put(self.detail_url, self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.patch(self.detail_url, {"title": "X"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Projects.objects.count(), 1)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, "NexTask")

    def test_regular_user_can_read_and_star_but_not_manage(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(self.list_url).status_code, 200)
        self.assertEqual(self.client.post(self.star_url).status_code, 200)
        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.put(self.detail_url, self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.patch(self.detail_url, {"title": "X"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(Projects.objects.count(), 1)

    def test_owner_can_create_put_patch_and_delete(self):
        self.client.force_login(self.owner)

        created = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(created.status_code, 201)
        new_url = reverse("api:project-detail", args=[created.json()["id"]])

        put = self.client.put(
            new_url,
            {**self.payload, "title": "Diganti Penuh"},
            format="json",
        )
        self.assertEqual(put.status_code, 200)
        self.assertEqual(put.json()["title"], "Diganti Penuh")

        patch = self.client.patch(new_url, {"tech_stack": "Django"}, format="json")
        self.assertEqual(patch.status_code, 200)
        self.assertEqual(patch.json()["tech_stack"], "Django")

        self.assertEqual(self.client.delete(new_url).status_code, 204)
        self.assertFalse(Projects.objects.filter(pk=created.json()["id"]).exists())

    def test_editor_can_patch_but_not_create_or_delete(self):
        self.client.force_login(self.editor)

        patch = self.client.patch(self.detail_url, {"title": "Judul Baru"}, format="json")
        self.assertEqual(patch.status_code, 200)
        put = self.client.put(
            self.detail_url, {**self.payload, "title": "Put Editor"}, format="json",
        )
        self.assertEqual(put.status_code, 200)

        self.assertEqual(self.client.post(self.list_url, self.payload, format="json").status_code, 403)
        self.assertEqual(self.client.delete(self.detail_url).status_code, 403)
        self.assertEqual(self.client.post(self.star_url).status_code, 200)
        self.assertTrue(Projects.objects.filter(pk=self.project.id).exists())

    def test_star_uses_logged_in_user_and_toggles(self):
        other = User.objects.create_user("lain", password="pass12345")
        self.client.force_login(self.user)

        first = self.client.post(self.star_url, {"user": other.id}, format="json")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["star_count"], 1)
        self.assertTrue(first.json()["is_starred"])
        self.assertEqual(list(self.project.starred_by.all()), [self.user])

        second = self.client.post(self.star_url)
        self.assertEqual(second.json()["star_count"], 0)
        self.assertFalse(second.json()["is_starred"])

    def test_star_requires_login(self):
        response = self.client.post(self.star_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.project.starred_by.count(), 0)

    def test_computed_fields_cannot_be_set_by_client(self):
        self.client.force_login(self.owner)
        forged_id = str(uuid.uuid4())

        created = self.client.post(
            self.list_url,
            {
                **self.payload,
                "id": forged_id,
                "star_count": 99,
                "is_starred": True,
                "starred_by_names": "palsu",
                "starred_by": [self.user.id],
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        data = created.json()
        self.assertNotEqual(data["id"], forged_id)
        self.assertEqual(data["star_count"], 0)
        self.assertFalse(data["is_starred"])
        self.assertEqual(data["starred_by_names"], "")

        patched = self.client.patch(
            self.detail_url, {"starred_by": [self.user.id], "star_count": 50}, format="json",
        )
        self.assertEqual(patched.status_code, 200)
        self.assertEqual(self.project.starred_by.count(), 0)
        self.assertEqual(patched.json()["star_count"], 0)

    def test_validation_rejects_bad_input(self):
        self.client.force_login(self.owner)
        bad_payloads = {
            "title": {**self.payload, "title": "<b></b>"},
            "description": {**self.payload, "description": "<i></i>"},
            "tech_stack": {**self.payload, "tech_stack": ""},
            "project_url": {**self.payload, "project_url": "javascript:alert(1)"},
            "project_image_url": {**self.payload, "project_image_url": "bukan-url"},
        }
        for field, payload in bad_payloads.items():
            with self.subTest(field=field):
                response = self.client.post(self.list_url, payload, format="json")
                self.assertEqual(response.status_code, 400)
                self.assertIn(field, response.json())

        self.assertEqual(self.client.post(self.list_url, {}, format="json").status_code, 400)
        self.assertEqual(Projects.objects.count(), 1)

        cleaned = self.client.post(
            self.list_url, {**self.payload, "title": "<b>Bersih</b>"}, format="json",
        )
        self.assertEqual(cleaned.status_code, 201)
        self.assertEqual(cleaned.json()["title"], "Bersih")

    def test_api_does_not_expose_sensitive_account_data(self):
        self.project.starred_by.add(self.user)
        self.client.force_login(self.owner)

        for url in (self.list_url, self.detail_url):
            body = self.client.get(url).content.decode()
            for secret in ("secret@example.com", "pbkdf2", "password", "is_superuser", "email"):
                self.assertNotIn(secret, body)

        keys = set(self.client.get(self.detail_url).json().keys())
        self.assertEqual(
            keys,
            {
                "id", "title", "description", "tech_stack", "project_url",
                "project_image_url", "project_date", "star_count",
                "is_starred", "starred_by_names",
            },
        )

    def test_csrf_is_enforced_for_session_writes(self):
        client = APIClient(enforce_csrf_checks=True)
        client.force_login(self.owner)

        rejected = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(Projects.objects.count(), 1)

        client.get(reverse("main:show_projects"))
        token = client.cookies["csrftoken"].value
        accepted = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(accepted.status_code, 201)
        self.assertEqual(Projects.objects.count(), 2)