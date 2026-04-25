from django.db import models
from django.utils.translation import gettext_lazy as _


class Department(models.Model):
    name = models.CharField(_("name"), max_length=120, unique=True)
    description = models.TextField(_("description"), blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        ordering = ("name",)
        verbose_name = _("department")
        verbose_name_plural = _("departments")

    def __str__(self) -> str:
        return self.name

# Create your models here.
