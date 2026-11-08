import uuid

from django.contrib.auth.models import Group, User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from main.models import Experience, Projects

PASSWORD = "StrongPass123!"
ORIGINAL_TITLE = "Asisten Dosen PBP"
DRIVE_URL = "https://drive.google.com/thumbnail?id=abc123&sz=w1000"


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

class ExperienceAPITestCase(APITestCase):
    def setUp(self):
        editor_group, _ = Group.objects.get_or_create(name="Editor")

        self.owner = User.objects.create_superuser("owner", "owner@example.com", PASSWORD)
        self.editor = User.objects.create_user("editor", "editor@example.com", PASSWORD)
        self.editor.groups.add(editor_group)
        self.regular = User.objects.create_user("regular", "regular@example.com", PASSWORD)

        self.experience = Experience.objects.create(
            title=ORIGINAL_TITLE,
            description="Membantu mahasiswa belajar Django.",
            category="part-time",
        )

        self.list_url = reverse("api:experience-list")
        self.detail_url = reverse("api:experience-detail", args=[self.experience.id])
        self.star_url = reverse("api:experience-star", args=[self.experience.id])
        self.payload = {
            "title": "Magang Data Scientist",
            "description": "Menganalisis data pengguna.",
            "category": "internship",
        }
        
    def assert_database_untouched(self):
        self.assertEqual(Experience.objects.count(), 1)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, ORIGINAL_TITLE)
        self.assertFalse(Experience.objects.filter(title=self.payload["title"]).exists())
        self.assertFalse(Experience.objects.filter(title="Hacked").exists())

    def assert_all_writes_rejected(self):
        attempts = [
            ("post", self.list_url, self.payload),
            ("put", self.detail_url, self.payload),
            ("patch", self.detail_url, {"title": "Hacked"}),
            ("delete", self.detail_url, None),
        ]
        for method, url, data in attempts:
            with self.subTest(method=method):
                response = getattr(self.client, method)(url, data, format="json")
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assert_database_untouched()


