import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.core.files.storage import default_storage
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.permissions import can_manage_tutorial, ensure_department_assignment
from knowledgebase.forms import (
    MAX_TUTORIAL_IMAGES,
    MAX_TUTORIAL_VIDEO_URLS,
    TutorialForm,
    TutorialImageFormSet,
    TutorialVideoFormSet,
)
from knowledgebase.models import ReadHistory, Tutorial, TutorialImage

logger = logging.getLogger(__name__)
TUTORIALS_PER_PAGE = 15


def _safe_delete_storage_file(file_name: str, storage=None) -> None:
    if not file_name:
        return
    storage_backend = storage or default_storage
    try:
        storage_backend.delete(file_name)
    except OSError:
        logger.warning("Could not delete media file '%s'", file_name, exc_info=True)


def _has_active_video_urls(video_formset) -> bool:
    for item in video_formset.cleaned_data:
        if not item or item.get("DELETE"):
            continue
        if (item.get("video_url") or "").strip():
            return True
    return False


def _can_view_tutorial(user: User, tutorial: Tutorial) -> bool:
    if user.role == User.Role.ADMIN:
        return True
    if user.role == User.Role.EDITOR:
        return user.department_id == tutorial.department_id
    if user.role == User.Role.USER:
        return user.department_id == tutorial.department_id and tutorial.is_published
    return False


@login_required
def tutorial_list(request):
    tutorials = Tutorial.objects.select_related("department", "created_by").defer(
        "content",
        "description",
        "video_file",
        "video_caption",
        "video_url",
    )
    if request.user.role == User.Role.ADMIN:
        pass
    elif request.user.role == User.Role.EDITOR:
        ensure_department_assignment(request.user)
        tutorials = tutorials.filter(department=request.user.department)
    else:
        ensure_department_assignment(request.user)
        tutorials = tutorials.filter(department=request.user.department, is_published=True)

    q = request.GET.get("q", "").strip()
    if q:
        tutorials = tutorials.filter(
            Q(title__icontains=q) | Q(description__icontains=q) | Q(content__icontains=q)
        )
    tutorials = tutorials.order_by("-updated_at")
    page_obj = Paginator(tutorials, TUTORIALS_PER_PAGE).get_page(request.GET.get("page"))

    return render(
        request,
        "knowledgebase/tutorial_list.html",
        {
            "tutorials": page_obj,
            "page_obj": page_obj,
            "query": q,
        },
    )


@login_required
def tutorial_detail(request, pk: int):
    if request.user.role in {User.Role.EDITOR, User.Role.USER}:
        ensure_department_assignment(request.user)

    tutorial = get_object_or_404(
        Tutorial.objects.select_related("department", "created_by").prefetch_related("images", "video_links"),
        pk=pk,
    )
    if not _can_view_tutorial(request.user, tutorial):
        raise PermissionDenied

    is_read = False
    if request.user.role == User.Role.USER:
        is_read = ReadHistory.objects.filter(user=request.user, tutorial=tutorial).exists()

    return render(
        request,
        "knowledgebase/tutorial_detail.html",
        {"tutorial": tutorial, "is_read": is_read},
    )


@login_required
@require_POST
def tutorial_toggle_read(request, pk: int):
    tutorial = get_object_or_404(Tutorial, pk=pk)
    if request.user.role != User.Role.USER:
        raise PermissionDenied
    ensure_department_assignment(request.user)
    if not _can_view_tutorial(request.user, tutorial):
        raise PermissionDenied

    read_item = ReadHistory.objects.filter(user=request.user, tutorial=tutorial).first()
    if read_item:
        read_item.delete()
        messages.info(request, _("Marked as unread."))
    else:
        ReadHistory.objects.create(user=request.user, tutorial=tutorial)
        messages.success(request, _("Marked as read."))
    return redirect("knowledgebase:tutorial-detail", pk=pk)


