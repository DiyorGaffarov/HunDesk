from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from departments.models import Department


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
