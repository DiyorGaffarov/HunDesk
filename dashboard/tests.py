from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from departments.models import Department
from knowledgebase.models import Tutorial


class AdminDashboardStatsTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Analytics", description="Analytics team")
        self.admin = User.objects.create_user(
            username="dashboard_admin",
            email="dashboard_admin@example.com",
            password="StrongPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        User.objects.create_user(
            username="dashboard_editor",
            email="dashboard_editor@example.com",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            department=self.department,
        )
        User.objects.create_user(
            username="dashboard_user",
            email="dashboard_user@example.com",
            password="StrongPass123!",
            role=User.Role.USER,
            department=self.department,
        )
        Tutorial.objects.create(
            title="Analytics guide",
            description="Guide",
            content="Body",
            department=self.department,
            created_by=self.admin,
            is_published=True,
        )

    def test_admin_dashboard_users_count_only_simple_users(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:admin-dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_users"], 1)
        self.assertEqual(response.context["total_editors"], 1)
