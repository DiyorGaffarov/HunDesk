from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from departments.models import Department
from knowledgebase.models import ReadHistory, Tutorial


class AccountsFlowTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Engineering", description="Eng")
        self.admin = User.objects.create_user(
            username="admin_test",
            email="admin_test@example.com",
            password="StrongPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.editor = User.objects.create_user(
            username="editor_test",
            email="editor_test@example.com",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            department=self.department,
        )

    def test_editor_can_create_simple_user_in_own_department(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse("accounts:user-create"),
            data={
                "username": "new_simple_user",
                "email": "new_simple_user@example.com",
                "phone_number": "+998901112233",
                "full_name": "New Simple User",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        created_user = User.objects.get(username="new_simple_user")
        self.assertEqual(created_user.role, User.Role.USER)
        self.assertEqual(created_user.department_id, self.department.id)
        self.assertFalse(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)

    def test_admin_role_created_from_ui_gets_django_admin_flags(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("accounts:user-create"),
            data={
                "username": "new_admin_ui",
                "email": "new_admin_ui@example.com",
                "phone_number": "",
                "full_name": "UI Admin",
                "role": User.Role.ADMIN,
                "department": "",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        created_admin = User.objects.get(username="new_admin_ui")
        self.assertTrue(created_admin.is_staff)
        self.assertTrue(created_admin.is_superuser)

    def test_logout_view_allows_post_only(self):
        self.client.force_login(self.admin)

        get_response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(get_response.status_code, 405)

        post_response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(post_response.status_code, 302)


class UserDetailViewTests(TestCase):
    def setUp(self):
        self.dept_a = Department.objects.create(name="Dept A", description="A")
        self.dept_b = Department.objects.create(name="Dept B", description="B")
        self.admin = User.objects.create_user(
            username="admin_view",
            email="admin_view@example.com",
            password="StrongPass123!",
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.editor_a = User.objects.create_user(
            username="editor_a",
            email="editor_a@example.com",
            password="StrongPass123!",
            role=User.Role.EDITOR,
            department=self.dept_a,
        )
        self.user_a = User.objects.create_user(
            username="user_a",
            email="user_a@example.com",
            password="StrongPass123!",
            role=User.Role.USER,
            department=self.dept_a,
            phone_number="+998900001122",
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            email="user_b@example.com",
            password="StrongPass123!",
            role=User.Role.USER,
            department=self.dept_b,
        )
        tutorial = Tutorial.objects.create(
            title="Viewed tutorial",
            description="Desc",
            content="Body",
            department=self.dept_a,
            created_by=self.admin,
            is_published=True,
        )
        ReadHistory.objects.create(user=self.user_a, tutorial=tutorial)

    def test_admin_can_view_user_profile_page(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("accounts:user-detail", args=[self.user_a.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_a.email)
        self.assertContains(response, "Viewed tutorial")

    def test_editor_can_view_only_own_department_user_profile(self):
        self.client.force_login(self.editor_a)

        allowed = self.client.get(reverse("accounts:user-detail", args=[self.user_a.id]))
        denied = self.client.get(reverse("accounts:user-detail", args=[self.user_b.id]))

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 403)

    def test_simple_user_cannot_view_user_profile_page(self):
        self.client.force_login(self.user_a)
        response = self.client.get(reverse("accounts:user-detail", args=[self.user_b.id]))

        self.assertEqual(response.status_code, 403)
