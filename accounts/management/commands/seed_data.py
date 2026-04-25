import base64

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from accounts.models import User
from departments.models import Department
from knowledgebase.models import ReadHistory, Tutorial, TutorialImage, TutorialVideo


SMALL_PNG_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+WvN8AAAAASUVORK5CYII="


class Command(BaseCommand):
    help = "Seed sample departments, users, tutorials, and read history data."

    def handle(self, *args, **options):
        engineering, _ = Department.objects.get_or_create(
            name="Engineering",
            defaults={"description": "Software engineering tutorials and docs."},
        )
        hr, _ = Department.objects.get_or_create(
            name="HR",
            defaults={"description": "Human resources policies and onboarding docs."},
        )
        finance, _ = Department.objects.get_or_create(
            name="Finance",
            defaults={"description": "Financial procedures and reports guidance."},
        )

        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@hubdesk.local",
                "role": User.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "full_name": "Main Admin",
            },
        )
        if not admin_user.check_password("admin12345"):
            admin_user.set_password("admin12345")
            admin_user.save()

        editor_user, _ = User.objects.get_or_create(
            username="editor",
            defaults={
                "email": "editor@hubdesk.local",
                "role": User.Role.EDITOR,
                "department": engineering,
                "full_name": "Main Editor",
            },
        )
        if not editor_user.check_password("editor12345"):
            editor_user.set_password("editor12345")
            editor_user.department = engineering
            editor_user.save()

        simple_user, _ = User.objects.get_or_create(
            username="user",
            defaults={
                "email": "user@hubdesk.local",
                "role": User.Role.USER,
                "department": engineering,
                "full_name": "Simple User",
            },
        )
        if not simple_user.check_password("user12345"):
            simple_user.set_password("user12345")
            simple_user.department = engineering
            simple_user.save()

        tutorials = [
            {
                "title": "Django Project Setup Guide",
                "description": "How to start and structure Django projects in our company.",
                "content": "This tutorial explains project setup, environments, and coding rules.",
                "department": engineering,
                "created_by": editor_user,
                "video_url": "https://www.youtube.com/watch?v=F5mRW0jo-U4",
                "is_published": True,
            },
            {
                "title": "HR Onboarding Checklist",
                "description": "Employee onboarding process for first week.",
                "content": "Follow these onboarding tasks for smooth first-week adaptation.",
                "department": hr,
                "created_by": admin_user,
                "is_published": True,
            },
            {
                "title": "Finance Monthly Reporting",
                "description": "How to prepare monthly reports.",
                "content": "Monthly finance report preparation steps and data validation workflow.",
                "department": finance,
                "created_by": admin_user,
                "is_published": False,
            },
        ]

        for item in tutorials:
            tutorial, created = Tutorial.objects.get_or_create(
                title=item["title"],
                defaults=item,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created tutorial: {tutorial.title}"))
            image_file = ContentFile(base64.b64decode(SMALL_PNG_BASE64), name=f"{tutorial.id}_sample.png")
            TutorialImage.objects.get_or_create(
                tutorial=tutorial,
                caption="Sample image",
                defaults={"image": image_file},
            )
            if tutorial.department == engineering:
                ReadHistory.objects.get_or_create(user=simple_user, tutorial=tutorial)

            if tutorial.title == "Django Project Setup Guide":
                TutorialVideo.objects.get_or_create(
                    tutorial=tutorial,
                    video_url="https://www.youtube.com/watch?v=F5mRW0jo-U4",
                    defaults={"caption": "Setup walkthrough"},
                )
                TutorialVideo.objects.get_or_create(
                    tutorial=tutorial,
                    video_url="https://www.youtube.com/watch?v=rHux0gMZ3Eg",
                    defaults={"caption": "Environment tips"},
                )

        self.stdout.write(self.style.SUCCESS("Seed data created successfully."))
        self.stdout.write("Admin: admin / admin12345")
        self.stdout.write("Editor: editor / editor12345")
        self.stdout.write("User: user / user12345")
