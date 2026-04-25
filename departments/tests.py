from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from departments.models import Department
from knowledgebase.models import Tutorial


class DepartmentDeleteSafetyTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="HR", description="Human Resources")
        self.admin = User.objects.create_user(
            username="admin_dept",
            email="admin_dept@example.com",
            password="StrongPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )

    def test_cannot_delete_department_with_related_users_or_tutorials(self):
        User.objects.create_user(
            username="department_user",
            email="department_user@example.com",
            password="StrongPass123!",
            role=User.Role.USER,
            department=self.department,
        )
        tutorial = Tutorial.objects.create(
            title="HR Policy",
            description="Policy",
            content="Details",
            department=self.department,
            created_by=self.admin,
            is_published=True,
        )

        self.client.force_login(self.admin)
        response = self.client.post(reverse("departments:delete", args=[self.department.id]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Department.objects.filter(id=self.department.id).exists())
        self.assertTrue(Tutorial.objects.filter(id=tutorial.id).exists())