@login_required
def tutorial_create(request):
    if request.user.role not in {User.Role.ADMIN, User.Role.EDITOR}:
        raise PermissionDenied
    if request.user.role == User.Role.EDITOR:
        ensure_department_assignment(request.user)

    form = TutorialForm(request.POST or None, request.FILES or None, current_user=request.user)
    formset = TutorialImageFormSet(
        request.POST or None,
        request.FILES or None,
        prefix="images",
    )
    video_formset = TutorialVideoFormSet(
        request.POST or None,
        prefix="video_urls",
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid() and video_formset.is_valid():
        has_uploaded_video = bool(form.cleaned_data.get("video_file"))
        has_video_urls = _has_active_video_urls(video_formset)
        if has_uploaded_video and has_video_urls:
            form.add_error(None, _("Use either uploaded video or video URLs, not both."))
            return render(
                request,
                "knowledgebase/tutorial_form.html",
                {
                    "form": form,
                    "formset": formset,
                    "video_formset": video_formset,
                    "is_create": True,
                    "max_images": MAX_TUTORIAL_IMAGES,
                    "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
                },
            )

        tutorial = form.save(commit=False)
        tutorial.created_by = request.user
        if request.user.role == User.Role.EDITOR:
            tutorial.department = request.user.department
        tutorial.video_url = ""
        tutorial.save()
        formset.instance = tutorial
        formset.save()
        video_formset.instance = tutorial
        video_formset.save()
        messages.success(request, _("Tutorial created successfully."))
        return redirect("knowledgebase:tutorial-list")

    return render(
        request,
        "knowledgebase/tutorial_form.html",
        {
            "form": form,
            "formset": formset,
            "video_formset": video_formset,
            "is_create": True,
            "max_images": MAX_TUTORIAL_IMAGES,
            "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
        },
    )


@login_required
def tutorial_update(request, pk: int):
    tutorial = get_object_or_404(Tutorial, pk=pk)
    if request.user.role == User.Role.EDITOR:
        ensure_department_assignment(request.user)
    if not can_manage_tutorial(request.user, tutorial.department_id):
        raise PermissionDenied
    original_video_name = tutorial.video_file.name if tutorial.video_file else ""
    original_video_storage = tutorial.video_file.storage if tutorial.video_file else None

    form = TutorialForm(
        request.POST or None,
        request.FILES or None,
        instance=tutorial,
        current_user=request.user,
    )
    formset = TutorialImageFormSet(
        request.POST or None,
        request.FILES or None,
        instance=tutorial,
        prefix="images",
    )
    video_formset = TutorialVideoFormSet(
        request.POST or None,
        instance=tutorial,
        prefix="video_urls",
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid() and video_formset.is_valid():
        has_uploaded_video = bool(form.cleaned_data.get("video_file")) or (
            bool(tutorial.video_file) and not form.cleaned_data.get("remove_video")
        )
        has_video_urls = _has_active_video_urls(video_formset)
        if has_uploaded_video and has_video_urls:
            form.add_error(None, _("Use either uploaded video or video URLs, not both."))
            return render(
                request,
                "knowledgebase/tutorial_form.html",
                {
                    "form": form,
                    "formset": formset,
                    "video_formset": video_formset,
                    "is_create": False,
                    "tutorial": tutorial,
                    "max_images": MAX_TUTORIAL_IMAGES,
                    "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
                },
            )

        tutorial = form.save(commit=False)
        if request.user.role == User.Role.EDITOR:
            tutorial.department = request.user.department
        tutorial.video_url = ""
        remove_video_requested = bool(form.cleaned_data.get("remove_video"))
        if remove_video_requested:
            tutorial.video_file = None
            tutorial.video_caption = ""
        tutorial.save()
        formset.save()
        video_formset.save()

        new_video_name = tutorial.video_file.name if tutorial.video_file else ""
        should_delete_old_video = bool(original_video_name) and (
            remove_video_requested or (new_video_name and new_video_name != original_video_name)
        )
        if should_delete_old_video:
            _safe_delete_storage_file(original_video_name, original_video_storage)

        messages.success(request, _("Tutorial updated successfully."))
        return redirect("knowledgebase:tutorial-list")

    return render(
        request,
        "knowledgebase/tutorial_form.html",
        {
            "form": form,
            "formset": formset,
            "video_formset": video_formset,
            "is_create": False,
            "tutorial": tutorial,
            "max_images": MAX_TUTORIAL_IMAGES,
            "max_video_urls": MAX_TUTORIAL_VIDEO_URLS,
        },
    )


@login_required
def tutorial_delete(request, pk: int):
    tutorial = get_object_or_404(Tutorial, pk=pk)
    if request.user.role == User.Role.EDITOR:
        ensure_department_assignment(request.user)
    if not can_manage_tutorial(request.user, tutorial.department_id):
        raise PermissionDenied
    if request.method == "POST":
        image_file_names = list(tutorial.images.values_list("image", flat=True))
        image_storage = TutorialImage._meta.get_field("image").storage
        tutorial.delete()
        for image_file_name in image_file_names:
            _safe_delete_storage_file(image_file_name, image_storage)
        messages.success(request, _("Tutorial deleted successfully."))
        return redirect("knowledgebase:tutorial-list")
    return render(
        request,
        "knowledgebase/tutorial_confirm_delete.html",
        {"tutorial": tutorial},
    )

# Create your views here.
