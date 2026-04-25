from django.db import models
from django.utils.translation import gettext_lazy as _


class Tutorial(models.Model):
    title = models.CharField(_("title"), max_length=220)
    description = models.TextField(_("description"), blank=True)
    content = models.TextField(_("content"))
    department = models.ForeignKey(
        "departments.Department",
        on_delete=models.CASCADE,
        related_name="tutorials",
        verbose_name=_("department"),
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tutorials",
        verbose_name=_("created by"),
    )
    video_file = models.FileField(_("video file"), upload_to="tutorials/videos/", null=True, blank=True)
    video_caption = models.CharField(_("video caption"), max_length=255, blank=True)
    video_url = models.URLField(_("video URL"), blank=True)
    is_published = models.BooleanField(_("is published"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = _("tutorial")
        verbose_name_plural = _("tutorials")

    def __str__(self) -> str:
        return self.title


class TutorialImage(models.Model):
    tutorial = models.ForeignKey(
        Tutorial,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=_("tutorial"),
    )
    image = models.ImageField(_("image"), upload_to="tutorials/images/")
    caption = models.CharField(_("caption"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("tutorial image")
        verbose_name_plural = _("tutorial images")

    def __str__(self) -> str:
        return self.caption or self.tutorial.title


class TutorialVideo(models.Model):
    tutorial = models.ForeignKey(
        Tutorial,
        on_delete=models.CASCADE,
        related_name="video_links",
        verbose_name=_("tutorial"),
    )
    video_url = models.URLField(_("video URL"))
    caption = models.CharField(_("caption"), max_length=255, blank=True)

    class Meta:
        verbose_name = _("tutorial video")
        verbose_name_plural = _("tutorial videos")

    def __str__(self) -> str:
        return self.caption or self.video_url


class ReadHistory(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="read_history",
        verbose_name=_("user"),
    )
    tutorial = models.ForeignKey(
        Tutorial,
        on_delete=models.CASCADE,
        related_name="read_history",
        verbose_name=_("tutorial"),
    )
    read_at = models.DateTimeField(_("read at"), auto_now_add=True)

    class Meta:
        ordering = ("-read_at",)
        verbose_name = _("read history")
        verbose_name_plural = _("read history")
        constraints = [
            models.UniqueConstraint(
                fields=("user", "tutorial"),
                name="unique_readhistory_user_tutorial",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.tutorial.title}"
