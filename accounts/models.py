from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", _("Admin")
        EDITOR = "EDITOR", _("Editor")
        USER = "USER", _("User")

    email = models.EmailField(_("email address"), unique=True)
    phone_number = models.CharField(_("phone number"), max_length=25, blank=True)
    full_name = models.CharField(_("full name"), max_length=180, blank=True)
    role = models.CharField(
        _("role"),
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name=_("department"),
    )
    profile_photo = models.ImageField(
        _("profile photo"),
        upload_to="profiles/",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")

    def clean(self):
        super().clean()
        if self.role in {self.Role.EDITOR, self.Role.USER} and not self.department:
            raise ValidationError({"department": _("Department is required for Editor and User roles.")})

    @property
    def display_name(self):
        return self.full_name or self.username

    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    def is_editor_role(self) -> bool:
        return self.role == self.Role.EDITOR

    def is_user_role(self) -> bool:
        return self.role == self.Role.USER

# Create your models here.