class ExperienceReadTests(ExperienceAPITestCase):
    def test_visitor_can_read_list_and_detail(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], ORIGINAL_TITLE)
        self.assertFalse(response.data[0]["is_starred"])

        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["category_display"], "Part-Time")
        self.assertTrue(response.data["is_ongoing"])

    def test_missing_experience_returns_404(self):
        missing = reverse("api:experience-detail", args=[uuid.uuid4()])
        self.assertEqual(self.client.get(missing).status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(user=self.owner)
        self.assertEqual(self.client.patch(missing, {"title": "x"}, format="json").status_code,
                         status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.client.delete(missing).status_code, status.HTTP_404_NOT_FOUND)

        missing_star = reverse("api:experience-star", args=[uuid.uuid4()])
        self.assertEqual(self.client.post(missing_star).status_code, status.HTTP_404_NOT_FOUND)


    def test_search_by_title_query_parameter(self):
        Experience.objects.create(title="Volunteer Event", description="Panitia", category="volunteer")

        response = self.client.get(self.list_url, {"title": "asisten"})
        self.assertEqual([item["title"] for item in response.data], [ORIGINAL_TITLE])

        response = self.client.get(self.list_url, {"title": "tidak-ada"})
        self.assertEqual(response.data, [])


class ExperiencePermissionTests(ExperienceAPITestCase):
    def test_visitor_cannot_write(self):
        self.assert_all_writes_rejected()

    def test_regular_user_cannot_write(self):
        self.client.force_authenticate(user=self.regular)
        self.assert_all_writes_rejected()

    def test_editor_can_patch_and_put(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.patch(self.detail_url, {"title": "Asisten Dosen Senior"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Asisten Dosen Senior")

        response = self.client.put(self.detail_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, self.payload["title"])
        self.assertEqual(self.experience.category, "internship")

    def test_editor_cannot_create_or_delete(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Experience.objects.count(), 1)
        self.assertFalse(Experience.objects.filter(title=self.payload["title"]).exists())

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())

    def test_owner_can_create_update_and_delete(self):
        self.client.force_authenticate(user=self.owner)

        response = self.client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Experience.objects.count(), 2)
        self.assertTrue(Experience.objects.filter(title=self.payload["title"]).exists())

        response = self.client.patch(self.detail_url, {"title": "Diperbarui"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, "Diperbarui")

        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Experience.objects.filter(pk=self.experience.pk).exists())


class ExperienceValidationTests(ExperienceAPITestCase):
    def setUp(self):
        super().setUp()
        self.client.force_authenticate(user=self.owner)

    def test_empty_title_is_rejected(self):
        response = self.client.post(self.list_url, {**self.payload, "title": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("title", response.data)
        self.assertEqual(Experience.objects.count(), 1)

    def test_html_only_input_is_rejected(self):
        response = self.client.post(
            self.list_url, {**self.payload, "description": "<b></b>"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)
        self.assertEqual(Experience.objects.count(), 1)

    def test_html_tags_are_stripped_before_saving(self):
        response = self.client.post(
            self.list_url, {**self.payload, "title": "<b>Magang</b> Data"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Magang Data")
        self.assertTrue(Experience.objects.filter(title="Magang Data").exists())

    def test_invalid_category_is_rejected(self):
        response = self.client.post(
            self.list_url, {**self.payload, "category": "astronaut"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("category", response.data)
        self.assertEqual(Experience.objects.count(), 1)

    def test_thumbnail_must_be_http_url(self):
        response = self.client.post(
            self.list_url, {**self.payload, "thumbnail": "javascript:alert(1)"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("thumbnail", response.data)
        self.assertEqual(Experience.objects.count(), 1)

    def test_thumbnail_url_with_query_string_is_kept_intact(self):
        response = self.client.post(
            self.list_url, {**self.payload, "thumbnail": DRIVE_URL}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["thumbnail"], DRIVE_URL)

    def test_ended_at_can_be_set_and_cleared(self):
        response = self.client.patch(
            self.detail_url, {"ended_at": "2026-05-01T10:30"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_ongoing"])

        response = self.client.patch(self.detail_url, {"ended_at": None}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_ongoing"])


class ExperienceStarTests(ExperienceAPITestCase):
    def test_visitor_cannot_star(self):
        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_user_can_star_and_unstar(self):
        self.client.force_authenticate(user=self.regular)

        response = self.client.post(self.star_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["star_count"], 1)
        self.assertTrue(response.data["is_starred"])
        self.assertEqual(list(self.experience.starred_by.all()), [self.regular])

        response = self.client.post(self.star_url)
        self.assertEqual(response.data["star_count"], 0)
        self.assertFalse(response.data["is_starred"])
        self.assertEqual(self.experience.starred_by.count(), 0)

    def test_star_account_always_comes_from_request_user(self):
        self.client.force_authenticate(user=self.regular)
        self.client.post(self.star_url, {"user": self.owner.pk, "starred_by": [self.owner.pk]}, format="json")
        self.assertEqual(list(self.experience.starred_by.all()), [self.regular])

    def test_is_starred_is_per_user_and_count_is_shared(self):
        self.experience.starred_by.add(self.regular)

        self.client.force_authenticate(user=self.regular)
        self.assertTrue(self.client.get(self.detail_url).data["is_starred"])

        self.client.force_authenticate(user=self.editor)
        data = self.client.get(self.detail_url).data
        self.assertFalse(data["is_starred"])
        self.assertEqual(data["star_count"], 1)

    def test_sensitive_account_data_is_not_exposed(self):
        self.experience.starred_by.add(self.regular)
        self.client.force_authenticate(user=self.regular)
        body = str(self.client.get(self.list_url).data)
        self.assertNotIn("regular@example.com", body)
        self.assertNotIn("password", body.lower())

    def test_api_exposes_only_expected_fields(self):
        keys = set(self.client.get(self.detail_url).json().keys())
        self.assertEqual(
            keys,
            {
                "id", "title", "description", "category", "category_display",
                "thumbnail", "started_at", "ended_at", "is_ongoing",
                "star_count", "is_starred",
            },
        )

    def test_star_does_not_allow_editing_content(self):
        self.client.force_authenticate(user=self.regular)
        self.client.post(self.star_url)
        response = self.client.patch(self.detail_url, {"title": "Hacked"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.experience.refresh_from_db()
        self.assertEqual(self.experience.title, ORIGINAL_TITLE)


class ExperienceCSRFTests(ExperienceAPITestCase):
    def make_client(self):
        client = APIClient(enforce_csrf_checks=True)
        self.assertTrue(client.login(username="owner", password=PASSWORD))
        return client

    def test_write_without_csrf_token_is_rejected(self):
        client = self.make_client()

        response = client.post(self.list_url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Experience.objects.count(), 1)

        response = client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Experience.objects.filter(pk=self.experience.pk).exists())

    def test_write_with_csrf_token_from_page_succeeds(self):
        client = self.make_client()

        page = client.get(reverse("main:show_experience"))
        self.assertEqual(page.status_code, status.HTTP_200_OK)
        token = client.cookies["csrftoken"].value

        response = client.post(
            self.list_url, self.payload, format="json", HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Experience.objects.count(), 2)