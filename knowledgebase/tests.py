import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from departments.models import Department
from knowledgebase.models import Tutorial


class KnowledgebaseFlowTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.temp_media.name)
        self.media_override.enable()

        self.department = Department.objects.create(name="IT", description="IT Department")
        self.admin = User.objects.create_user(
            username="kb_admin",
            email="kb_admin@example.com",
            password="StrongPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )

    def tearDown(self):
        self.media_override.disable()
        self.temp_media.cleanup()

    def test_editor_without_department_cannot_open_tutorial_list(self):
        editor = User.objects.create_user(
            username="kb_editor_no_dept",
            email="kb_editor_no_dept@example.com",
            password="StrongPass123!",
            role=User.Role.EDITOR,
        )
        self.client.force_login(editor)

        response = self.client.get(reverse("knowledgebase:tutorial-list"))

        self.assertEqual(response.status_code, 403)

    def test_video_replacement_removes_old_file(self):
        tutorial = Tutorial.objects.create(
            title="Video tutorial",
            description="Desc",
            content="Body",
            department=self.department,
            created_by=self.admin,
            is_published=True,
        )
        tutorial.video_file.save(
            "old.mp4",
            SimpleUploadedFile("old.mp4", b"old-video-bytes", content_type="video/mp4"),
            save=True,
        )
        old_file_path = Path(tutorial.video_file.path)
        self.assertTrue(old_file_path.exists())

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("knowledgebase:tutorial-edit", args=[tutorial.id]),
            data={
                "title": tutorial.title,
                "description": tutorial.description,
                "content": tutorial.content,
                "department": str(self.department.id),
                "is_published": "on",
                "video_caption": "New caption",
                "remove_video": "",
                "video_file": SimpleUploadedFile("new.mp4", b"new-video-bytes", content_type="video/mp4"),
                "images-TOTAL_FORMS": "0",
                "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "5",
                "video_urls-TOTAL_FORMS": "0",
                "video_urls-INITIAL_FORMS": "0",
                "video_urls-MIN_NUM_FORMS": "0",
                "video_urls-MAX_NUM_FORMS": "5",
            },
        )

        self.assertEqual(response.status_code, 302)
        tutorial.refresh_from_db()
        self.assertIn("new.mp4", tutorial.video_file.name)
        self.assertFalse(old_file_path.exists())
